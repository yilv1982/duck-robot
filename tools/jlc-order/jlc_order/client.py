"""开放平台 HTTP 客户端：JOP 签名、JSON POST、multipart 上传、错误翻译。

协议要点（open.jlc.com 开发指南「基本规则」）：
- 一律 HTTPS POST；普通请求 JSON（Content-Type: application/json），UTF-8。
- 文件上传用 multipart/form-data，但**签名仍用 meta 对应的 JSON 报文**。
- 200 不代表业务成功，须看业务 code；400 鉴权参数错、401 验签不通过、
  403 请求不合法（常见为 IP 白名单未放行）、500 平台内部错误。
- 应答头 J-Trace-ID 是请求唯一标识，报障时提供它。
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .auth import build_authorization
from .config import Config

# 业务成功码集合：以控制台接口文档为准，联调阶段对齐（常见为 0 或 200）。
DEFAULT_SUCCESS_CODES = frozenset({0, 200, "0", "200"})

Transport = Callable[..., tuple[int, dict[str, str], bytes]]
# Transport(request: HttpRequest) -> (status, headers, body)


@dataclass
class HttpRequest:
    method: str
    url: str
    headers: dict[str, str]
    body: bytes | None


@dataclass
class ApiResponse:
    path: str
    status: int
    body_text: str
    json: dict | None
    trace_id: str | None
    success: bool
    headers: dict[str, str] | None = None

    def data(self) -> dict:
        if not self.success:
            raise ApiError.from_response(self)
        payload = (self.json or {}).get("data")
        return payload if isinstance(payload, dict) else {}

    def data_list(self) -> list:
        if not self.success:
            raise ApiError.from_response(self)
        payload = (self.json or {}).get("data")
        return payload if isinstance(payload, list) else []


@dataclass
class ApiError(Exception):
    status: int
    code: object = None
    message: str = ""
    trace_id: str | None = None
    path: str = ""

    def __str__(self) -> str:  # pragma: no cover - 纯格式化
        parts = [f"HTTP {self.status}"]
        if self.code is not None:
            parts.append(f"业务码 {self.code}")
        if self.message:
            parts.append(self.message)
        if self.path:
            parts.append(f"接口 {self.path}")
        if self.trace_id:
            parts.append(f"J-Trace-ID {self.trace_id}")
        text = "，".join(parts)
        return f"{text}。{self.hint}" if self.hint else text

    @property
    def hint(self) -> str:
        if self.status == 400:
            return "鉴权参数错误：检查 appid/access_key 是否填错。"
        if self.status == 401:
            return "验签不通过：检查 secret_key、本机系统时间是否准确（时间戳按秒级校验）。"
        if self.status == 403:
            return "请求不合法：最常见是 IP 白名单未放行本机出口 IP（控制台→应用管理→IP白名单）。"
        if self.status == 500:
            return "开放平台内部错误：可携带 J-Trace-ID 联系官方客服 18665386054。"
        return ""

    @classmethod
    def from_response(cls, resp: ApiResponse) -> ApiError:
        code = (resp.json or {}).get("code")
        message = (resp.json or {}).get("message") or (resp.json or {}).get("msg") or ""
        return cls(resp.status, code, message, resp.trace_id, resp.path)


@dataclass
class CallRecord:
    """写入台账的一次调用摘要（不含任何密钥）。"""

    time: str
    path: str
    status: int
    code: object
    message: str
    trace_id: str | None
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])


class JlcClient:
    def __init__(
        self,
        config: Config,
        *,
        transport: Transport | None = None,
        dry_run: bool = False,
        sleep: Callable[[float], None] = time.sleep,
        now: Callable[[], str] | None = None,
        on_call: Callable[[CallRecord], None] | None = None,
    ) -> None:
        self.config = config
        self.credentials = config.credentials
        self.dry_run = dry_run
        self._transport = transport or urllib_transport
        self._sleep = sleep
        self._now = now or (lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
        self._on_call = on_call

    # ---- 对外能力 -------------------------------------------------------

    def post_json(self, path: str, payload: dict, *, retries: int = 2) -> ApiResponse:
        """POST JSON 请求。签名与发送共用同一份序列化字节，保证一致。"""
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        return self._send(path, body, retries)

    def upload_file(
        self,
        path: str,
        meta: dict,
        file_path: Path,
        *,
        file_field: str = "file",
        meta_field: str = "meta",
        retries: int = 1,
    ) -> ApiResponse:
        """文件上传：multipart 传输，签名用 meta JSON（官方规则）。"""
        meta_text = json.dumps(meta, ensure_ascii=False, separators=(",", ":"))
        boundary = f"----jlcorder{uuid.uuid4().hex}"
        file_bytes = Path(file_path).read_bytes()
        file_name = Path(file_path).name
        parts: list[bytes] = []
        for name, value in ((meta_field, meta_text),):
            parts.append(
                f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"'
                f"\r\n\r\n{value}\r\n".encode()
            )
        parts.append(
            (
                f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; '
                f'filename="{file_name}"\r\n'
                f"Content-Type: application/zip\r\n\r\n"
            ).encode()
            + file_bytes
            + b"\r\n"
        )
        parts.append(f"--{boundary}--\r\n".encode())
        body_bytes = b"".join(parts)
        # 签名用 meta 文本（不是 multipart 原始字节）
        return self._send(
            path,
            meta_text,
            retries,
            raw_body=body_bytes,
            content_type=f"multipart/form-data; boundary={boundary}",
        )

    # ---- 内部 ------------------------------------------------------------

    def _send(
        self,
        path: str,
        signing_body: str,
        retries: int,
        *,
        raw_body: bytes | None = None,
        content_type: str = "application/json",
    ) -> ApiResponse:
        body_bytes = raw_body if raw_body is not None else signing_body.encode("utf-8")
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            authorization = build_authorization(
                self.credentials, "POST", path, signing_body
            )
            request = HttpRequest(
                method="POST",
                url=f"{self.config.endpoint}{path}",
                headers={
                    "Authorization": authorization,
                    "Content-Type": content_type,
                },
                body=body_bytes,
            )
            if self.dry_run:
                self._print_dry_run(request, signing_body)
                return ApiResponse(path, 0, "(dry-run 未发送)", None, None, True)
            try:
                status, headers, body = self._transport(request)
                response = self._to_response(path, status, headers, body)
                if status >= 500 and attempt < retries:
                    last_error = ApiError.from_response(response)
                    self._backoff(attempt)
                    continue
                return response
            except (urllib.error.URLError, OSError) as exc:
                last_error = exc
                if attempt < retries:
                    self._backoff(attempt)
                    continue
                raise ConnectionError(
                    f"无法连接 {self.config.endpoint}（{path}）：{exc}"
                ) from exc
        raise last_error or RuntimeError("unreachable")  # pragma: no cover

    def _backoff(self, attempt: int) -> None:
        self._sleep(0.5 * (attempt + 1))

    def _to_response(
        self, path: str, status: int, headers: dict[str, str], body: bytes
    ) -> ApiResponse:
        body_text = body.decode("utf-8", errors="replace")
        try:
            payload = json.loads(body_text) if body_text else None
        except json.JSONDecodeError:
            payload = None
        trace_id = headers.get("J-Trace-ID") or headers.get("j-trace-id")
        success = status == 200 and (
            not isinstance(payload, dict)
            or "code" not in payload
            or payload.get("code") in DEFAULT_SUCCESS_CODES
        )
        response = ApiResponse(path, status, body_text, payload, trace_id, success, headers)
        if self._on_call:
            code = payload.get("code") if isinstance(payload, dict) else None
            message = (
                payload.get("message") or payload.get("msg") or ""
                if isinstance(payload, dict)
                else ""
            )
            self._on_call(
                CallRecord(
                    time=self._now(),
                    path=path,
                    status=status,
                    code=code,
                    message=str(message)[:200],
                    trace_id=trace_id,
                )
            )
        return response

    def _print_dry_run(self, request: HttpRequest, signing_body: str) -> None:
        print("== DRY-RUN：以下请求未发送 ==")
        print(f"{request.method} {request.url}")
        auth = request.headers["Authorization"]
        # 干跑输出也可能进日志，密钥同样脱敏
        safe_auth = auth.replace(self.credentials.access_key, "***").replace(
            self.credentials.secret_key, "***"
        )
        print(f"Authorization: {safe_auth}")
        print(f"Content-Type: {request.headers['Content-Type']}")
        print(f"签名报文: {signing_body}")
        if request.body and len(request.body) > 4096:
            print(f"(传输体 {len(request.body)} 字节，文件上传内容略)")
        print("== DRY-RUN 结束 ==")


def urllib_transport(request: HttpRequest) -> tuple[int, dict[str, str], bytes]:
    req = urllib.request.Request(
        request.url, data=request.body, headers=request.headers, method=request.method
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, dict(resp.headers.items()), resp.read()
    except urllib.error.HTTPError as exc:  # 4xx/5xx 也要拿到应答体
        return exc.code, dict(exc.headers.items()), exc.read()

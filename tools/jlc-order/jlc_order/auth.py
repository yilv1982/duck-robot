"""JOP 请求签名（嘉立创开放平台官方协议）。

协议出处（open.jlc.com 开发指南「请求签名」）：
- 签名串共 5 行，每行以 ``\\n`` 结束（包括最后一行）：
  ``HTTP方法\\n URL(去域名,含query)\\n unix秒时间戳\\n 32位随机串\\n 请求报文\\n``
- GET 请求报文为空串；POST 用真实发送的 JSON 原文；文件上传用 meta JSON。
- 签名 = Base64(HmacSHA256(SecretKey, 签名串))。
- Authorization 头：``JOP appid="..",accesskey="..",nonce="..",timestamp="..",signature=".."``

本模块的期望输出已用官方文档示例数据做过逐字节验证（见 tests/test_auth.py）。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import string
import time
from dataclasses import dataclass

NONCE_LENGTH = 32
_NONCE_ALPHABET = string.ascii_letters + string.digits
_AUTH_SCHEME = "JOP"


@dataclass(frozen=True)
class Credentials:
    """一组开放平台应用密钥（创建应用后从控制台获得）。"""

    app_id: str
    access_key: str
    secret_key: str


def generate_nonce() -> str:
    """生成 32 位请求随机串（仅大小写字母与数字）。"""
    return "".join(secrets.choice(_NONCE_ALPHABET) for _ in range(NONCE_LENGTH))


def build_string_to_sign(
    method: str, url_path: str, timestamp: int, nonce: str, body: str
) -> str:
    """按官方 5 行规则构造待签名串。

    ``url_path`` 是去除域名后的绝对路径；有查询参数时须带上 ``?`` 及查询串。
    """
    return f"{method}\n{url_path}\n{timestamp}\n{nonce}\n{body}\n"


def sign(secret_key: str, message: str) -> str:
    """HmacSHA256(secret_key, message) 的 Base64 结果。"""
    digest = hmac.new(
        secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
    ).digest()
    return base64.b64encode(digest).decode("ascii")


def build_authorization(
    credentials: Credentials,
    method: str,
    url_path: str,
    body: str,
    *,
    timestamp: int | None = None,
    nonce: str | None = None,
) -> str:
    """构造完整的 Authorization 头。

    ``timestamp``/``nonce`` 仅供测试注入；默认取当前时间与新随机串。
    """
    ts = int(time.time()) if timestamp is None else int(timestamp)
    nc = nonce if nonce is not None else generate_nonce()
    string_to_sign = build_string_to_sign(method, url_path, ts, nc, body)
    signature = sign(credentials.secret_key, string_to_sign)
    return (
        f'{_AUTH_SCHEME} appid="{credentials.app_id}",'
        f'accesskey="{credentials.access_key}",'
        f'nonce="{nc}",'
        f'timestamp="{ts}",'
        f'signature="{signature}"'
    )

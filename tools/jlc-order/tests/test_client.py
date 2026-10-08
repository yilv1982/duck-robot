"""client 模块测试：全部走注入的假传输层，不发真实网络请求。"""

import base64
import hashlib
import hmac
import json

import pytest

from jlc_order.auth import Credentials
from jlc_order.client import ApiError, CallRecord, JlcClient
from jlc_order.config import Config


def make_client(transport, **kwargs) -> JlcClient:
    config = Config(
        credentials=Credentials(
            app_id="app-1", access_key="ak-1", secret_key="sk-1"
        ),
        endpoint="https://open-api.example",
        timeout=1.0,
    )
    return JlcClient(config, transport=transport, **kwargs)


def ok_body(data=None):
    return json.dumps({"code": 0, "message": "ok", "data": data or {}}).encode()


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, request):
        self.requests.append(request)
        result = self.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def test_post_json_headers_and_body():
    transport = FakeTransport([(200, {"J-Trace-ID": "t-1"}, ok_body({"price": 5}))])
    client = make_client(transport)
    resp = client.post_json("/pcb/v1/quote", {"board": 2})
    assert resp.success and resp.data() == {"price": 5}
    request = transport.requests[0]
    assert request.method == "POST"
    assert request.url == "https://open-api.example/pcb/v1/quote"
    assert request.headers["Content-Type"] == "application/json"
    assert request.headers["Authorization"].startswith('JOP appid="app-1"')
    # 发送体与签名体必须一致且为紧凑 JSON
    assert json.loads(request.body) == {"board": 2}


def test_authorization_signature_covers_sent_body():
    transport = FakeTransport([(200, {}, ok_body())])
    client = make_client(transport)
    client.post_json("/order/v1/createOrder", {"a": 1, "中文": "值"})
    request = transport.requests[0]
    auth = request.headers["Authorization"]
    nonce = auth.split('nonce="')[1].split('"')[0]
    timestamp = auth.split('timestamp="')[1].split('"')[0]
    signature = auth.split('signature="')[1].split('"')[0]
    body = request.body.decode("utf-8")
    string_to_sign = f"POST\n/order/v1/createOrder\n{timestamp}\n{nonce}\n{body}\n"
    expected = base64.b64encode(
        hmac.new(b"sk-1", string_to_sign.encode("utf-8"), hashlib.sha256).digest()
    ).decode()
    assert signature == expected


def test_business_error_code_raises_with_message():
    transport = FakeTransport(
        [(200, {"J-Trace-ID": "t-2"}, '{"code": 1001, "message": "预付款余额不足"}'.encode())]
    )
    client = make_client(transport)
    resp = client.post_json("/order/v1/createOrder", {})
    assert not resp.success
    with pytest.raises(ApiError) as excinfo:
        resp.data()
    assert excinfo.value.code == 1001
    assert "预付款余额不足" in str(excinfo.value)


@pytest.mark.parametrize(
    ("status", "keyword"),
    [(400, "鉴权参数"), (401, "验签"), (403, "IP 白名单"), (500, "内部错误")],
)
def test_http_status_hints(status, keyword):
    transport = FakeTransport([(status, {"J-Trace-ID": "t-3"}, b"{}")])
    client = make_client(transport)
    resp = client.post_json("/x", {}, retries=0)  # 500 会触发重试，单测禁用重试
    assert not resp.success
    with pytest.raises(ApiError) as excinfo:
        resp.data()
    assert keyword in excinfo.value.hint


def test_retry_on_500_then_success():
    transport = FakeTransport(
        [
            (500, {}, b"boom"),
            (200, {}, ok_body({"ok": True})),
        ]
    )
    sleeps = []
    client = make_client(transport, sleep=sleeps.append)
    resp = client.post_json("/pcb/v1/quote", {}, retries=2)
    assert resp.success
    assert len(transport.requests) == 2
    assert sleeps  # 有退避等待


def test_connection_error_after_retries():
    import urllib.error

    transport = FakeTransport([urllib.error.URLError("refused")] * 3)
    client = make_client(transport, sleep=lambda _s: None)
    with pytest.raises(ConnectionError):
        client.post_json("/x", {}, retries=2)


def test_no_retry_by_default_on_business_failure():
    transport = FakeTransport([(200, {}, b'{"code": 1001, "message": "x"}')])
    client = make_client(transport)
    resp = client.post_json("/order/v1/createOrder", {}, retries=0)
    assert not resp.success
    assert len(transport.requests) == 1  # 业务失败绝不重试（防重复下单）


def test_upload_file_multipart_and_meta_signing(tmp_path):
    gerber = tmp_path / "board.zip"
    gerber.write_bytes(b"PK-fake-gerber")
    transport = FakeTransport([(200, {}, ok_body({"fileId": "f-1"}))])
    client = make_client(transport)
    resp = client.upload_file("/file/v1/upload", {"orderNo": "A1"}, gerber)
    assert resp.data() == {"fileId": "f-1"}
    request = transport.requests[0]
    assert request.headers["Content-Type"].startswith("multipart/form-data; boundary=")
    body = request.body.decode("utf-8", errors="replace")
    assert 'name="meta"' in body
    assert '{"orderNo":"A1"}' in body
    assert "PK-fake-gerber" in body
    # 签名针对 meta JSON 而非 multipart 原始体
    auth = request.headers["Authorization"]
    nonce = auth.split('nonce="')[1].split('"')[0]
    timestamp = auth.split('timestamp="')[1].split('"')[0]
    signature = auth.split('signature="')[1].split('"')[0]
    string_to_sign = f'POST\n/file/v1/upload\n{timestamp}\n{nonce}\n{{"orderNo":"A1"}}\n'
    expected = base64.b64encode(
        hmac.new(b"sk-1", string_to_sign.encode("utf-8"), hashlib.sha256).digest()
    ).decode()
    assert signature == expected


def test_dry_run_never_touches_transport():
    transport = FakeTransport([])
    client = make_client(transport, dry_run=True)
    resp = client.post_json("/order/v1/createOrder", {"q": 5})
    assert resp.success
    assert transport.requests == []  # 关键安全属性：dry-run 零网络调用
    assert resp.body_text == "(dry-run 未发送)"


def test_ledger_hook_gets_record(tmp_path):
    records = []
    transport = FakeTransport([(200, {"J-Trace-ID": "trace-9"}, ok_body())])
    client = make_client(transport, on_call=records.append)
    client.post_json("/pcb/v1/quote", {})
    (record,) = records
    assert isinstance(record, CallRecord)
    assert record.path == "/pcb/v1/quote"
    assert record.status == 200
    assert record.trace_id == "trace-9"
    # 台账不能含任何密钥
    dumped = json.dumps(record.__dict__, default=str)
    assert "sk-1" not in dumped and "ak-1" not in dumped

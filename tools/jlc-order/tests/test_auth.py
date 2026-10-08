"""auth 模块 golden 测试：期望值逐字取自官方文档「请求签名」示例。

来源 https://open.jlc.com/develop-guide?doc=signature （2026-10-08 取证）。
若官方文档更新导致此处失败，需人工重新核对协议，而不是改断言迁就实现。
"""

from jlc_order.auth import (
    Credentials,
    build_authorization,
    build_string_to_sign,
    generate_nonce,
    sign,
)

# 官方示例密钥与参数（文档原文，非真实可用密钥）
DOC_CREDENTIALS = Credentials(
    app_id="293992070061998081",
    access_key="b6713a535d56412f805afadd7e818455",
    secret_key="z0BWlikshimuyiwBsH1i2qwnzMb3j3kA",
)
DOC_TIMESTAMP = 1625208260
DOC_NONCE = "IZHEJYNIHYZIE8S0LLC0VWTPJVRRTO50"
DOC_BODY = '{"goodsId":100,"quantity":52,"createdTime":"2024-03-21 10:03:20"}'
DOC_SIGNATURE = "sygwKhKBkLwHVv0c7D+a/A7JTEJjGH/kLugFKh16918="


def test_string_to_sign_five_lines():
    sts = build_string_to_sign(
        "POST", "/order/v1/createOrder", DOC_TIMESTAMP, DOC_NONCE, DOC_BODY
    )
    assert sts == (
        "POST\n"
        "/order/v1/createOrder\n"
        "1625208260\n"
        "IZHEJYNIHYZIE8S0LLC0VWTPJVRRTO50\n"
        '{"goodsId":100,"quantity":52,"createdTime":"2024-03-21 10:03:20"}\n'
    )
    assert sts.endswith("\n")


def test_official_signature_vector():
    sts = build_string_to_sign(
        "POST", "/order/v1/createOrder", DOC_TIMESTAMP, DOC_NONCE, DOC_BODY
    )
    assert sign(DOC_CREDENTIALS.secret_key, sts) == DOC_SIGNATURE


def test_official_authorization_header():
    header = build_authorization(
        DOC_CREDENTIALS,
        "POST",
        "/order/v1/createOrder",
        DOC_BODY,
        timestamp=DOC_TIMESTAMP,
        nonce=DOC_NONCE,
    )
    assert header == (
        'JOP appid="293992070061998081",'
        'accesskey="b6713a535d56412f805afadd7e818455",'
        'nonce="IZHEJYNIHYZIE8S0LLC0VWTPJVRRTO50",'
        'timestamp="1625208260",'
        'signature="sygwKhKBkLwHVv0c7D+a/A7JTEJjGH/kLugFKh16918="'
    )


def test_get_request_empty_body_signing():
    """GET 请求报文主体为空：签名串第 5 行只有一个换行。"""
    sts = build_string_to_sign("GET", "/order/v1/query", 1000, DOC_NONCE, "")
    assert sts == f"GET\n/order/v1/query\n1000\n{DOC_NONCE}\n\n"
    sign(DOC_CREDENTIALS.secret_key, sts)  # 可计算即可


def test_nonce_shape():
    nonce = generate_nonce()
    assert len(nonce) == 32
    assert nonce.isalnum()
    assert generate_nonce() != nonce

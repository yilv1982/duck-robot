"""order_info 模块测试：[order] 配置解析与创建订单报文装配。"""

import pytest

from jlc_order.order_info import OrderInfo, OrderInfoError

FULL = {
    "pcb_file_url": "https://pan.example.com/s/abc?pwd=wpgy",
    "file_name": "banana_pcb.zip",
    "link_man": "张三",
    "link_phone": "13800001111",
    "consignee": "张三",
    "receive_phone": "13800001111",
    "province": "广东省",
    "city": "深圳市",
    "area": "南山区",
    "address": "科技园 1 号",
    "invoice_title": "张三",
}


def test_load_full_and_payload_shape():
    info = OrderInfo.load(FULL)
    assert info.validate() == []
    payload = info.to_payload()
    assert payload["pcbFileUrl"] == FULL["pcb_file_url"]
    assert payload["fileName"] == "banana_pcb.zip"
    assert payload["advancePayment"] is False  # 默认不自动扣款
    assert payload["useCouponFlag"] is True
    assert payload["orderLinkMan"] == {"man": "张三", "phone": "13800001111"}
    assert payload["orderReceive"]["consignee"] == "张三"
    assert payload["orderReceive"]["area"] == "南山区"
    assert "orderRemark" not in payload  # 空备注不发送


def test_load_missing_section_gives_guidance():
    with pytest.raises(OrderInfoError, match="\\[order\\]"):
        OrderInfo.load(None)


def test_load_reports_missing_required_fields():
    data = {**FULL, "address": "", "city": None}
    info = OrderInfo.load(data)
    problems = " ".join(info.validate())
    assert "address" in problems and "city" in problems


def test_validate_flags_bad_url_and_express():
    info = OrderInfo.load({**FULL, "pcb_file_url": "ftp://x/y.zip", "express_type": "SF_FAST"})
    problems = " ".join(info.validate())
    assert "pcb_file_url" in problems and "express_type" in problems


def test_remark_included_when_set():
    info = OrderInfo.load({**FULL, "order_remark": "审核有疑问请电话联系"})
    assert info.to_payload()["orderRemark"] == "审核有疑问请电话联系"

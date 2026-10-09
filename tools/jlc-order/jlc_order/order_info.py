"""下单信息：收货人/发票/快递/资料文件 URL。

出于隐私考虑，这些个人信息**不放参数模板**（模板要进 git），
而是放在 gitignore 的 jlc-order.toml 的 ``[order]`` 段（本机私有）。

字段对齐《创建订单接口》PDF（tools/jlc-order/api-docs/）：
- pcbFileUrl/fileName：开放平台无上传接口，资料须先托管到可公网访问的 URL
  （官方示例甚至用百度网盘链接）；
- advancePayment=false：只建单不自动扣款，去 jlc.com 手动支付（安全默认）；
- expressType 枚举见 ALLOWED_EXPRESS；发票枚举见 ALLOWED_INVOICE。
"""

from __future__ import annotations

from dataclasses import dataclass, fields

ALLOWED_EXPRESS = {
    # JYM（加运美）在文档枚举里但 API 下单实测报「提交订单错误」，勿用；
    # SF_DSBZ_JF（顺丰电商标快寄付）为实测可用默认
    "DEBANG": "德邦货运",
    "EMS": "EMS经济快递",
    "sf_special_offers": "顺丰经济快递",
    "SF": "顺丰标准快递(寄付)",
    "sf_send_payment": "顺丰标准快递(到付)",
    "SF_DSBZ_JF": "顺丰电商标快(寄付)",
    "SR": "速尔快递",
    "YS": "优速快递",
    "ZT": "自提",
    "DEBANG_ZT": "德邦货运寄付(自提)",
    "DEBANG_SH": "德邦货运寄付(送货)",
    "DEBANG_KD": "德邦快递",
    "KYBZJF": "跨越标准速运(寄付)",
    "JDTH": "京东特惠快递",
    "JDTK": "京东航空快递",
}
ALLOWED_INVOICE = {"增值税发票", "已预开增值税专用发票", "个人电子发票普票"}

REQUIRED_FIELDS = (
    "pcb_file_url",
    "file_name",
    "invoice_title",
    "link_man",
    "link_phone",
    "consignee",
    "receive_phone",
    "province",
    "city",
    "area",
    "address",
)


class OrderInfoError(Exception):
    """下单信息缺失或非法。"""


@dataclass
class OrderInfo:
    pcb_file_url: str = ""  # gerber zip 的公网可访问 URL
    file_name: str = ""  # 如 banana_pcb.zip
    invoice: str = "个人电子发票普票"
    invoice_title: str = ""  # 发票抬头（个人=姓名）
    invoice_type: str = "personal"  # personal / company
    express_type: str = "SF_DSBZ_JF"  # 快递代码，见 ALLOWED_EXPRESS（JYM 文档有但 API 实测被拒）
    link_man: str = ""  # 下单联系人
    link_phone: str = ""
    consignee: str = ""  # 收货人
    receive_phone: str = ""
    province: str = ""
    city: str = ""
    area: str = ""
    address: str = ""  # 详细地址（不含省市区）
    advance_payment: bool = False  # false=只建单，去 jlc.com 手动付款
    use_coupon: bool = True
    order_remark: str = ""
    receipt_delivery: str = "电子收据/送货单"

    @classmethod
    def load(cls, data: dict | None) -> OrderInfo:
        """从配置 toml 的 [order] 表构造；缺失时给出可操作的提示。"""
        if not data:
            raise OrderInfoError(
                "缺少下单信息：请在 jlc-order.toml 增加 [order] 段"
                "（pcb_file_url/file_name/invoice_title/link_man/link_phone/"
                "consignee/receive_phone/province/city/area/address），"
                "字段说明见 config.example.toml 与 api-docs/创建订单接口.txt"
            )
        return cls.from_toml_table(data)

    @classmethod
    def from_toml_table(cls, table: dict) -> OrderInfo:
        known = {f.name for f in fields(cls)}
        unknown = [k for k in table if k not in known]
        if unknown:
            raise OrderInfoError(f"[order] 含未知字段: {', '.join(unknown)}")
        try:
            return cls(**table)
        except TypeError as exc:
            raise OrderInfoError(f"[order] 字段类型错误: {exc}") from exc

    def validate(self) -> list[str]:
        problems: list[str] = []
        for name in REQUIRED_FIELDS:
            if not getattr(self, name):
                problems.append(f"[order].{name} 未填写")
        if self.invoice not in ALLOWED_INVOICE:
            problems.append(f"发票类型 {self.invoice} 不在 {sorted(ALLOWED_INVOICE)}")
        if self.express_type not in ALLOWED_EXPRESS:
            problems.append(
                f"express_type {self.express_type} 不是有效快递代码（见 ALLOWED_EXPRESS）"
            )
        if self.invoice_type not in ("personal", "company"):
            problems.append("invoice_type 只能是 personal/company")
        if self.pcb_file_url and not self.pcb_file_url.startswith(("http://", "https://")):
            problems.append("pcb_file_url 必须是 http(s) URL")
        return problems

    def to_payload(self) -> dict:
        """顶层下单字段（与 orderTechnical 平级），映射出自官方文档。"""
        payload = {
            "pcbFileUrl": self.pcb_file_url,
            "fileName": self.file_name,
            "invoice": self.invoice,
            "invoiceTitle": self.invoice_title,
            "invoiceType": self.invoice_type,
            "receiptDelivery": self.receipt_delivery,
            "expressType": self.express_type,
            "orderLinkMan": {"man": self.link_man, "phone": self.link_phone},
            "orderReceive": {
                "consignee": self.consignee,
                "phone": self.receive_phone,
                "province": self.province,
                "city": self.city,
                "area": self.area,
                "address": self.address,
            },
            "advancePayment": self.advance_payment,
            "useCouponFlag": self.use_coupon,
        }
        if self.order_remark:
            payload["orderRemark"] = self.order_remark
        return payload

    def describe(self) -> str:
        express = ALLOWED_EXPRESS.get(self.express_type, self.express_type)
        pay = "自动扣款" if self.advance_payment else "建单后手动支付"
        return (
            f"{express}，收货：{self.consignee} {self.receive_phone} "
            f"{self.province}{self.city}{self.area}{self.address}，"
            f"发票：{self.invoice}（{self.invoice_title}），{pay}；"
            f"资料：{self.file_name} <- {self.pcb_file_url}"
        )

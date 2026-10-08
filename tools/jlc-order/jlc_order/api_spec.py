"""业务接口注册表：路径、重试安全性、对齐状态集中管理。

路径对齐状态说明：
- ``confirmed``  出自官方公开文档原文（请求签名页示例出现该路径）。
- ``pending``    按官方路径风格推断的占位，需登录控制台 api-docs 逐字段对齐；
                 对齐后把 status 改为 confirmed 并更新 doc_url。

控制台接口文档入口（需登录）：https://open.jlc.com/control-board → 接口文档。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApiEndpoint:
    name: str
    path: str
    description: str
    status: str  # confirmed | pending
    retry_safe: bool  # 失败重试是否安全（下单类一律 False，防重复下单）


PCB_QUOTE = ApiEndpoint(
    name="pcb_quote",
    path="/pcb/v1/quote",
    description="PCB 在线计价",
    status="pending",
    retry_safe=True,
)
PCB_CREATE_ORDER = ApiEndpoint(
    name="pcb_create_order",
    path="/order/v1/createOrder",  # 官方签名文档示例路径（orderType=PCB）
    description="创建 PCB 订单",
    status="confirmed",
    retry_safe=False,
)
PCB_REORDER = ApiEndpoint(
    name="pcb_reorder",
    path="/order/v1/repeatOrder",
    description="创建 PCB 返单（按历史订单重下）",
    status="pending",
    retry_safe=False,
)
ORDER_GET = ApiEndpoint(
    name="order_get",
    path="/order/v1/getOrderInfo",
    description="查询订单信息",
    status="pending",
    retry_safe=True,
)
ORDER_PROGRESS = ApiEndpoint(
    name="order_progress",
    path="/order/v1/getOrderProgress",
    description="查询订单生产进度",
    status="pending",
    retry_safe=True,
)
FILE_UPLOAD = ApiEndpoint(
    name="file_upload",
    path="/file/v1/upload",
    description="上传 Gerber/资料文件（multipart，签名用 meta JSON）",
    status="pending",
    retry_safe=False,  # 上传成功与否未知时重试可能产生多份文件，默认不自动重试
)

ALL_ENDPOINTS: tuple[ApiEndpoint, ...] = (
    PCB_QUOTE,
    PCB_CREATE_ORDER,
    PCB_REORDER,
    ORDER_GET,
    ORDER_PROGRESS,
    FILE_UPLOAD,
)

BY_NAME = {ep.name: ep for ep in ALL_ENDPOINTS}


def pending_endpoints() -> list[ApiEndpoint]:
    """尚未与控制台文档对齐的接口（doctor 输出提醒用）。"""
    return [ep for ep in ALL_ENDPOINTS if ep.status == "pending"]

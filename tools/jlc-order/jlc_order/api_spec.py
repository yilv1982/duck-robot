"""业务接口注册表：路径、重试安全性、对齐状态集中管理。

路径对齐状态说明：
- ``confirmed``  出自官方 PCB 业务 SDK（控制台→SDK下载→jlc-openapi-sdk-pcb-java）
                 jar 内各 Request 类常量提取，2026-10-09 与线上网关逐一探活验证。
- ``pending``    仍未对齐的占位，需登录控制台 api-docs 逐字段对齐；
                 对齐后把 status 改为 confirmed 并更新说明。

已确认但未注册的其余 PCB 接口（备用）：
- /pcb/order/getList（订单列表）  /pcb/order/getOrderPageList（订单分页）
- /pcb/order/getExpressSchedule（快递轨迹）  /pcb/order/getOrderPriceDetails（价格明细）
- /pcb/order/getOrderDownloadFile（下载生产文件）  /pcb/order/getListBySerialCode（按序列号查单）

3D 打印（3DP 业务 SDK，jlc-openapi-sdk-3dp-java）：
- /3dp-open/order/uploadModelFile（上传模型）  /3dp-open/order/submitOrder（下单）
- /3dp-open/order/getCraft（工艺清单）  /3dp-open/order/uploadNutFile  /3dp-open/ask/replyOPAsk

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
    path="/pcb/onlinePrice/get",
    description="PCB 在线计价",
    status="confirmed",
    retry_safe=True,
)
PCB_CREATE_ORDER = ApiEndpoint(
    name="pcb_create_order",
    path="/pcb/order/create",
    description="创建 PCB 订单（文件以 pcbFileUrl+fileName 传入，非先上传）",
    status="confirmed",
    retry_safe=False,
)
PCB_REORDER = ApiEndpoint(
    name="pcb_reorder",
    path="/pcb/order/backOrder/create",
    description="创建 PCB 返单（按历史订单 customerOrderId 重下）",
    status="confirmed",
    retry_safe=False,
)
ORDER_GET = ApiEndpoint(
    name="order_get",
    path="/pcb/order/get",
    description="查询订单信息（customerOrderId+orderType）",
    status="confirmed",
    retry_safe=True,
)
ORDER_PROGRESS = ApiEndpoint(
    name="order_progress",
    path="/pcb/order/progress/get",
    description="查询订单生产进度（customerOrderId+orderType）",
    status="confirmed",
    retry_safe=True,
)
ORDER_LIST = ApiEndpoint(
    name="order_list",
    path="/pcb/order/getList",
    description="查询订单列表",
    status="confirmed",
    retry_safe=True,
)
FILE_UPLOAD = ApiEndpoint(
    name="file_upload",
    path="/file/v1/upload",
    description="上传资料文件（PCB SDK 无此接口：下单直接传 pcbFileUrl；此路径为占位）",
    status="pending",
    retry_safe=False,  # 上传成功与否未知时重试可能产生多份文件，默认不自动重试
)

ALL_ENDPOINTS: tuple[ApiEndpoint, ...] = (
    PCB_QUOTE,
    PCB_CREATE_ORDER,
    PCB_REORDER,
    ORDER_GET,
    ORDER_PROGRESS,
    ORDER_LIST,
    FILE_UPLOAD,
)

BY_NAME = {ep.name: ep for ep in ALL_ENDPOINTS}


def pending_endpoints() -> list[ApiEndpoint]:
    """尚未与控制台文档对齐的接口（doctor 输出提醒用）。"""
    return [ep for ep in ALL_ENDPOINTS if ep.status == "pending"]

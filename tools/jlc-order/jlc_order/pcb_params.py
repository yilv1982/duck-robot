"""PCB 下单/计价参数：TOML 模板 → 校验 → API 报文。

字段映射对齐《在线计价接口》《创建订单接口》PDF（tools/jlc-order/api-docs/，
2026-10-09 自开放平台控制台下载）：
- 工艺参数在 ``orderTechnical`` 嵌套对象内；
- 板长/宽传 ``stencilLength``/``stencilWidth``，单位 **cm**（模板内部仍用 mm）；
- 板层数是 ``stencilLayer``、数量是 ``stencilCounts``、板厚是 ``stencilPly``(mm)；
- 模板字段名保持人类可读，只改 ``to_payload`` 的映射，模板文件不动。
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path

import tomllib

# 枚举值全部出自官方接口文档，勿凭直觉增删
ALLOWED_COLORS = {"绿色", "红色", "黄色", "蓝色", "白色", "黑色", "紫色"}
ALLOWED_FINISH = {"有铅喷锡", "无铅喷锡", "沉金"}
ALLOWED_TEST = {"不测试", "抽测", "全部测试", "测试一半", "随机抽测"}
ALLOWED_VIA = {"过孔盖油", "过孔开窗", "过孔塞油", "过孔塞树脂", "过孔塞铜浆"}
ALLOWED_CHAR_COLOR = {"白色", "黑色"}
ALLOWED_THICKNESS = (0.4, 0.6, 0.8, 1.0, 1.2, 1.6, 1.8, 2.0, 2.5, 3.0)
ALLOWED_COPPER = (1.0, 2.0)  # 外层铜厚仅 1/2 盎司（0.5 仅内层 insideCuprumThickness）
ALLOWED_PLATE_TYPE = {
    1: "FR-4", 2: "铝基板", 4: "热电分离铜基板", 5: "罗杰斯高频板", 6: "铁氟龙高频板", 7: "FPC软板",
}


class ParamsError(Exception):
    """参数模板缺失或非法。"""


@dataclass
class PcbParams:
    # 板子基本参数（尺寸单位 mm）
    length: float
    width: float
    layers: int = 2
    quantity: int = 5
    thickness: float = 1.6  # 板厚 mm
    color: str = "绿色"  # 阻焊颜色
    surface_finish: str = "无铅喷锡"  # 焊盘喷镀
    copper_thickness: float = 1.0  # 盎司（外层）
    test: str = "全部测试"
    plate_type: int = 1  # 板材类型（1=FR-4）
    via_cover: str = "过孔盖油"  # 阻焊覆盖（下单接口必填）
    char_font_color: str = "白色"  # 丝印字符颜色（下单接口必填：白色/黑色）
    acheive_time_type: str = "normal_one"  # 发货时间：normal_one 正常3-4天（1/2层样板默认）
    # 下单所需业务信息（收货地址/发票等走 [extra] 或后续扩展）
    remark: str = ""
    extra: dict = field(default_factory=dict)  # 官方新增字段的逃生口（并入顶层）

    @classmethod
    def load(cls, path: Path) -> PcbParams:
        if not path.is_file():
            raise ParamsError(f"参数模板不存在: {path}")
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        if "board" not in data:
            raise ParamsError(f"模板缺少 [board] 段: {path}")
        raw = dict(data["board"])
        known = {f.name for f in fields(cls)}
        extra = data.get("extra", {})
        unknown = [k for k in raw if k not in known]
        if unknown:
            raise ParamsError(f"模板含未知字段 [board].{', '.join(unknown)}")
        missing = [
            name for name in ("length", "width") if name not in raw
        ]
        if missing:
            raise ParamsError(f"模板缺少必填字段: {', '.join(missing)}")
        try:
            return cls(**raw, extra=extra)
        except TypeError as exc:
            raise ParamsError(f"模板字段类型错误: {exc}") from exc

    def validate(self) -> list[str]:
        problems: list[str] = []
        if not (5 <= self.length <= 500):
            problems.append(f"板长 {self.length}mm 超出常见范围 5~500")
        if not (5 <= self.width <= 500):
            problems.append(f"板宽 {self.width}mm 超出常见范围 5~500")
        if self.layers not in (1, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32):
            problems.append(f"层数 {self.layers} 不是文档允许的偶数档位")
        if not (1 <= self.quantity <= 10000):
            problems.append(f"数量 {self.quantity} 超范围 1~10000")
        if self.thickness not in ALLOWED_THICKNESS:
            problems.append(f"板厚 {self.thickness}mm 不在 {list(ALLOWED_THICKNESS)}")
        if self.color not in ALLOWED_COLORS:
            problems.append(f"阻焊颜色 {self.color} 不在 {sorted(ALLOWED_COLORS)}")
        if self.surface_finish not in ALLOWED_FINISH:
            problems.append(f"焊盘喷镀 {self.surface_finish} 不在 {sorted(ALLOWED_FINISH)}")
        if self.copper_thickness not in ALLOWED_COPPER:
            problems.append(f"外层铜厚 {self.copper_thickness}oz 不是 1/2")
        if self.test not in ALLOWED_TEST:
            problems.append(f"测试方式 {self.test} 不在 {sorted(ALLOWED_TEST)}")
        if self.via_cover not in ALLOWED_VIA:
            problems.append(f"过孔覆盖 {self.via_cover} 不在 {sorted(ALLOWED_VIA)}")
        if self.char_font_color not in ALLOWED_CHAR_COLOR:
            problems.append(f"字符颜色 {self.char_font_color} 不在 {sorted(ALLOWED_CHAR_COLOR)}")
        if self.plate_type not in ALLOWED_PLATE_TYPE:
            problems.append(f"板材类型 {self.plate_type} 不在 {sorted(ALLOWED_PLATE_TYPE)}")
        return problems

    def to_payload(self) -> dict:
        """转计价/下单请求报文（orderTechnical 嵌套结构，映射出自官方文档）。"""
        technical = {
            "plateType": self.plate_type,
            "stencilLayer": self.layers,
            "stencilLength": round(self.length / 10, 2),  # mm → cm，最多 2 位小数
            "stencilWidth": round(self.width / 10, 2),
            "stencilCounts": self.quantity,
            "stencilPly": self.thickness,
            "cuprumThickness": self.copper_thickness,
            "testProduct": self.test,
            "adornColor": self.color,
            "adornPut": self.surface_finish,
            "adornBestrow": self.via_cover,
            "charFontColor": self.char_font_color,
            "acheiveTimeType": self.acheive_time_type,
        }
        payload: dict = {"orderTechnical": technical}
        if self.remark:
            payload["orderRemark"] = self.remark  # 仅创建订单接口消费，计价接口忽略
        payload.update(self.extra)
        return payload

    def describe(self) -> str:
        plate = ALLOWED_PLATE_TYPE.get(self.plate_type, self.plate_type)
        return (
            f"{self.length:g}×{self.width:g}mm {self.layers}层 板厚{self.thickness:g}mm "
            f"数量{self.quantity}pcs {plate} {self.color} {self.surface_finish} "
            f"铜厚{self.copper_thickness:g}oz {self.test}"
        )

"""PCB 下单/计价参数：TOML 模板 → 校验 → API 报文。

字段名现阶段与嘉立创下单页术语一致；待控制台 api-docs 对齐后，
如官方报文字段不同，只改 ``to_payload`` 的映射，模板文件不动。
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path

import tomllib

ALLOWED_COLORS = {"绿色", "红色", "黄色", "蓝色", "白色", "黑色", "紫色", "哑黑"}
ALLOWED_FINISH = {"无铅喷锡", "有铅喷锡", "沉金", "OSP", "沉锡", "沉银"}
ALLOWED_TEST = {"免费飞针测试", "百分之百测试"}


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
    surface_finish: str = "无铅喷锡"  # 表面处理
    copper_thickness: float = 1.0  # 盎司
    test: str = "免费飞针测试"
    # 下单所需业务信息（对齐后按需扩充，如收货地址 ID）
    remark: str = ""
    extra: dict = field(default_factory=dict)  # 官方新增字段的逃生口

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
        if self.layers not in (1, 2, 4, 6, 8):
            problems.append(f"层数 {self.layers} 不是 1/2/4/6/8")
        if not (1 <= self.quantity <= 10000):
            problems.append(f"数量 {self.quantity} 超范围 1~10000")
        if self.thickness not in (0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.6, 2.0, 2.4, 3.2):
            problems.append(f"板厚 {self.thickness}mm 不是常用规格")
        if self.color not in ALLOWED_COLORS:
            problems.append(f"阻焊颜色 {self.color} 不在 {sorted(ALLOWED_COLORS)}")
        if self.surface_finish not in ALLOWED_FINISH:
            problems.append(f"表面处理 {self.surface_finish} 不在 {sorted(ALLOWED_FINISH)}")
        if self.copper_thickness not in (0.5, 1.0, 2.0):
            problems.append(f"铜厚 {self.copper_thickness}oz 不是 0.5/1/2")
        if self.test not in ALLOWED_TEST:
            problems.append(f"测试方式 {self.test} 不在 {sorted(ALLOWED_TEST)}")
        return problems

    def to_payload(self) -> dict:
        """转 API 请求报文（字段映射对齐点）。"""
        payload = {
            "orderType": "PCB",
            "length": f"{self.length:g}",
            "width": f"{self.width:g}",
            "layers": self.layers,
            "quantity": self.quantity,
            "thickness": f"{self.thickness:g}",
            "color": self.color,
            "surfaceFinish": self.surface_finish,
            "copperThickness": f"{self.copper_thickness:g}",
            "testType": self.test,
        }
        if self.remark:
            payload["remark"] = self.remark
        payload.update(self.extra)
        return payload

    def describe(self) -> str:
        return (
            f"{self.length:g}×{self.width:g}mm {self.layers}层 板厚{self.thickness:g}mm "
            f"数量{self.quantity}pcs {self.color} {self.surface_finish} "
            f"铜厚{self.copper_thickness:g}oz {self.test}"
        )

"""Gerber 制造包校验与打包（面向嘉立创 PCB 打样上传）。"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path

# KiCad 输出后缀 → 作用（嘉立创识别 KiCad 命名）
COPPER_PATTERNS = (".gtl", ".gbl", ".g2", ".g3", ".g4", ".g5", ".g6", ".g7", ".g8")
OUTLINE_PATTERNS = (".gm1", ".gko", ".gml", "edge_cuts")
DRILL_PATTERNS = (".drl", ".txt", "-drl")


@dataclass
class GerberReport:
    ok: bool
    layer_count: int
    problems: list[str]
    files: list[str]

    def summary(self) -> str:
        head = f"Gerber 校验{'通过' if self.ok else '未通过'}：{len(self.files)} 个文件，"
        head += f"{self.layer_count} 层铜"
        if self.problems:
            head += "\n问题:\n" + "\n".join(f"  - {p}" for p in self.problems)
        return head


def validate_zip(zip_path: Path) -> GerberReport:
    """校验 gerber zip 的层完整性。规则保守：只拦明确缺失，不猜工艺。"""
    problems: list[str] = []
    if not zip_path.is_file():
        return GerberReport(False, 0, [f"文件不存在: {zip_path}"], [])
    if zip_path.suffix.lower() != ".zip":
        problems.append(f"不是 zip 文件: {zip_path.name}（嘉立创上传要求 zip）")
    try:
        with zipfile.ZipFile(zip_path) as zf:
            names = [n for n in zf.namelist() if not n.endswith("/")]
            bad = zf.testzip()
            if bad is not None:
                problems.append(f"zip 内损坏条目: {bad}")
    except zipfile.BadZipFile as exc:
        return GerberReport(False, 0, [f"zip 无法读取: {exc}"], [])

    lowered = [n.lower() for n in names]
    if not names:
        problems.append("zip 为空")

    copper = [n for n in lowered if n.endswith(COPPER_PATTERNS)]
    inner = [n for n in copper if n.endswith((".g2", ".g3", ".g4", ".g5", ".g6", ".g7", ".g8"))]
    layer_count = 2 + len(inner)
    if not any(n.endswith(".gtl") for n in copper):
        problems.append("缺顶层铜 (.gtl / F_Cu)")
    if not any(n.endswith(".gbl") for n in copper):
        problems.append("缺底层铜 (.gbl / B_Cu)")

    if not any(p in n for n in lowered for p in OUTLINE_PATTERNS):
        problems.append("缺板框层 (.gm1/.gko/Edge_Cuts)")

    drills = [n for n in lowered if n.endswith(".drl") or "drill" in n]
    if not any(n.endswith(".drl") for n in lowered) and not any(
        "-drl" in n for n in drills
    ):
        problems.append("缺钻孔文件 (.drl)")

    return GerberReport(not problems, layer_count, problems, names)


def pack_directory(source: Path, output: Path) -> Path:
    """把散放的 gerber 文件目录打成 zip（扁平结构，不嵌目录）。"""
    if not source.is_dir():
        raise FileNotFoundError(f"目录不存在: {source}")
    files = sorted(p for p in source.iterdir() if p.is_file())
    if not files:
        raise ValueError(f"目录里没有文件: {source}")
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(f, f.name)
    return output


def default_output_zip(project_dir: Path, stem: str | None = None) -> Path:
    """默认制造包路径：工程目录 production/<工程名>.zip。"""
    return project_dir / "production" / f"{stem or project_dir.name}.zip"

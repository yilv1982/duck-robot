"""gerber 模块测试。"""

import zipfile

from jlc_order.gerber import pack_directory, validate_zip


def make_gerber_zip(path, names):
    with zipfile.ZipFile(path, "w") as zf:
        for name in names:
            zf.writestr(name, "G04 demo*")


def test_validate_ok_kicad_layout(tmp_path):
    zip_path = tmp_path / "board.zip"
    make_gerber_zip(
        zip_path,
        [
            "board-F_Cu.gtl",
            "board-B_Cu.gbl",
            "board-F_Mask.gts",
            "board-Edge_Cuts.gm1",
            "board-PTH.drl",
        ],
    )
    report = validate_zip(zip_path)
    assert report.ok, report.problems
    assert report.layer_count == 2


def test_validate_detects_missing_outline_and_drill(tmp_path):
    zip_path = tmp_path / "bad.zip"
    make_gerber_zip(zip_path, ["board-F_Cu.gtl", "board-B_Cu.gbl"])
    report = validate_zip(zip_path)
    assert not report.ok
    assert any("板框" in p for p in report.problems)
    assert any("钻孔" in p for p in report.problems)


def test_validate_counts_inner_layers(tmp_path):
    zip_path = tmp_path / "four.zip"
    make_gerber_zip(
        zip_path,
        ["b.gtl", "b.gbl", "b.g2", "b.g3", "b.gm1", "b.drl"],
    )
    report = validate_zip(zip_path)
    assert report.ok
    assert report.layer_count == 4


def test_validate_missing_file(tmp_path):
    report = validate_zip(tmp_path / "nope.zip")
    assert not report.ok
    assert report.problems == ["文件不存在: {}".format(tmp_path / "nope.zip")]


def test_pack_directory_flat(tmp_path):
    src = tmp_path / "gerbers"
    src.mkdir()
    (src / "a.gtl").write_text("x")
    (src / "sub").mkdir()
    out = tmp_path / "packed.zip"
    pack_directory(src, out)
    with zipfile.ZipFile(out) as zf:
        assert zf.namelist() == ["a.gtl"]

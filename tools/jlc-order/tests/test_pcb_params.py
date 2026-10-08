"""pcb_params 模块测试。"""

import pytest

from jlc_order.pcb_params import ParamsError, PcbParams


def write_toml(tmp_path, text):
    path = tmp_path / "p.toml"
    path.write_text(text, encoding="utf-8")
    return path


VALID = """
[board]
length = 39.2
width = 6.8
"""


def test_load_minimal_and_defaults(tmp_path):
    params = PcbParams.load(write_toml(tmp_path, VALID))
    assert (params.length, params.width) == (39.2, 6.8)
    assert params.layers == 2 and params.quantity == 5
    assert params.validate() == []


def test_load_rejects_unknown_field(tmp_path):
    path = write_toml(tmp_path, VALID + "colour = \"red\"\n")
    with pytest.raises(ParamsError, match="未知字段"):
        PcbParams.load(path)


def test_load_rejects_missing_size(tmp_path):
    path = write_toml(tmp_path, '[board]\nquantity = 5\n')
    with pytest.raises(ParamsError, match="必填"):
        PcbParams.load(path)


def test_validate_flags_bad_values(tmp_path):
    params = PcbParams(length=4, width=6.8, layers=3, thickness=1.1, color="粉色",
                       surface_finish="镀金", copper_thickness=3, test="免测")
    problems = " ".join(params.validate())
    for keyword in ("板长", "层数", "板厚", "阻焊颜色", "表面处理", "铜厚", "测试方式"):
        assert keyword in problems


def test_payload_shape_and_extra(tmp_path):
    params = PcbParams(length=39.2, width=6.8, remark="测试板", extra={"addressId": "A1"})
    payload = params.to_payload()
    assert payload["orderType"] == "PCB"
    assert payload["length"] == "39.2"
    assert payload["width"] == "6.8"
    assert payload["remark"] == "测试板"
    assert payload["addressId"] == "A1"

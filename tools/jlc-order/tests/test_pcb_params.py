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
    for keyword in ("板长", "层数", "板厚", "阻焊颜色", "焊盘喷镀", "铜厚", "测试方式"):
        assert keyword in problems


def test_payload_shape_and_extra(tmp_path):
    params = PcbParams(length=39.2, width=6.8, remark="测试板", extra={"invoice": "增值税发票"})
    payload = params.to_payload()
    tech = payload["orderTechnical"]
    assert tech["plateType"] == 1
    assert tech["stencilLayer"] == 2
    assert tech["stencilLength"] == 3.92  # mm → cm
    assert tech["stencilWidth"] == 0.68
    assert tech["stencilCounts"] == 5
    assert tech["stencilPly"] == 1.6
    assert tech["testProduct"] == "全部测试"
    assert payload["orderRemark"] == "测试板"
    assert payload["invoice"] == "增值税发票"

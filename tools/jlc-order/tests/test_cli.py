"""cli 模块测试：重点验证 dry-run 安全属性与命令装配。"""

import json

import pytest

from jlc_order import cli
from jlc_order.client import JlcClient


@pytest.fixture
def config_env(monkeypatch, tmp_path):
    monkeypatch.setenv("JLC_APP_ID", "app-1")
    monkeypatch.setenv("JLC_ACCESS_KEY", "ak-1")
    monkeypatch.setenv("JLC_SECRET_KEY", "sk-1")
    monkeypatch.setenv("JLC_LEDGER_PATH", str(tmp_path / "ledger.jsonl"))
    return tmp_path


PARAMS_TOML = """
[board]
length = 39.2
width = 6.8
"""


def test_order_dry_run_never_sends(monkeypatch, config_env, tmp_path, capsys):
    # 把模块默认传输函数换成会爆炸的桩：任何真实网络调用都会让测试失败
    import jlc_order.client as client_mod

    def boom(request):
        raise AssertionError("dry-run 不允许发网络请求")

    monkeypatch.setattr(client_mod, "urllib_transport", boom)
    params = tmp_path / "p.toml"
    params.write_text(PARAMS_TOML, encoding="utf-8")
    code = cli.main(
        ["pcb", "order", "-p", str(params), "--file-id", "f-1", "--dry-run"]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "DRY-RUN" in out and "不会发送" in out
    # 台账不应记录 dry-run
    assert not (config_env / "ledger.jsonl").exists()


def test_order_confirm_gate_blocks_without_yes(monkeypatch, config_env, tmp_path, capsys):
    calls = []

    def fake_post(self, path, payload, **kw):
        calls.append(path)
        from jlc_order.client import ApiResponse

        return ApiResponse(path, 200, "{}", {}, None, True)

    monkeypatch.setattr(JlcClient, "post_json", fake_post)
    params = tmp_path / "p.toml"
    params.write_text(PARAMS_TOML, encoding="utf-8")
    code = cli.main(["pcb", "order", "-p", str(params), "--file-id", "f-1"])
    assert code == 1  # 非交互环境没有 --yes → 拒绝
    assert calls == []
    assert "已取消" in capsys.readouterr().out


def test_quote_prints_params(monkeypatch, config_env, tmp_path, capsys):
    def fake_post(self, path, payload, **kw):
        from jlc_order.client import ApiResponse

        return ApiResponse(
            path, 200, json.dumps({"code": 0, "data": {"totalPrice": "5.00"}}),
            {"code": 0, "data": {"totalPrice": "5.00"}}, None, True,
        )

    monkeypatch.setattr(JlcClient, "post_json", fake_post)
    params = tmp_path / "p.toml"
    params.write_text(PARAMS_TOML, encoding="utf-8")
    code = cli.main(["pcb", "quote", "-p", str(params)])
    out = capsys.readouterr().out
    assert code == 0
    assert "计价参数" in out and "5.00" in out
    # 台账写入行为由 test_client.py::test_ledger_hook_gets_record 覆盖（此处桩替换了 post_json）


def test_missing_config_returns_error(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("JLC_APP_ID", raising=False)
    monkeypatch.delenv("JLC_ACCESS_KEY", raising=False)
    monkeypatch.delenv("JLC_SECRET_KEY", raising=False)
    code = cli.main(["--config", str(tmp_path / "none.toml"), "doctor"])
    assert code == 2
    assert "缺少配置项" in capsys.readouterr().err


def test_version(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--version"])
    assert excinfo.value.code == 0

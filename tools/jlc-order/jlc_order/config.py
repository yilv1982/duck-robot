"""配置加载：jlc-order.toml（默认）或环境变量，密钥永不打印。"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

import tomllib

from .auth import Credentials

DEFAULT_ENDPOINT = "https://open-api.jlc.com"
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_CONFIG_NAME = "jlc-order.toml"

CONFIG_ENV_PREFIX = "JLC_"


class ConfigError(Exception):
    """配置缺失或非法。"""


@dataclass(frozen=True)
class Config:
    credentials: Credentials
    endpoint: str = DEFAULT_ENDPOINT
    timeout: float = DEFAULT_TIMEOUT_SECONDS
    ledger_path: Path | None = None  # None = 工具目录下 orders.jsonl
    order: dict | None = None  # [order] 段原文，由 order_info.OrderInfo 解析校验


def load_config(path: Path | None = None) -> Config:
    """按 优先级（高→低）加载：显式路径 > 环境变量 > 工具目录 jlc-order.toml。

    密钥字段允许 toml 与环境变量互补（例如密钥放环境变量、其余放 toml）。
    """
    data = _read_toml(path)
    app_id = _pick(data, "app_id", "APP_ID")
    access_key = _pick(data, "access_key", "ACCESS_KEY")
    secret_key = _pick(data, "secret_key", "SECRET_KEY")

    missing = [
        name
        for name, value in (
            ("app_id", app_id),
            ("access_key", access_key),
            ("secret_key", secret_key),
        )
        if not value
    ]
    if missing:
        raise ConfigError(
            f"缺少配置项: {', '.join(missing)}。"
            f"请在 {DEFAULT_CONFIG_NAME}（参考 config.example.toml）或环境变量 "
            f"JLC_APP_ID / JLC_ACCESS_KEY / JLC_SECRET_KEY 中提供。"
        )

    endpoint = _pick(data, "endpoint", "ENDPOINT") or DEFAULT_ENDPOINT
    timeout = float(_pick(data, "timeout_seconds", "TIMEOUT_SECONDS") or DEFAULT_TIMEOUT_SECONDS)
    ledger = _pick(data, "ledger_path", "LEDGER_PATH")

    return Config(
        credentials=Credentials(
            app_id=str(app_id), access_key=str(access_key), secret_key=str(secret_key)
        ),
        endpoint=str(endpoint).rstrip("/"),
        timeout=timeout,
        ledger_path=Path(ledger).expanduser() if ledger else None,
        order=data.get("order") if isinstance(data.get("order"), dict) else None,
    )


def default_config_path() -> Path:
    """约定真实配置放在工具根目录的 jlc-order.toml（已 gitignore）。"""
    return Path(__file__).resolve().parent.parent / DEFAULT_CONFIG_NAME


def _read_toml(path: Path | None) -> dict:
    candidates = [path] if path else [default_config_path()]
    for candidate in candidates:
        if candidate and candidate.is_file():
            try:
                return tomllib.loads(candidate.read_text(encoding="utf-8"))
            except tomllib.TOMLDecodeError as exc:  # pragma: no cover - 人工排障路径
                raise ConfigError(f"配置文件解析失败 {candidate}: {exc}") from exc
    return {}


def _pick(data: dict, key: str, env_suffix: str) -> str | None:
    env = os.environ.get(CONFIG_ENV_PREFIX + env_suffix)
    if env:
        return env
    value = data.get(key)
    return str(value) if value is not None else None


def redact(text: str, credentials: Credentials) -> str:
    """把密钥从任意文本中抹掉，用于日志与异常输出。"""
    for secret in (credentials.secret_key, credentials.access_key):
        if secret:
            text = text.replace(secret, "***")
    return text


def die(message: str, exit_code: int = 2) -> None:
    print(f"错误: {message}", file=sys.stderr)
    sys.exit(exit_code)

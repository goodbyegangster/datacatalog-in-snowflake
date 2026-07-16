from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path
from typing import Any, cast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _install_fallback_settings() -> None:
    """settings.py が未生成の環境向けに最小の settings module を用意する。"""
    settings = cast("Any", types.ModuleType("settings"))
    settings.CATALOG_LOCATION = {
        "DATABASE_NAME": "hogehoge",
        "SCHEMA_NAME": "CATALOG",
    }
    settings.DISPLAY_SCOPES = [
        {"DATABASE_NAME": "hogehoge", "SCHEMA_NAME": "DATA_AD"},
        {"DATABASE_NAME": "hogehoge", "SCHEMA_NAME": "DATA_SALES"},
    ]
    settings.SELECTABLE_TAG_KEYS = [
        {"DATABASE_NAME": "hogehoge", "SCHEMA_NAME": "TAG", "TAG_NAME": "DATA_CATEGORY"},
        {"DATABASE_NAME": "hogehoge", "SCHEMA_NAME": "TAG", "TAG_NAME": "DATA_DOMAIN"},
        {"DATABASE_NAME": "hogehoge", "SCHEMA_NAME": "TAG", "TAG_NAME": "PII"},
        {"DATABASE_NAME": "hogehoge", "SCHEMA_NAME": "TAG", "TAG_NAME": "SENSITIVITY"},
    ]
    settings.IS_VISIBLE_ONLY_SELF_USER = False
    sys.modules["settings"] = settings


try:
    importlib.import_module("settings")
except ModuleNotFoundError as exc:
    if exc.name != "settings":
        raise
    _install_fallback_settings()

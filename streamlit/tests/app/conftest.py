# ruff: noqa: S101

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

STREAMLIT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_PAGE = STREAMLIT_ROOT / "views" / "assets.py"
USERS_PAGE = STREAMLIT_ROOT / "views" / "users.py"
GRAPH_PAGE = STREAMLIT_ROOT / "views" / "graph.py"


@pytest.fixture
def assets_app(monkeypatch: pytest.MonkeyPatch) -> AppTest:
    """fake mode のデータ資産ページ AppTest を返す。"""
    monkeypatch.setenv("CATALOG_DATA_MODE", "fake")
    return AppTest.from_file(ASSETS_PAGE)


@pytest.fixture
def users_app(monkeypatch: pytest.MonkeyPatch) -> AppTest:
    """fake mode のユーザーページ AppTest を返す。"""
    monkeypatch.setenv("CATALOG_DATA_MODE", "fake")
    return AppTest.from_file(USERS_PAGE)


def assert_no_exception(app: AppTest) -> None:
    """AppTest 実行時に Streamlit exception が出ていないことを検証する。"""
    assert not app.exception


def dataframe_value(app: AppTest, index: int = 0) -> pd.DataFrame:
    """AppTest の dataframe value を DataFrame として取り出す。"""
    value = app.dataframe[index].value
    assert isinstance(value, pd.DataFrame)
    return value


def multiselect_by_label(app: AppTest, label: str) -> Any:
    """label から multiselect widget を探す。"""
    for widget in app.multiselect:
        if widget.label == label:
            return widget
    raise AssertionError(f"multiselect not found: {label}")

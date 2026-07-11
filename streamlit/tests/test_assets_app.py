# ruff: noqa: S101

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from tests.fixtures import catalog_data
from lib import catalog_fake, schema, state

ASSETS_PAGE = Path(__file__).resolve().parents[1] / "views" / "assets.py"
BASE_ASSET = catalog_data.assets().iloc[0].to_dict()


@pytest.fixture
def assets_app(monkeypatch: pytest.MonkeyPatch) -> AppTest:
    monkeypatch.setenv("CATALOG_DATA_MODE", "fake")

    return AppTest.from_file(ASSETS_PAGE)


def assert_no_exception(app: AppTest) -> None:
    assert not app.exception


def dataframe_value(app: AppTest, index: int = 0) -> pd.DataFrame:
    value = app.dataframe[index].value
    assert isinstance(value, pd.DataFrame)
    return value


def multiselect_by_label(app: AppTest, label: str) -> Any:
    for widget in app.multiselect:
        if widget.label == label:
            return widget
    raise AssertionError(f"multiselect not found: {label}")


def many_assets(count: int) -> pd.DataFrame:
    A = schema.Assets
    return pd.DataFrame(
        {
            **BASE_ASSET,
            A.TABLE_ID: table_id,
            A.ASSET_NAME: f"ASSET_{table_id:03d}",
            A.DESCRIPTION: "Paged asset",
        }
        for table_id in range(1, count + 1)
    )


def test_assets_page_initial_state_is_empty_until_search_condition(
    assets_app: AppTest,
) -> None:
    app = assets_app.run()

    assert_no_exception(app)
    assert [title.value for title in app.title] == ["🗂️ データ資産"]
    assert any("検索結果" in md.value and ">-<" in md.value for md in app.markdown)
    assert [info.value for info in app.info] == ["左の検索条件を指定すると、一覧が表示されます。"]
    assert len(app.dataframe) == 0


def test_assets_page_filters_by_freeword(assets_app: AppTest) -> None:
    app = assets_app.run()

    app.text_input[0].set_value("orders").run()

    assert_no_exception(app)
    assert any("検索結果" in md.value and ">1 件<" in md.value for md in app.markdown)
    result = dataframe_value(app)
    assert result["名前"].tolist() == ["ORDERS"]
    assert result["説明"].tolist() == ["Sales order facts"]


def test_assets_page_resets_schema_when_database_changes(assets_app: AppTest) -> None:
    app = assets_app.run()

    multiselect_by_label(app, "データベース").set_value([catalog_data.DB]).run()
    assert multiselect_by_label(app, "スキーマ").options == ["DATA_AD", "DATA_SALES"]

    multiselect_by_label(app, "スキーマ").set_value(["DATA_SALES"]).run()
    assert multiselect_by_label(app, "スキーマ").value == ["DATA_SALES"]

    multiselect_by_label(app, "データベース").set_value([]).run()

    assert_no_exception(app)
    assert multiselect_by_label(app, "データベース").value == []
    assert multiselect_by_label(app, "スキーマ").value == []
    assert multiselect_by_label(app, "スキーマ").options == []


def test_assets_page_clear_button_resets_search_widgets(assets_app: AppTest) -> None:
    app = assets_app.run()

    app.text_input[0].set_value("orders").run()
    app.segmented_control[0].set_value("OR").run()
    app.segmented_control[1].set_value("OR").run()
    app.segmented_control[2].set_value("OR").run()
    assert dataframe_value(app)["名前"].tolist() == ["ORDERS"]

    app.button[0].click().run()

    assert_no_exception(app)
    assert app.text_input[0].key == "search_asset_freeword"
    assert app.text_input[0].value == ""
    assert app.segmented_control[0].value == "AND"
    assert app.segmented_control[1].value == "AND"
    assert app.segmented_control[2].value == "AND"
    assert [info.value for info in app.info] == ["左の検索条件を指定すると、一覧が表示されます。"]
    assert len(app.dataframe) == 0


def test_assets_page_clears_selection_when_search_condition_becomes_empty(
    assets_app: AppTest,
) -> None:
    app = assets_app.run()

    app.text_input[0].set_value("orders").run()
    app.session_state[state.ASSET_SELECTED_TABLE_ID] = 1
    assert app.session_state[state.ASSET_SELECTED_TABLE_ID] == 1

    app.text_input[0].set_value("").run()

    assert_no_exception(app)
    assert state.ASSET_SELECTED_TABLE_ID not in app.session_state
    assert [info.value for info in app.info] == ["左の検索条件を指定すると、一覧が表示されます。"]
    assert len(app.dataframe) == 0


def test_assets_page_clears_selection_when_search_condition_changes(
    assets_app: AppTest,
) -> None:
    app = assets_app.run()

    app.text_input[0].set_value("orders").run()
    app.session_state[state.ASSET_SELECTED_TABLE_ID] = 1
    app.session_state[state.ASSET_PAGE] = 2
    assert app.session_state[state.ASSET_SELECTED_TABLE_ID] == 1

    app.text_input[0].set_value("customer").run()

    assert_no_exception(app)
    assert state.ASSET_SELECTED_TABLE_ID not in app.session_state
    assert state.ASSET_PAGE not in app.session_state
    assert dataframe_value(app)["名前"].tolist() == ["CUSTOMERS"]


def test_assets_page_paginates_large_results_with_pagination_widget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CATALOG_DATA_MODE", "fake")
    monkeypatch.setattr(catalog_fake, "load_assets", lambda: many_assets(105))
    app = AppTest.from_file(ASSETS_PAGE).run()

    multiselect_by_label(app, "データベース").set_value([catalog_data.DB]).run()

    assert_no_exception(app)
    assert any("検索結果" in md.value and ">105 件<" in md.value for md in app.markdown)
    assert len(app.number_input) == 0
    assert app.session_state[state.ASSET_PAGE] == 1
    assert len(dataframe_value(app)) == 100


def test_assets_page_shows_traceback_in_fake_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CATALOG_DATA_MODE", "fake")

    def load_assets() -> pd.DataFrame:
        raise RuntimeError("fake catalog exploded")

    monkeypatch.setattr(catalog_fake, "load_assets", load_assets)
    app = AppTest.from_file(ASSETS_PAGE).run()

    assert [error.value for error in app.error] == [
        "データの取得に失敗しました。接続設定やカタログテーブルの生成状況をご確認ください。"
    ]
    assert len(app.exception) == 1
    assert "fake catalog exploded" in str(app.exception[0].value)


def test_assets_page_hides_traceback_outside_fake_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CATALOG_DATA_MODE", "snowflake")

    def load_assets() -> pd.DataFrame:
        raise RuntimeError("snowflake catalog exploded")

    monkeypatch.setattr("lib.catalog_snowflake.load_assets", load_assets)
    app = AppTest.from_file(ASSETS_PAGE).run()

    assert [error.value for error in app.error] == [
        "データの取得に失敗しました。接続設定やカタログテーブルの生成状況をご確認ください。"
    ]
    assert len(app.exception) == 0

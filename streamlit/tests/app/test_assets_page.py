# ruff: noqa: S101

from __future__ import annotations

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from catalog import schema
from catalog.providers import fake as catalog_fake
from runtime import state
from tests.app.conftest import (
    ASSETS_PAGE,
    assert_no_exception,
    checkbox_by_label,
    dataframe_value,
    multiselect_by_label,
)
from tests.fixtures import catalog_data

BASE_ASSET = catalog_data.assets().iloc[0].to_dict()


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
    assert [info.value for info in app.info] == [
        "サイドバーの検索条件を指定すると、一覧が表示されます。"
    ]
    assert len(app.dataframe) == 0


def test_assets_page_opens_detail_from_navigation_state(assets_app: AppTest) -> None:
    app = assets_app.run()
    app.session_state[state.NAV_TO_TABLE_ID] = 1

    app.run()

    assert_no_exception(app)
    assert [subheader.value for subheader in app.subheader] == ["ORDERS"]
    assert [info.value for info in app.info] == ["検索条件が未指定のため、一覧は非表示です。"]
    assert state.NAV_TO_TABLE_ID not in app.session_state

    app.run()

    assert_no_exception(app)
    assert [subheader.value for subheader in app.subheader] == ["ORDERS"]


def test_assets_page_filters_by_freeword(assets_app: AppTest) -> None:
    app = assets_app.run()

    app.text_input[0].set_value("orders").run()

    assert_no_exception(app)
    result = dataframe_value(app)
    assert result["名前"].tolist() == ["ORDERS"]
    assert result["説明"].tolist() == ["Sales order facts"]


def test_assets_page_disables_freeword_when_all_targets_are_off(
    assets_app: AppTest,
) -> None:
    app = assets_app.run()

    app.text_input[0].set_value("orders").run()
    for label in (
        "オブジェクトの名前",
        "オブジェクトの説明",
        "カラムの名前",
        "カラムの説明",
    ):
        checkbox_by_label(app, label).set_value(False).run()

    assert_no_exception(app)
    assert app.text_input[0].disabled
    assert app.text_input[0].value == ""
    assert [info.value for info in app.info] == [
        "サイドバーの検索条件を指定すると、一覧が表示されます。"
    ]


def test_assets_page_orders_visible_users_by_user_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CATALOG_DATA_MODE", "fake")
    V = schema.AssetVisibility
    visibility = catalog_data.asset_visibility()
    bob_visibility = visibility.iloc[0].copy()
    bob_visibility[V.USER_NAME] = "BOB"
    bob_visibility[V.USER_ROLES] = ["ANALYST"]
    bob_visibility[V.ASSET_ROLES] = ["SALES_READER"]
    visibility = pd.concat([visibility, bob_visibility.to_frame().T], ignore_index=True)
    monkeypatch.setattr(
        catalog_fake,
        "load_asset_visibility",
        lambda: visibility.sort_values(V.USER_NAME, ascending=False).reset_index(drop=True),
    )
    app = AppTest.from_file(ASSETS_PAGE).run()
    app.session_state[state.NAV_TO_TABLE_ID] = 1

    app.run()

    assert_no_exception(app)
    assert dataframe_value(app, index=3)["ユーザー"].tolist() == ["ALICE", "BOB"]


def test_assets_page_shows_empty_message_when_no_asset_matches(
    assets_app: AppTest,
) -> None:
    app = assets_app.run()

    app.text_input[0].set_value("not-found").run()

    assert_no_exception(app)
    assert [info.value for info in app.info] == [
        "該当するデータ資産がありません。検索条件を変更してください。"
    ]
    assert len(app.dataframe) == 0


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
    assert [info.value for info in app.info] == [
        "サイドバーの検索条件を指定すると、一覧が表示されます。"
    ]
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
    assert [info.value for info in app.info] == [
        "サイドバーの検索条件を指定すると、一覧が表示されます。"
    ]
    assert len(app.dataframe) == 0


def test_assets_page_clears_selection_when_search_condition_changes(
    assets_app: AppTest,
) -> None:
    app = assets_app.run()

    app.text_input[0].set_value("orders").run()
    app.session_state[state.ASSET_SELECTED_TABLE_ID] = 1
    assert app.session_state[state.ASSET_SELECTED_TABLE_ID] == 1

    app.text_input[0].set_value("customer").run()

    assert_no_exception(app)
    assert state.ASSET_SELECTED_TABLE_ID not in app.session_state
    assert dataframe_value(app)["名前"].tolist() == ["CUSTOMERS"]


def test_assets_page_shows_large_results_without_pagination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CATALOG_DATA_MODE", "fake")
    monkeypatch.setattr(catalog_fake, "load_assets", lambda: many_assets(105))
    app = AppTest.from_file(ASSETS_PAGE).run()

    multiselect_by_label(app, "データベース").set_value([catalog_data.DB]).run()

    assert_no_exception(app)
    assert len(app.number_input) == 0
    assert len(dataframe_value(app)) == 105


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

    monkeypatch.setattr("catalog.providers.snowflake.load_assets", load_assets)
    app = AppTest.from_file(ASSETS_PAGE).run()

    assert [error.value for error in app.error] == [
        "データの取得に失敗しました。接続設定やカタログテーブルの生成状況をご確認ください。"
    ]
    assert len(app.exception) == 0

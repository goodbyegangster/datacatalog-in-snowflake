# ruff: noqa: S101

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from lib import catalog_fake, schema, state
from tests.fixtures import catalog_data

USERS_PAGE = Path(__file__).resolve().parents[1] / "views" / "users.py"
BASE_USER = catalog_data.users().iloc[0].to_dict()


@pytest.fixture
def users_app(monkeypatch: pytest.MonkeyPatch) -> AppTest:
    monkeypatch.setenv("CATALOG_DATA_MODE", "fake")

    return AppTest.from_file(USERS_PAGE)


def assert_no_exception(app: AppTest) -> None:
    assert not app.exception


def dataframe_value(app: AppTest, index: int = 0) -> pd.DataFrame:
    value = app.dataframe[index].value
    assert isinstance(value, pd.DataFrame)
    return value


def many_users(count: int) -> pd.DataFrame:
    U = schema.Users
    return pd.DataFrame(
        {
            **BASE_USER,
            U.USER_NAME: f"USER_{user_id:03d}",
            U.DISPLAY_NAME: f"User {user_id:03d}",
        }
        for user_id in range(1, count + 1)
    )


def test_users_page_initial_state_shows_all_users(users_app: AppTest) -> None:
    app = users_app.run()

    assert_no_exception(app)
    assert [title.value for title in app.title] == ["👤 ユーザー"]
    assert [(toggle.label, toggle.value) for toggle in app.toggle] == [
        ("ログインユーザーのみ表示", False)
    ]
    result = dataframe_value(app)
    assert result["名前"].tolist() == ["ALICE", "BOB", "SVC_ETL"]
    assert result["表示名"].tolist() == ["Alice Analytics", "Bob Builder", "ETL Service"]


def test_users_page_opens_detail_from_navigation_state(users_app: AppTest) -> None:
    app = users_app.run()
    app.session_state[state.NAV_TO_USER_NAME] = "ALICE"

    app.run()

    assert_no_exception(app)
    assert [subheader.value for subheader in app.subheader] == ["ALICE"]
    assert state.NAV_TO_USER_NAME not in app.session_state

    app.run()

    assert_no_exception(app)
    assert [subheader.value for subheader in app.subheader] == ["ALICE"]


def test_users_page_filters_by_freeword(users_app: AppTest) -> None:
    app = users_app.run()

    app.text_input[0].set_value("service").run()

    assert_no_exception(app)
    result = dataframe_value(app)
    assert result["名前"].tolist() == ["SVC_ETL"]
    assert result["表示名"].tolist() == ["ETL Service"]


def test_users_page_orders_visible_assets_by_hierarchy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CATALOG_DATA_MODE", "fake")
    V = schema.AssetVisibility
    visibility = catalog_data.asset_visibility()
    campaign_visibility = visibility.iloc[1].copy()
    campaign_visibility[V.USER_NAME] = "ALICE"
    visibility = pd.concat([visibility, campaign_visibility.to_frame().T], ignore_index=True)
    monkeypatch.setattr(
        catalog_fake,
        "load_asset_visibility",
        lambda: visibility.sort_values(
            [V.DATABASE_NAME, V.SCHEMA_NAME, V.ASSET_NAME],
            ascending=False,
        ).reset_index(drop=True),
    )
    app = AppTest.from_file(USERS_PAGE).run()
    app.session_state[state.NAV_TO_USER_NAME] = "ALICE"

    app.run()

    assert_no_exception(app)
    result = dataframe_value(app, index=1)
    assert result[["データベース", "スキーマ", "名前"]].values.tolist() == [
        [catalog_data.DB, "DATA_AD", "CAMPAIGN_LEADS"],
        [catalog_data.DB, "DATA_SALES", "ORDERS"],
    ]


def test_users_page_filters_only_self_in_fake_mode(users_app: AppTest) -> None:
    app = users_app.run()

    app.toggle[0].set_value(True).run()

    assert_no_exception(app)
    assert app.text_input[0].disabled
    assert app.checkbox[0].disabled
    assert app.checkbox[1].disabled
    result = dataframe_value(app)
    assert result["名前"].tolist() == ["ALICE"]


def test_users_page_forces_only_self_when_setting_is_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CATALOG_DATA_MODE", "fake")
    monkeypatch.setattr("settings.IS_VISIBLE_ONLY_SELF_USER", True)
    app = AppTest.from_file(USERS_PAGE).run()

    assert_no_exception(app)
    assert [(toggle.label, toggle.value, toggle.disabled) for toggle in app.toggle] == [
        ("ログインユーザーのみ表示", True, True)
    ]
    assert app.text_input[0].disabled
    assert dataframe_value(app)["名前"].tolist() == ["ALICE"]


def test_users_page_stops_when_current_user_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CATALOG_DATA_MODE", "snowflake")
    monkeypatch.setattr("settings.IS_VISIBLE_ONLY_SELF_USER", True)
    app = AppTest.from_file(USERS_PAGE).run()

    assert_no_exception(app)
    assert [(toggle.label, toggle.value, toggle.disabled) for toggle in app.toggle] == [
        ("ログインユーザーのみ表示", True, True)
    ]
    assert [warning.value for warning in app.warning] == [
        "ログインユーザー名を取得できないため、ログインユーザーのみ表示を適用できません。"
    ]
    assert len(app.dataframe) == 0


def test_users_page_clear_button_resets_search_widgets(users_app: AppTest) -> None:
    app = users_app.run()

    app.text_input[0].set_value("service").run()
    assert dataframe_value(app)["名前"].tolist() == ["SVC_ETL"]

    app.button[0].click().run()

    assert_no_exception(app)
    assert app.toggle[0].value is False
    assert app.text_input[0].value == ""
    assert app.checkbox[0].value is True
    assert app.checkbox[1].value is True
    assert dataframe_value(app)["名前"].tolist() == ["ALICE", "BOB", "SVC_ETL"]


def test_users_page_clears_selection_when_search_condition_changes(
    users_app: AppTest,
) -> None:
    app = users_app.run()

    app.session_state[state.USER_SELECTED_NAME] = "ALICE"
    assert app.session_state[state.USER_SELECTED_NAME] == "ALICE"

    app.text_input[0].set_value("service").run()

    assert_no_exception(app)
    assert state.USER_SELECTED_NAME not in app.session_state
    assert dataframe_value(app)["名前"].tolist() == ["SVC_ETL"]


def test_users_page_shows_empty_message_when_no_user_matches(users_app: AppTest) -> None:
    app = users_app.run()

    app.text_input[0].set_value("not-found").run()

    assert_no_exception(app)
    assert [info.value for info in app.info] == [
        "該当するユーザーがいません。検索条件を変更してください。"
    ]
    assert len(app.dataframe) == 0


def test_users_page_shows_large_results_without_pagination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CATALOG_DATA_MODE", "fake")
    monkeypatch.setattr(catalog_fake, "load_users", lambda: many_users(105))
    app = AppTest.from_file(USERS_PAGE).run()

    assert_no_exception(app)
    assert len(app.number_input) == 0
    assert len(dataframe_value(app)) == 105


def test_users_page_shows_traceback_in_fake_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CATALOG_DATA_MODE", "fake")

    def load_users() -> pd.DataFrame:
        raise RuntimeError("fake users exploded")

    monkeypatch.setattr(catalog_fake, "load_users", load_users)
    app = AppTest.from_file(USERS_PAGE).run()

    assert [error.value for error in app.error] == [
        "データの取得に失敗しました。接続設定やカタログテーブルの生成状況をご確認ください。"
    ]
    assert len(app.exception) == 1
    assert "fake users exploded" in str(app.exception[0].value)


def test_users_page_hides_traceback_outside_fake_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CATALOG_DATA_MODE", "snowflake")

    def load_users() -> pd.DataFrame:
        raise RuntimeError("snowflake users exploded")

    monkeypatch.setattr("lib.catalog_snowflake.load_users", load_users)
    app = AppTest.from_file(USERS_PAGE).run()

    assert [error.value for error in app.error] == [
        "データの取得に失敗しました。接続設定やカタログテーブルの生成状況をご確認ください。"
    ]
    assert len(app.exception) == 0

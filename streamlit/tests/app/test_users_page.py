# ruff: noqa: S101

from __future__ import annotations

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from catalog import schema
from catalog.providers import fake as catalog_fake
from runtime import state
from tests.app.conftest import USERS_PAGE, assert_no_exception, checkbox_by_label, dataframe_value
from tests.fixtures import catalog_data

BASE_USER = catalog_data.users().iloc[0].to_dict()
LARGE_RESULT_COUNT = 105


def many_users(count: int) -> pd.DataFrame:
    """指定件数の fake ユーザーを返す。"""
    users_schema = schema.Users
    return pd.DataFrame(
        {
            **BASE_USER,
            users_schema.USER_NAME: f"USER_{user_id:03d}",
            users_schema.DISPLAY_NAME: f"User {user_id:03d}",
        }
        for user_id in range(1, count + 1)
    )


def test_users_page_initial_state_shows_all_users(users_app: AppTest) -> None:
    """初期状態では全ユーザーを表示する。"""
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
    """ページ遷移 state からユーザー詳細を開く。"""
    app = users_app.run()
    app.session_state[state.NAV_TO_USER_NAME] = "ALICE"

    app.run()

    assert_no_exception(app)
    assert [subheader.value for subheader in app.subheader] == ["ALICE"]
    assert state.NAV_TO_USER_NAME not in app.session_state

    app.run()

    assert_no_exception(app)
    assert [subheader.value for subheader in app.subheader] == ["ALICE"]


def test_users_page_navigation_clears_freeword_that_hides_target(
    users_app: AppTest,
) -> None:
    """遷移先を隠すフリーワードを解除する。"""
    app = users_app
    app.session_state[state.SEARCH_USER_FREEWORD] = "bob"
    app.session_state[state.SEARCH_USER_ONLY_SELF] = False
    app.session_state[state.SEARCH_USER_TARGET_USER_NAME] = True
    app.session_state[state.SEARCH_USER_TARGET_DISPLAY_NAME] = True
    app.session_state[state.NAV_TO_USER_NAME] = "ALICE"

    app.run()

    assert_no_exception(app)
    assert app.text_input[0].value == ""
    assert dataframe_value(app)["名前"].tolist() == ["ALICE", "BOB", "SVC_ETL"]
    assert [subheader.value for subheader in app.subheader] == ["ALICE"]


def test_users_page_filters_by_freeword(users_app: AppTest) -> None:
    """フリーワードでユーザーを絞り込む。"""
    app = users_app.run()

    app.text_input[0].set_value("service").run()

    assert_no_exception(app)
    result = dataframe_value(app)
    assert result["名前"].tolist() == ["SVC_ETL"]
    assert result["表示名"].tolist() == ["ETL Service"]


def test_users_page_disables_freeword_when_all_targets_are_off(
    users_app: AppTest,
) -> None:
    """検索対象がない場合はフリーワード入力を無効化する。"""
    app = users_app.run()

    app.text_input[0].set_value("service").run()
    checkbox_by_label(app, "ユーザーの名前").set_value(False).run()
    checkbox_by_label(app, "ユーザーの表示名").set_value(False).run()

    assert_no_exception(app)
    assert app.text_input[0].disabled
    assert app.text_input[0].value == ""
    assert not checkbox_by_label(app, "ユーザーの名前").disabled
    assert not checkbox_by_label(app, "ユーザーの表示名").disabled
    assert dataframe_value(app)["名前"].tolist() == ["ALICE", "BOB", "SVC_ETL"]

    checkbox_by_label(app, "ユーザーの名前").set_value(True).run()

    assert_no_exception(app)
    assert not app.text_input[0].disabled


def test_users_page_orders_visible_assets_by_hierarchy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """詳細の閲覧可能資産を階層順で表示する。"""
    monkeypatch.setenv("CATALOG_DATA_MODE", "fake")
    visibility_schema = schema.AssetVisibility
    visibility = catalog_data.asset_visibility()
    campaign_visibility = visibility.iloc[1].copy()
    campaign_visibility[visibility_schema.USER_NAME] = "ALICE"
    campaign_visibility[visibility_schema.USER_ROLES] = ["MARKETER", "ANALYST"]
    campaign_visibility[visibility_schema.ASSET_ROLES] = ["SALES_READER", "AD_READER"]
    visibility = pd.concat([visibility, campaign_visibility.to_frame().T], ignore_index=True)
    monkeypatch.setattr(
        catalog_fake,
        "load_asset_visibility",
        lambda: visibility.sort_values(
            [
                visibility_schema.DATABASE_NAME,
                visibility_schema.SCHEMA_NAME,
                visibility_schema.ASSET_NAME,
            ],
            ascending=False,
        ).reset_index(drop=True),
    )
    app = AppTest.from_file(USERS_PAGE).run()
    app.session_state[state.NAV_TO_USER_NAME] = "ALICE"

    app.run()

    assert_no_exception(app)
    result = dataframe_value(app, index=1)
    assert result[["データベース", "スキーマ", "名前"]].to_numpy().tolist() == [
        [catalog_data.DB, "DATA_AD", "CAMPAIGN_LEADS"],
        [catalog_data.DB, "DATA_SALES", "ORDERS"],
    ]
    assert result["ユーザー付与ロール"].tolist()[0] == "ANALYST, MARKETER"
    assert result["データ資産付与ロール"].tolist()[0] == "AD_READER, SALES_READER"
    assert "データ資産: 2 件" in [caption.value for caption in app.caption]


def test_users_page_filters_only_self_in_fake_mode(users_app: AppTest) -> None:
    """fake mode でログインユーザーのみ表示を適用する。"""
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
    """設定有効時はログインユーザーのみ表示を強制する。"""
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
    """現在ユーザー不明時は検索を停止する。"""
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
    """クリアボタンで検索ウィジェットを初期化する。"""
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
    """検索条件変更時に選択中詳細を解除する。"""
    app = users_app.run()

    app.session_state[state.USER_SELECTED_NAME] = "ALICE"
    assert app.session_state[state.USER_SELECTED_NAME] == "ALICE"

    app.text_input[0].set_value("service").run()

    assert_no_exception(app)
    assert state.USER_SELECTED_NAME not in app.session_state
    assert dataframe_value(app)["名前"].tolist() == ["SVC_ETL"]


def test_users_page_shows_empty_message_when_no_user_matches(users_app: AppTest) -> None:
    """検索結果が空の場合の案内を表示する。"""
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
    """大量結果でもページネーションを表示しない。"""
    monkeypatch.setenv("CATALOG_DATA_MODE", "fake")
    monkeypatch.setattr(catalog_fake, "load_users", lambda: many_users(LARGE_RESULT_COUNT))
    app = AppTest.from_file(USERS_PAGE).run()

    assert_no_exception(app)
    assert len(app.number_input) == 0
    assert len(dataframe_value(app)) == LARGE_RESULT_COUNT


def test_users_page_shows_traceback_in_fake_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """fake mode の取得失敗では例外詳細を表示する。"""
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
    """Snowflake mode の取得失敗では例外詳細を隠す。"""
    monkeypatch.setenv("CATALOG_DATA_MODE", "snowflake")

    def load_users() -> pd.DataFrame:
        raise RuntimeError("snowflake users exploded")

    monkeypatch.setattr("catalog.providers.snowflake.load_users", load_users)
    app = AppTest.from_file(USERS_PAGE).run()

    assert [error.value for error in app.error] == [
        "データの取得に失敗しました。接続設定やカタログテーブルの生成状況をご確認ください。"
    ]
    assert len(app.exception) == 0

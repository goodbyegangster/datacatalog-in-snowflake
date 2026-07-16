# ruff: noqa: S101

from __future__ import annotations

from typing import NoReturn

import pytest
from streamlit.testing.v1 import AppTest

from catalog.providers import fake as catalog_fake
from runtime import state
from tests.app.conftest import GRAPH_PAGE, assert_no_exception


def test_graph_page_requires_selected_target(monkeypatch: pytest.MonkeyPatch) -> None:
    """表示対象未選択時に案内を表示する。"""
    monkeypatch.setenv("CATALOG_DATA_MODE", "fake")
    app = AppTest.from_file(GRAPH_PAGE).run()

    assert_no_exception(app)
    assert [title.value for title in app.title] == ["🌐 ロール継承グラフ"]
    assert [info.value for info in app.info] == ["ロール継承グラフの表示対象が選択されていません。"]


def test_graph_page_shows_graph_target_and_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    """assets 由来の表示対象と経路を表示する。"""
    monkeypatch.setenv("CATALOG_DATA_MODE", "fake")
    app = AppTest.from_file(GRAPH_PAGE)
    app.session_state[state.NAV_GRAPH_USER_NAME] = "ALICE"
    app.session_state[state.NAV_GRAPH_TABLE_ID] = 1
    app.session_state[state.NAV_GRAPH_ASSET_FQN] = "hogehoge.DATA_SALES.ORDERS"
    app.session_state[state.NAV_GRAPH_RETURN_PAGE] = "assets"

    app.run()

    assert_no_exception(app)
    assert [title.value for title in app.title] == ["🌐 ロール継承グラフ"]
    assert any("**ALICE** から **hogehoge.DATA_SALES.ORDERS**" in md.value for md in app.markdown)
    assert [button.label for button in app.button] == ["データ資産に戻る", "ユーザーを開く"]
    assert [caption.value for caption in app.caption] == ["1 経路"]
    assert len(app.dataframe) == 0


def test_graph_page_shows_user_return_button_from_users(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """users 由来の戻り先ボタンを表示する。"""
    monkeypatch.setenv("CATALOG_DATA_MODE", "fake")
    app = AppTest.from_file(GRAPH_PAGE)
    app.session_state[state.NAV_GRAPH_USER_NAME] = "ALICE"
    app.session_state[state.NAV_GRAPH_TABLE_ID] = 1
    app.session_state[state.NAV_GRAPH_ASSET_FQN] = "hogehoge.DATA_SALES.ORDERS"
    app.session_state[state.NAV_GRAPH_RETURN_PAGE] = "users"

    app.run()

    assert_no_exception(app)
    assert [button.label for button in app.button] == ["ユーザーに戻る", "データ資産を開く"]


def test_graph_page_shows_open_buttons_without_return_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """戻り元がない場合に詳細ページを開くボタンを表示する。"""
    monkeypatch.setenv("CATALOG_DATA_MODE", "fake")
    app = AppTest.from_file(GRAPH_PAGE)
    app.session_state[state.NAV_GRAPH_USER_NAME] = "ALICE"
    app.session_state[state.NAV_GRAPH_TABLE_ID] = 1
    app.session_state[state.NAV_GRAPH_ASSET_FQN] = "hogehoge.DATA_SALES.ORDERS"

    app.run()

    assert_no_exception(app)
    assert [button.label for button in app.button] == ["ユーザーを開く", "データ資産を開く"]


def test_graph_page_shows_traceback_in_fake_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """fake mode の取得失敗では例外詳細を表示する。"""
    monkeypatch.setenv("CATALOG_DATA_MODE", "fake")

    def load_access_edges() -> NoReturn:
        raise RuntimeError("fake graph exploded")

    monkeypatch.setattr(catalog_fake, "load_access_edges", load_access_edges)
    app = AppTest.from_file(GRAPH_PAGE)
    app.session_state[state.NAV_GRAPH_USER_NAME] = "ALICE"
    app.session_state[state.NAV_GRAPH_TABLE_ID] = 1
    app.session_state[state.NAV_GRAPH_ASSET_FQN] = "hogehoge.DATA_SALES.ORDERS"

    app.run()

    assert [error.value for error in app.error] == [
        "データの取得に失敗しました。接続設定やカタログテーブルの生成状況をご確認ください。"
    ]
    assert len(app.exception) == 1
    assert "fake graph exploded" in str(app.exception[0].value)

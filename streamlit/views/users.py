"""page：ユーザー。

design-view.md の「page：ユーザー」に対応。検索 UI は sidebar に配置し、本文側に
ユーザー一覧・詳細ペインを表示する。初期は全ユーザー表示。

詳細ペインでは、選択ユーザーの基本情報と閲覧可能なデータ資産を表示する。
閲覧可能データ資産一覧では、行選択後のボタン操作でロール継承グラフを表示する。
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
import styles

from catalog import provider as catalog
from catalog import schema
from components.users import detail as user_detail
from components.users import results as user_results
from components.users import search as user_search
from logic import search
from runtime import state


def _render_base_css() -> None:
    """全ページ共通 CSS を適用する。"""
    styles.render_base_css()


def _consume_nav_to_user_name(users: pd.DataFrame) -> str | None:
    """ページ間遷移で指定されたユーザー名を取り出し、存在する場合のみ返す。"""
    user_name = st.session_state.pop(state.NAV_TO_USER_NAME, None)
    if user_name is None:
        return None

    normalized = str(user_name).upper()
    U = schema.Users
    if normalized in set(users[U.USER_NAME].astype(str).str.upper().tolist()):
        st.session_state[state.USER_SELECTED_NAME] = normalized
        return normalized
    return None


def main() -> None:
    st.title("👤 ユーザー", anchor=False)
    _render_base_css()

    main_pane = st.container()
    with st.sidebar:
        freeword, only_user_name, only_self = user_search.render()

    with main_pane:
        if only_self and only_user_name is None:
            user_results.clear_selection()
            st.warning(user_search.CURRENT_USER_UNAVAILABLE_MESSAGE)
            return

        try:
            users = catalog.load_users()
            visibility = catalog.load_asset_visibility()
        except Exception as exc:
            st.error(
                "データの取得に失敗しました。接続設定やカタログテーブルの生成状況をご確認ください。"
            )
            if catalog.data_mode() == "fake":
                st.exception(exc)
            return

        search_fingerprint = user_search.fingerprint(freeword, only_user_name)
        if st.session_state.get(state.USER_SEARCH_FINGERPRINT) != search_fingerprint:
            user_results.clear_selection()
            st.session_state[state.USER_SEARCH_FINGERPRINT] = search_fingerprint

        _consume_nav_to_user_name(users)

        filtered = search.filter_users(users, freeword, only_user_name=only_user_name)
        if filtered.empty:
            user_results.clear_selection()
            st.info("該当するユーザーがいません。検索条件を変更してください。")
            return

        prior = st.session_state.get(state.USER_SELECTED_NAME)
        U = schema.Users
        if prior is not None and prior not in set(filtered[U.USER_NAME].astype(str).tolist()):
            user_results.clear_selection()
            prior = None

        if prior is None:
            selected_now = user_results.render(filtered)
        else:
            list_col, detail_col = st.columns([1, 3])
            with list_col:
                selected_now = user_results.render(filtered, compact=True)
            with detail_col:
                user_detail.render(prior, users, visibility)

        # 選択セルがない rerun は、詳細ペイン内の操作でも発生するため既存詳細を維持する。
        if selected_now is not None and selected_now != prior:
            st.session_state[state.USER_SELECTED_NAME] = selected_now
            st.rerun()


main()

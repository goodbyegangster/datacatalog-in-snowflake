"""View ユーザー。"""

from __future__ import annotations

from dataclasses import dataclass

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
from views.common import error_handling


@dataclass(frozen=True)
class UserCatalogData:
    """ユーザーページで利用するカタログデータ。"""

    users: pd.DataFrame
    visibility: pd.DataFrame


def _render_base_css() -> None:
    """全ページ共通 CSS を適用する。"""
    styles.render_base_css()


def _get_nav_user_name_to_show(users: pd.DataFrame) -> str | None:
    """遷移元から指定された表示対象のユーザー名を返す。

    取得した NAV_TO_USER_NAME は session_state から削除する。
    """
    user_name = st.session_state.pop(state.NAV_TO_USER_NAME, None)
    if user_name is None:
        return None

    normalized = str(user_name).upper()
    users_schema = schema.Users
    if normalized in set(users[users_schema.USER_NAME].astype(str).str.upper().tolist()):
        return normalized
    return None


def _load_catalog_data() -> UserCatalogData | None:
    """ユーザーページで利用するカタログデータを読み込む。"""
    try:
        users = catalog.load_users()
        visibility = catalog.load_asset_visibility()
    except Exception as exc:
        error_handling.render_catalog_load_error(exc)
        return None
    return UserCatalogData(users=users, visibility=visibility)


def _clear_selection_when_search_changed(criteria: user_search.UserSearchCriteria) -> None:
    """検索条件変更時に選択状態を解除する。"""
    search_fingerprint = user_search.build_fingerprint(criteria)
    if st.session_state.get(state.USER_SEARCH_FINGERPRINT) != search_fingerprint:
        user_results.clear_user_selection()
        st.session_state[state.USER_SEARCH_FINGERPRINT] = search_fingerprint


def _resolve_selected_user_name(filtered: pd.DataFrame) -> str | None:
    """検索結果内で維持できる選択ユーザー名を返す。"""
    prior = st.session_state.get(state.USER_SELECTED_NAME)
    users_schema = schema.Users
    if prior is not None and prior not in set(
        filtered[users_schema.USER_NAME].astype(str).tolist()
    ):
        user_results.clear_user_selection()
        return None
    return prior


def _rerun_when_selection_changed(selected_now: str | None, prior: str | None) -> None:
    """選択ユーザーが変わった場合に詳細ペインを更新する。"""
    # 詳細ペイン内の操作でも selected_now は None になり得るため、既存詳細を維持する。
    if selected_now is not None and selected_now != prior:
        st.session_state[state.USER_SELECTED_NAME] = selected_now
        st.rerun()


def _render_users_with_detail(
    *,
    filtered: pd.DataFrame,
    catalog_data: UserCatalogData,
) -> None:
    """ユーザー検索結果と選択ユーザーの詳細を表示する。"""
    prior = _resolve_selected_user_name(filtered)
    if prior is None:
        selected_now = user_results.render(filtered)
    else:
        list_col, detail_col = st.columns([1, 3])
        with list_col:
            selected_now = user_results.render(filtered, compact=True)
        with detail_col:
            user_detail.render(prior, catalog_data.users, catalog_data.visibility)

    _rerun_when_selection_changed(selected_now, prior)


def _render_filtered_users(
    *,
    catalog_data: UserCatalogData,
    criteria: user_search.UserSearchCriteria,
) -> None:
    """検索条件に一致するユーザー一覧と詳細を表示する。"""
    filtered = search.filter_users(
        catalog_data.users,
        criteria.freeword,
        current_user_filter_name=criteria.current_user_filter_name,
    )
    if filtered.empty:
        user_results.clear_user_selection()
        st.info("該当するユーザーがいません。検索条件を変更してください。")
        return

    _render_users_with_detail(filtered=filtered, catalog_data=catalog_data)


def main() -> None:
    """ユーザーページを描画する。"""
    st.title("👤 ユーザー", anchor=False)
    _render_base_css()

    main_pane = st.container()
    if state.NAV_TO_USER_NAME in st.session_state:
        user_search.set_all_users_view_for_navigation()
    with st.sidebar:
        criteria = user_search.render()

    with main_pane:
        if criteria.is_only_self_filter_enabled and criteria.current_user_filter_name is None:
            user_results.clear_user_selection()
            st.warning(user_search.CURRENT_USER_UNAVAILABLE_MESSAGE)
            return

        catalog_data = _load_catalog_data()
        if catalog_data is None:
            return

        _clear_selection_when_search_changed(criteria)

        nav_user_name = _get_nav_user_name_to_show(catalog_data.users)
        if nav_user_name is not None:
            st.session_state[state.USER_SELECTED_NAME] = nav_user_name

        _render_filtered_users(
            catalog_data=catalog_data,
            criteria=criteria,
        )


main()

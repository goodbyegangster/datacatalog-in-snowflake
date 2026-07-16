"""ページ間遷移の state 契約を扱う。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import streamlit as st

from runtime import state

ASSETS_PAGE = "views/assets.py"
USERS_PAGE = "views/users.py"
GRAPH_PAGE = "views/graph.py"

GraphReturnPage = Literal["assets", "users"]

RETURN_PAGE_PATHS: dict[GraphReturnPage, str] = {
    "assets": ASSETS_PAGE,
    "users": USERS_PAGE,
}


@dataclass(frozen=True)
class GraphTarget:
    """ロール継承グラフに表示するユーザー・資産ペア。"""

    user_name: str
    table_id: int
    asset_fqn: str


def open_user_page(user_name: str) -> None:
    """ユーザーページで指定ユーザーを開く。"""
    st.session_state[state.NAV_TO_USER_NAME] = user_name
    st.session_state.pop(state.USER_SELECTED_NAME, None)
    st.switch_page(USERS_PAGE)


def open_asset_page(table_id: int) -> None:
    """データ資産ページで指定資産を開く。"""
    st.session_state[state.NAV_TO_TABLE_ID] = int(table_id)
    st.session_state.pop(state.ASSET_SELECTED_TABLE_ID, None)
    st.switch_page(ASSETS_PAGE)


def open_graph_page(
    *,
    user_name: str,
    table_id: int,
    asset_fqn: str,
    return_page: GraphReturnPage,
) -> None:
    """選択されたユーザー・資産ペアをロール継承グラフページで開く。"""
    st.session_state[state.NAV_GRAPH_USER_NAME] = user_name
    st.session_state[state.NAV_GRAPH_TABLE_ID] = int(table_id)
    st.session_state[state.NAV_GRAPH_ASSET_FQN] = asset_fqn
    st.session_state[state.NAV_GRAPH_RETURN_PAGE] = return_page
    st.switch_page(GRAPH_PAGE)


def resolve_graph_target() -> GraphTarget | None:
    """session_state から graph 表示対象を解決する。"""
    user_name = st.session_state.get(state.NAV_GRAPH_USER_NAME)
    table_id = st.session_state.get(state.NAV_GRAPH_TABLE_ID)
    asset_fqn = st.session_state.get(state.NAV_GRAPH_ASSET_FQN)
    if user_name is None or table_id is None or asset_fqn is None:
        return None

    try:
        normalized_table_id = int(table_id)
    except (TypeError, ValueError):
        return None

    return GraphTarget(
        user_name=str(user_name),
        table_id=normalized_table_id,
        asset_fqn=str(asset_fqn),
    )


def resolve_graph_return_page() -> GraphReturnPage | None:
    """session_state から graph 表示元ページを解決する。"""
    value = st.session_state.get(state.NAV_GRAPH_RETURN_PAGE)
    if value not in RETURN_PAGE_PATHS:
        return None
    return value


def return_from_graph(return_page: GraphReturnPage, *, user_name: str, table_id: int) -> None:
    """graph 表示元ページへ戻る。"""
    if return_page == "assets":
        st.session_state[state.ASSET_SELECTED_TABLE_ID] = int(table_id)
    elif return_page == "users":
        st.session_state[state.USER_SELECTED_NAME] = user_name
    st.switch_page(RETURN_PAGE_PATHS[return_page])

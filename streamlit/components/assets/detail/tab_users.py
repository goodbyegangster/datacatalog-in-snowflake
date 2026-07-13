"""データ資産詳細のユーザー tab component。"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import settings
from catalog import schema
from runtime import state, user_context

TABLE_KEY = "asset_users_table"
CURRENT_USER_UNAVAILABLE_MESSAGE = (
    "ログインユーザー名を取得できないため、ログインユーザーのみ表示を適用できません。"
)


def _fmt_roles(roles: object) -> str:
    """ロール配列を dataframe 表示向けに整形する。"""
    if not isinstance(roles, list) or not roles:
        return ""
    return ", ".join(sorted(str(role) for role in roles))


def _set_user_page_navigation(user_name: str) -> None:
    """ユーザーページへ遷移するための状態を積む。"""
    st.session_state[state.NAV_TO_USER_NAME] = user_name
    st.session_state.pop(state.USER_SELECTED_NAME, None)


def _set_graph_page_navigation(*, user_name: str, table_id: int, asset_fqn: str) -> None:
    """ロール継承グラフページへ遷移するための状態を積む。"""
    st.session_state[state.NAV_GRAPH_USER_NAME] = user_name
    st.session_state[state.NAV_GRAPH_TABLE_ID] = int(table_id)
    st.session_state[state.NAV_GRAPH_ASSET_FQN] = asset_fqn
    st.session_state[state.NAV_GRAPH_RETURN_PAGE] = "assets"


def _selected_user_row(event: object, display: pd.DataFrame) -> int | None:
    """ユーザータブで選択されたセルの行位置を返す。"""
    cells = event.selection.cells
    if not cells:
        return None

    cell = cells[0]
    row_index = cell["row"] if isinstance(cell, dict) else cell[0]
    if row_index >= len(display):
        return None
    return int(row_index)


def render(asset: pd.Series, visibility: pd.DataFrame) -> None:
    """ユーザー tab を表示する。"""
    A = schema.Assets
    V = schema.AssetVisibility
    table_id = int(asset[A.TABLE_ID])
    vis = visibility[visibility[V.TABLE_ID] == table_id]
    if settings.IS_VISIBLE_ONLY_SELF_USER:
        current_user_name = user_context.current_user_name()
        if current_user_name is None:
            st.warning(CURRENT_USER_UNAVAILABLE_MESSAGE)
            return
        vis = vis[vis[V.USER_NAME] == current_user_name]

    if vis.empty:
        st.caption("閲覧可能なユーザーがいません")
        return

    vis = vis.sort_values(V.USER_NAME).reset_index(drop=True)
    display = pd.DataFrame(
        {
            "ユーザー": vis[V.USER_NAME],
            "ユーザー付与ロール": vis[V.USER_ROLES].map(_fmt_roles),
            "データ資産付与ロール": vis[V.ASSET_ROLES].map(_fmt_roles),
        }
    ).reset_index(drop=True)
    action_slot = st.container()
    event = st.dataframe(
        display,
        hide_index=True,
        height="auto",
        width="stretch",
        selection_mode="single-cell",
        on_select="rerun",
        key=f"{TABLE_KEY}_{table_id}",
        column_config={
            "ユーザー": st.column_config.TextColumn(width="medium"),
            "ユーザー付与ロール": st.column_config.TextColumn(width="medium"),
            "データ資産付与ロール": st.column_config.TextColumn(width="medium"),
        },
    )

    selected_user_row = _selected_user_row(event, display)
    selected_user_name = (
        None if selected_user_row is None else str(display.iloc[selected_user_row]["ユーザー"])
    )
    asset_fqn = ".".join(
        [
            str(asset[A.DATABASE_NAME]),
            str(asset[A.SCHEMA_NAME]),
            str(asset[A.ASSET_NAME]),
        ]
    )
    with action_slot:
        open_col, graph_col = st.columns(2)
        with open_col:
            if st.button(
                "選択ユーザーを開く",
                icon=":material/person_search:",
                disabled=selected_user_name is None,
                key=f"asset_user_open_button_{table_id}",
                width="stretch",
            ):
                _set_user_page_navigation(selected_user_name or "")
                st.switch_page("views/users.py")
        with graph_col:
            if st.button(
                "ロール継承グラフを表示",
                icon=":material/account_tree:",
                disabled=selected_user_name is None,
                key=f"asset_user_graph_button_{table_id}",
                width="stretch",
            ):
                _set_graph_page_navigation(
                    user_name=selected_user_name or "",
                    table_id=table_id,
                    asset_fqn=asset_fqn,
                )
                st.switch_page("views/graph.py")
        st.caption("行を選択してから、必要な操作ボタンを押してください")

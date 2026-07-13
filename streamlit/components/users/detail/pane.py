"""ユーザーページの詳細 component。"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from catalog import schema
from components.users import results
from runtime import state

ASSETS_TABLE_KEY = "user_assets_table"
USER_TYPE_BADGE_COLORS = {
    "PERSON": "blue",
    "SERVICE": "orange",
    "LEGACY_SERVICE": "gray",
}


def _fmt_roles(roles: object) -> str:
    """ロール配列を dataframe 表示向けに整形する。"""
    if not isinstance(roles, list) or not roles:
        return ""
    return ", ".join(sorted(str(role) for role in roles))


def _display_user_type(user_type: object) -> str:
    """Snowflake ユーザー種別を表示用に正規化する。"""
    if pd.isna(user_type) or user_type == "":
        return "PERSON"
    return str(user_type)


def _user_type_badge_color(user_type: str) -> str:
    """ユーザー種別に応じた badge 色を返す。"""
    return USER_TYPE_BADGE_COLORS.get(user_type, "gray")


def _close() -> None:
    """詳細ペインを閉じる。行選択ウィジェットの選択状態も解除する。"""
    results.clear_selection()
    st.session_state.pop(state.NAV_TO_USER_NAME, None)


def _set_asset_page_navigation(table_id: int) -> None:
    """データ資産ページへ遷移するための状態を積む。"""
    st.session_state[state.NAV_TO_TABLE_ID] = int(table_id)
    st.session_state.pop(state.ASSET_SELECTED_TABLE_ID, None)


def _set_graph_page_navigation(*, user_name: str, table_id: int, asset_fqn: str) -> None:
    """ロール継承グラフページへ遷移するための状態を積む。"""
    st.session_state[state.NAV_GRAPH_USER_NAME] = user_name
    st.session_state[state.NAV_GRAPH_TABLE_ID] = int(table_id)
    st.session_state[state.NAV_GRAPH_ASSET_FQN] = asset_fqn
    st.session_state[state.NAV_GRAPH_RETURN_PAGE] = "users"


def _selected_asset_row(event: object, display: pd.DataFrame) -> int | None:
    """閲覧可能データ資産一覧で選択されたセルの行位置を返す。"""
    cells = event.selection.cells
    if not cells:
        return None

    cell = cells[0]
    row_index = cell["row"] if isinstance(cell, dict) else cell[0]
    if row_index >= len(display):
        return None
    return int(row_index)


def render(user_name: str, users: pd.DataFrame, visibility: pd.DataFrame) -> None:
    """ユーザーの詳細ペインを表示する。"""
    U = schema.Users
    match = users[users[U.USER_NAME] == user_name]
    if match.empty:
        st.error("選択されたユーザーが見つかりませんでした。")
        return
    user = match.iloc[0]

    title_col, close_col = st.columns([1, 0.12], vertical_alignment="center")
    with title_col:
        st.subheader(user[U.USER_NAME], anchor=False)
    with close_col:
        st.button(
            "",
            icon=":material/close:",
            help="詳細を閉じる",
            on_click=_close,
            key="user_detail_close",
            type="primary",
        )

    display_name = user[U.DISPLAY_NAME]
    if pd.notna(display_name) and str(display_name) != "":
        st.markdown(f"**{display_name}**")

    user_type = _display_user_type(user[U.USER_TYPE])
    disabled = bool(user[U.DISABLED])
    col1, col2 = st.columns(2)
    with col1:
        st.caption("タイプ")
        st.badge(user_type, color=_user_type_badge_color(user_type))
    with col2:
        st.caption("ステータス")
        st.badge("無効" if disabled else "有効", color="red" if disabled else "green")

    V = schema.AssetVisibility
    vis = visibility[visibility[V.USER_NAME] == user_name]
    st.markdown("**閲覧可能なデータ資産**")
    if vis.empty:
        st.caption("閲覧可能なデータ資産がありません。")
        return

    vis_display_source = vis.sort_values(
        [V.DATABASE_NAME, V.SCHEMA_NAME, V.ASSET_NAME]
    ).reset_index(drop=True)
    display = pd.DataFrame(
        {
            "データベース": vis_display_source[V.DATABASE_NAME],
            "スキーマ": vis_display_source[V.SCHEMA_NAME],
            "名前": vis_display_source[V.ASSET_NAME],
            "ユーザー付与ロール": vis_display_source[V.USER_ROLES].map(_fmt_roles),
            "データ資産付与ロール": vis_display_source[V.ASSET_ROLES].map(_fmt_roles),
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
        key=f"{ASSETS_TABLE_KEY}_{user_name}",
        column_config={
            "データベース": st.column_config.TextColumn(width="small"),
            "スキーマ": st.column_config.TextColumn(width="small"),
            "名前": st.column_config.TextColumn(width="medium"),
            "ユーザー付与ロール": st.column_config.TextColumn(width="medium"),
            "データ資産付与ロール": st.column_config.TextColumn(width="medium"),
        },
    )

    selected_asset_row = _selected_asset_row(event, display)
    selected_table_id = (
        None
        if selected_asset_row is None
        else int(vis_display_source.iloc[selected_asset_row][V.TABLE_ID])
    )
    with action_slot:
        open_col, graph_col = st.columns(2)
        with open_col:
            if st.button(
                "選択データ資産を開く",
                icon=":material/table_view:",
                disabled=selected_table_id is None,
                key=f"user_asset_open_button_{user_name}",
                width="stretch",
            ):
                _set_asset_page_navigation(selected_table_id or 0)
                st.switch_page("views/assets.py")
        with graph_col:
            if st.button(
                "ロール継承グラフを表示",
                icon=":material/account_tree:",
                disabled=selected_asset_row is None,
                key=f"user_asset_graph_button_{user_name}",
                width="stretch",
            ):
                asset_fqn = ".".join(
                    [
                        str(display.iloc[selected_asset_row]["データベース"]),
                        str(display.iloc[selected_asset_row]["スキーマ"]),
                        str(display.iloc[selected_asset_row]["名前"]),
                    ]
                )
                _set_graph_page_navigation(
                    user_name=user_name,
                    table_id=selected_table_id or 0,
                    asset_fqn=asset_fqn,
                )
                st.switch_page("views/graph.py")
        st.caption("行を選択してから、必要な操作ボタンを押してください")

"""ユーザーページの詳細 component。"""

from __future__ import annotations

import math
from typing import Literal

import pandas as pd
import streamlit as st

from catalog import schema
from components.common import dataframe_selection, formatters
from components.users import results
from runtime import navigation, state

BadgeColor = Literal[
    "red",
    "orange",
    "yellow",
    "blue",
    "green",
    "violet",
    "gray",
    "grey",
    "primary",
]

ASSETS_TABLE_KEY = "user_assets_table"
USER_TYPE_BADGE_COLORS: dict[str, BadgeColor] = {
    "PERSON": "blue",
    "SERVICE": "orange",
    "LEGACY_SERVICE": "gray",
}


def _normalize_user_type(user_type: object) -> str:
    """Snowflake ユーザー種別を表示用に正規化する。"""
    if (
        user_type is None
        or user_type is pd.NA
        or user_type == ""
        or (isinstance(user_type, float) and math.isnan(user_type))
    ):
        return "PERSON"
    return str(user_type)


def _get_user_type_badge_color(user_type: str) -> BadgeColor:
    """ユーザー種別に応じた badge 色を返す。"""
    return USER_TYPE_BADGE_COLORS.get(user_type, "gray")


def _close() -> None:
    """詳細ペインを閉じる。行選択ウィジェットの選択状態も解除する。"""
    results.clear_user_selection()
    st.session_state.pop(state.NAV_TO_USER_NAME, None)


def render(user_name: str, users: pd.DataFrame, visibility: pd.DataFrame) -> None:
    """ユーザーの詳細ペインを表示する。"""
    users_schema = schema.Users
    match = users[users[users_schema.USER_NAME] == user_name]
    if match.empty:
        st.error("選択されたユーザーが見つかりませんでした。")
        return
    user = match.iloc[0]

    title_col, close_col = st.columns([1, 0.12], vertical_alignment="center")
    with title_col:
        st.subheader(user[users_schema.USER_NAME], anchor=False)
    with close_col:
        st.button(
            "",
            icon=":material/close:",
            help="詳細を閉じる",
            on_click=_close,
            key="user_detail_close",
            type="primary",
        )

    display_name = user[users_schema.DISPLAY_NAME]
    if pd.notna(display_name) and str(display_name) != "":
        st.markdown(f"**{display_name}**")

    user_type = _normalize_user_type(user[users_schema.USER_TYPE])
    disabled = bool(user[users_schema.DISABLED])
    col1, col2 = st.columns(2)
    with col1:
        st.caption("タイプ")
        st.badge(user_type, color=_get_user_type_badge_color(user_type))
    with col2:
        st.caption("ステータス")
        st.badge("無効" if disabled else "有効", color="red" if disabled else "green")

    visibility_schema = schema.AssetVisibility
    vis = visibility[visibility[visibility_schema.USER_NAME] == user_name]
    st.markdown("**閲覧可能なデータ資産**")
    if vis.empty:
        st.caption("閲覧可能なデータ資産がありません。")
        return

    vis_display_source = vis.sort_values(
        [
            visibility_schema.DATABASE_NAME,
            visibility_schema.SCHEMA_NAME,
            visibility_schema.ASSET_NAME,
        ]
    ).reset_index(drop=True)
    display = pd.DataFrame(
        {
            "データベース": vis_display_source[visibility_schema.DATABASE_NAME],
            "スキーマ": vis_display_source[visibility_schema.SCHEMA_NAME],
            "名前": vis_display_source[visibility_schema.ASSET_NAME],
            "ユーザー付与ロール": vis_display_source[visibility_schema.USER_ROLES].map(
                formatters.format_roles
            ),
            "データ資産付与ロール": vis_display_source[visibility_schema.ASSET_ROLES].map(
                formatters.format_roles
            ),
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

    selected_asset_row = dataframe_selection.get_selected_row_index(event, len(display))
    selected_table_id = (
        None
        if selected_asset_row is None
        else int(vis_display_source.iloc[selected_asset_row][visibility_schema.TABLE_ID])
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
                navigation.open_asset_page(selected_table_id or 0)
        with graph_col:
            if st.button(
                "ロール継承グラフを表示",
                icon=":material/account_tree:",
                disabled=selected_asset_row is None,
                key=f"user_asset_graph_button_{user_name}",
                width="stretch",
            ):
                if selected_asset_row is None:
                    return
                selected_asset = vis_display_source.iloc[selected_asset_row]
                asset_fqn = formatters.format_asset_fqn(
                    database_name=selected_asset[visibility_schema.DATABASE_NAME],
                    schema_name=selected_asset[visibility_schema.SCHEMA_NAME],
                    asset_name=selected_asset[visibility_schema.ASSET_NAME],
                )
                navigation.open_graph_page(
                    user_name=user_name,
                    table_id=selected_table_id or 0,
                    asset_fqn=asset_fqn,
                    return_page="users",
                )
        st.caption(f"データ資産: {len(display)} 件")

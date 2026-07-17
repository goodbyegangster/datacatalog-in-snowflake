"""データ資産詳細のユーザー tab component。"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import settings
from catalog import schema
from components.common import dataframe_selection, formatters
from runtime import navigation, user_context

TABLE_KEY = "asset_users_table"
CURRENT_USER_UNAVAILABLE_MESSAGE = (
    "ログインユーザー名を取得できないため、ログインユーザーのみ表示を適用できません。"
)


def render(asset: pd.Series, visibility: pd.DataFrame) -> None:
    """ユーザー tab を表示する。"""
    assets_schema = schema.Assets
    visibility_schema = schema.AssetVisibility
    table_id = int(asset[assets_schema.TABLE_ID])
    vis = visibility[visibility[visibility_schema.TABLE_ID] == table_id]
    if settings.IS_VISIBLE_ONLY_SELF_USER:
        current_user_name = user_context.current_user_name()
        if current_user_name is None:
            st.warning(CURRENT_USER_UNAVAILABLE_MESSAGE)
            return
        vis = vis[vis[visibility_schema.USER_NAME] == current_user_name]

    if vis.empty:
        if settings.IS_VISIBLE_ONLY_SELF_USER:
            st.caption("ログインユーザーには、このデータ資産の閲覧権限がありません。")
        else:
            st.caption("閲覧可能なユーザーがいません")
        return

    vis = vis.sort_values(visibility_schema.USER_NAME).reset_index(drop=True)
    display = pd.DataFrame(
        {
            "ユーザー": vis[visibility_schema.USER_NAME],
            "ユーザー付与ロール": vis[visibility_schema.USER_ROLES].map(formatters.format_roles),
            "データ資産付与ロール": vis[visibility_schema.ASSET_ROLES].map(
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
        key=f"{TABLE_KEY}_{table_id}",
        column_config={
            "ユーザー": st.column_config.TextColumn(width="medium"),
            "ユーザー付与ロール": st.column_config.TextColumn(width="medium"),
            "データ資産付与ロール": st.column_config.TextColumn(width="medium"),
        },
    )

    selected_user_row = dataframe_selection.get_selected_row_index(event, len(display))
    selected_user_name = (
        None if selected_user_row is None else str(display.iloc[selected_user_row]["ユーザー"])
    )
    asset_fqn = formatters.format_asset_fqn(
        database_name=asset[assets_schema.DATABASE_NAME],
        schema_name=asset[assets_schema.SCHEMA_NAME],
        asset_name=asset[assets_schema.ASSET_NAME],
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
                navigation.open_user_page(selected_user_name or "")
        with graph_col:
            if st.button(
                "ロール継承グラフを表示",
                icon=":material/account_tree:",
                disabled=selected_user_name is None,
                key=f"asset_user_graph_button_{table_id}",
                width="stretch",
            ):
                navigation.open_graph_page(
                    user_name=selected_user_name or "",
                    table_id=table_id,
                    asset_fqn=asset_fqn,
                    return_page="assets",
                )
        st.caption(f"ユーザー: {len(display)} 件")

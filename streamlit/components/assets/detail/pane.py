"""データ資産ページの詳細 component。"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from catalog import schema
from components.assets import results
from components.assets.detail import tab_columns, tab_contact, tab_stats, tab_users
from runtime import state

ASSET_TYPE_BADGE_COLORS = {
    "BASE TABLE": "blue",
    "VIEW": "green",
    "MATERIALIZED VIEW": "violet",
    "DYNAMIC TABLE": "orange",
    "ICEBERG TABLE": "blue",
    "HYBRID TABLE": "yellow",
    "EXTERNAL TABLE": "gray",
    "EVENT TABLE": "red",
    "TEMPORARY TABLE": "gray",
}
TAG_BADGE_COLOR_PALETTE = ("blue", "green", "orange", "violet", "red", "gray")


def _asset_type_badge_color(asset_type: str) -> str:
    """ASSET_TYPE に応じた badge 色を返す。"""
    return ASSET_TYPE_BADGE_COLORS.get(asset_type, "gray")


def _tag_badge_color(tag_name: str) -> str:
    """タグキー名から安定した badge 色を返す。"""
    index = sum(ord(char) for char in tag_name) % len(TAG_BADGE_COLOR_PALETTE)
    return TAG_BADGE_COLOR_PALETTE[index]


def _close() -> None:
    """詳細ペインを閉じる。行選択ウィジェットの選択状態も解除する。"""
    st.session_state.pop(state.ASSET_SELECTED_TABLE_ID, None)
    st.session_state.pop(results.RESULTS_KEY, None)
    st.session_state.pop(state.NAV_TO_TABLE_ID, None)


def render(
    table_id: int,
    assets: pd.DataFrame,
    columns: pd.DataFrame,
    visibility: pd.DataFrame,
) -> None:
    """データ資産の詳細ペインを表示する。"""
    A = schema.Assets
    match = assets[assets[A.TABLE_ID] == table_id]
    if match.empty:
        st.error("選択されたデータ資産が見つかりませんでした")
        return
    asset = match.iloc[0]

    with st.container(key="asset-summary"):
        title_col, close_col = st.columns([1, 0.12], vertical_alignment="center")
        with title_col:
            st.subheader(asset[A.ASSET_NAME], anchor=False)
        with close_col:
            st.button(
                "",
                icon=":material/close:",
                help="詳細を閉じる",
                on_click=_close,
                key="asset_detail_close",
                type="primary",
            )

        if asset[A.DESCRIPTION]:
            st.markdown(f"**{asset[A.DESCRIPTION]}**")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.caption("データベース")
            st.markdown(f"**{asset[A.DATABASE_NAME]}**")
        with col2:
            st.caption("スキーマ")
            st.markdown(f"**{asset[A.SCHEMA_NAME]}**")
        with col3:
            st.caption("オブジェクト種別")
            st.badge(
                asset[A.ASSET_TYPE],
                color=_asset_type_badge_color(asset[A.ASSET_TYPE]),
            )
        with col4:
            is_public = bool(asset[A.IS_PUBLIC_VISIBILITY])
            st.caption("PUBLIC")
            st.badge(
                "参照可能" if is_public else "参照不可",
                color="primary" if is_public else "gray",
            )

        st.caption("タグ")
        tags = asset[A.TAGS]
        if isinstance(tags, list) and tags:
            tag_cols = st.columns(3)
            for index, tag in enumerate(tags):
                with tag_cols[index % len(tag_cols)]:
                    tag_name = str(tag["TAG_NAME"])
                    st.badge(
                        f"{tag_name}: {tag['TAG_VALUE']}",
                        icon=":material/sell:",
                        color=_tag_badge_color(tag_name),
                    )
        else:
            st.caption("タグはありません")

    tab_columns_pane, tab_contact_pane, tab_stats_pane, tab_users_pane = st.tabs(
        ["カラム", "連絡先", "統計情報", "ユーザー"]
    )
    with tab_columns_pane:
        tab_columns.render(table_id, columns)
    with tab_contact_pane:
        tab_contact.render(asset)
    with tab_stats_pane:
        tab_stats.render(asset)
    with tab_users_pane:
        tab_users.render(asset, visibility)

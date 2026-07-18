"""データ資産ページの詳細 component。"""

from __future__ import annotations

import hashlib

import pandas as pd
import streamlit as st

from catalog import schema
from components.assets import results
from components.assets.detail import tab_columns, tab_contact, tab_stats, tab_users
from components.common.badges import StreamlitBadgeColor
from runtime import state

ASSET_TYPE_BADGE_COLORS: dict[str, StreamlitBadgeColor] = {
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
TAG_BADGE_COLOR_PALETTE: tuple[StreamlitBadgeColor, ...] = (
    "blue",
    "green",
    "orange",
    "violet",
    "red",
    "yellow",
    "gray",
    "primary",
)


def _get_asset_type_badge_color(asset_type: str) -> StreamlitBadgeColor:
    """ASSET_TYPE に応じた badge 色を返す。"""
    return ASSET_TYPE_BADGE_COLORS.get(asset_type, "gray")


def _get_tag_badge_color(tag_name: str) -> StreamlitBadgeColor:
    """タグキー名から安定した badge 色を返す。"""
    digest = hashlib.sha256(tag_name.encode("utf-8")).digest()
    index = digest[0] % len(TAG_BADGE_COLOR_PALETTE)
    return TAG_BADGE_COLOR_PALETTE[index]


def _close_detail_pane() -> None:
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
    assets_schema = schema.Assets
    match = assets[assets[assets_schema.TABLE_ID] == table_id]
    if match.empty:
        st.error("選択されたデータ資産が見つかりませんでした")
        return
    asset = match.iloc[0]

    with st.container(key="asset-summary"):
        title_col, close_col = st.columns([1, 0.12], vertical_alignment="center")
        with title_col:
            st.subheader(asset[assets_schema.ASSET_NAME], anchor=False)
        with close_col:
            st.button(
                "",
                icon=":material/close:",
                help="詳細を閉じる",
                on_click=_close_detail_pane,
                key="asset_detail_close",
                type="primary",
            )

        if asset[assets_schema.DESCRIPTION]:
            st.markdown(f"**{asset[assets_schema.DESCRIPTION]}**")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.caption("データベース")
            st.markdown(f"**{asset[assets_schema.DATABASE_NAME]}**")
        with col2:
            st.caption("スキーマ")
            st.markdown(f"**{asset[assets_schema.SCHEMA_NAME]}**")
        with col3:
            st.caption("オブジェクト種別")
            st.badge(
                asset[assets_schema.ASSET_TYPE],
                color=_get_asset_type_badge_color(asset[assets_schema.ASSET_TYPE]),
            )
        with col4:
            is_public = bool(asset[assets_schema.IS_PUBLIC_VISIBILITY])
            st.caption("PUBLIC")
            st.badge(
                "参照可能" if is_public else "参照不可",
                color="primary" if is_public else "gray",
            )

        st.caption("タグ")
        tags = asset[assets_schema.TAGS]
        if isinstance(tags, list) and tags:
            tag_cols = st.columns(3)
            for index, tag in enumerate(tags):
                with tag_cols[index % len(tag_cols)]:
                    tag_name = str(tag["TAG_NAME"])
                    st.badge(
                        f"{tag_name}: {tag['TAG_VALUE']}",
                        icon=":material/sell:",
                        color=_get_tag_badge_color(tag_name),
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

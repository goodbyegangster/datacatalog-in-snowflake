"""ページをまたいで保持する widget state の補助処理。"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import streamlit as st
from runtime import state

if TYPE_CHECKING:
    from settings import SelectableTagKey


def search_widget_keys(selectable_tag_keys: Sequence[SelectableTagKey]) -> list[str]:
    """検索条件としてページをまたいで保持する widget key を返す。"""
    return [
        state.SEARCH_ASSET_FREEWORD,
        state.SEARCH_ASSET_TARGET_ASSET_NAME,
        state.SEARCH_ASSET_TARGET_ASSET_DESC,
        state.SEARCH_ASSET_TARGET_COLUMN_NAME,
        state.SEARCH_ASSET_TARGET_COLUMN_DESC,
        state.SEARCH_ASSET_DATABASES,
        state.SEARCH_ASSET_SCHEMAS,
        state.SEARCH_ASSET_TYPES,
        state.SEARCH_ASSET_OP_HIERARCHY,
        state.SEARCH_ASSET_OP_TYPE,
        state.SEARCH_ASSET_OP_TAG,
        *[
            state.search_asset_tag_key(
                tag_key["DATABASE_NAME"],
                tag_key["SCHEMA_NAME"],
                tag_key["TAG_NAME"],
            )
            for tag_key in selectable_tag_keys
        ],
        state.SEARCH_USER_FREEWORD,
        state.SEARCH_USER_TARGET_USER_NAME,
        state.SEARCH_USER_TARGET_DISPLAY_NAME,
    ]


def preserve_widget_state(keys: list[str]) -> None:
    """Streamlit の widget cleanup 対象から指定 key を外す。"""
    for key in keys:
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]

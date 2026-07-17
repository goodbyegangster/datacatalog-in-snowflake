"""ページをまたいで保持する widget state の補助処理。"""

from __future__ import annotations

import streamlit as st

from components.assets import search as asset_search
from components.users import search as user_search


def search_widget_keys() -> list[str]:
    """検索条件としてページをまたいで保持する widget key を返す。"""
    return [
        *asset_search.get_preserved_widget_keys(),
        *user_search.get_preserved_widget_keys(),
    ]


def preserve_widget_state(keys: list[str]) -> None:
    """Streamlit の widget cleanup 対象から指定 key を外す。"""
    for key in keys:
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]

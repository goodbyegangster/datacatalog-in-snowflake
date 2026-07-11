"""Streamlit UI 共通ヘルパ。"""

from __future__ import annotations

import streamlit as st

PAGE_SPACING_CSS = """
<style>
[data-testid="stMainBlockContainer"] {
    padding-bottom: 32px;
}
</style>
"""


def render_page_spacing_css() -> None:
    """Streamlit 既定の本文下余白を抑える。"""
    st.markdown(PAGE_SPACING_CSS, unsafe_allow_html=True)

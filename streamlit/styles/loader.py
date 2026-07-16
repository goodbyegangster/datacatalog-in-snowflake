"""CSS file loader for Streamlit pages."""

from __future__ import annotations

from functools import cache
from pathlib import Path

import streamlit as st

_STYLE_DIR = Path(__file__).parent


@cache
def _read_css(name: str) -> str:
    """CSS ファイルを読み込む。"""
    return (_STYLE_DIR / name).read_text(encoding="utf-8")


def _render_css(name: str) -> None:
    """指定 CSS ファイルを Streamlit ページへ適用する。"""
    st.markdown(f"<style>{_read_css(name)}</style>", unsafe_allow_html=True)


def render_base_css() -> None:
    """全ページ共通 CSS を適用する。"""
    _render_css("base.css")


def render_page_css(name: str) -> None:
    """ページ固有 CSS を適用する。"""
    _render_css(name)

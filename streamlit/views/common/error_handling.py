"""View 共通のエラー表示 helper。"""

from __future__ import annotations

import streamlit as st

from catalog import provider as catalog

CATALOG_LOAD_ERROR_MESSAGE = (
    "データの取得に失敗しました。接続設定やカタログテーブルの生成状況をご確認ください。"
)


def render_catalog_load_error(exc: Exception) -> None:
    """カタログロード失敗時のエラーを表示する。"""
    st.error(CATALOG_LOAD_ERROR_MESSAGE)
    if catalog.data_mode() == "fake":
        st.exception(exc)

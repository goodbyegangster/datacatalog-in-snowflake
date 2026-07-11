"""Streamlit の閲覧者ユーザー情報を扱うヘルパ。"""

from __future__ import annotations

import streamlit as st

from lib import catalog

FAKE_CURRENT_USER_NAME = "ALICE"


def current_user_name() -> str | None:
    """Streamlit のログインユーザー名を返す。fake mode では固定ユーザーを返す。"""
    if catalog.data_mode() == "fake":
        return FAKE_CURRENT_USER_NAME

    user = st.user.to_dict()
    for key in ("user_name", "login_name", "name"):
        value = user.get(key)
        if value:
            return str(value).upper()
    return None

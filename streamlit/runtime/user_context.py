"""Streamlit の閲覧者ユーザー情報を扱うヘルパ。"""

from __future__ import annotations

import streamlit as st

from catalog import provider as catalog

FAKE_CURRENT_USER_NAME = "ALICE"


def get_current_user_name() -> str | None:
    """Streamlit のログインユーザー名を返す。fake mode では固定ユーザー名を返す。"""
    if catalog.get_data_mode() == "fake":
        return FAKE_CURRENT_USER_NAME

    user = st.user.to_dict()
    for key in ("user_name", "login_name", "name"):
        value = user.get(key)
        if value:
            return str(value).upper()
    return None

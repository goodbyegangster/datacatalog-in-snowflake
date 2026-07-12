"""ユーザーページの検索 component。"""

from __future__ import annotations

import streamlit as st

import settings
from components.users import results
from logic.search import UserFreewordQuery
from runtime import state, user_context

CURRENT_USER_UNAVAILABLE_MESSAGE = (
    "ログインユーザー名を取得できないため、ログインユーザーのみ表示を適用できません。"
)


def _defaults() -> dict[str, object]:
    """検索ウィジェットの初期値。"""
    return {
        state.SEARCH_USER_ONLY_SELF: settings.IS_VISIBLE_ONLY_SELF_USER,
        state.SEARCH_USER_FREEWORD: "",
        state.SEARCH_USER_TARGET_USER_NAME: True,
        state.SEARCH_USER_TARGET_DISPLAY_NAME: True,
    }


def _init_state() -> None:
    """検索ウィジェットの初期値を session_state に寄せる。"""
    for key, value in _defaults().items():
        st.session_state.setdefault(key, value)
    if settings.IS_VISIBLE_ONLY_SELF_USER:
        st.session_state[state.SEARCH_USER_ONLY_SELF] = True


def _clear() -> None:
    """検索入力を全クリアする。"""
    for key, value in _defaults().items():
        st.session_state[key] = value
    if settings.IS_VISIBLE_ONLY_SELF_USER:
        st.session_state[state.SEARCH_USER_ONLY_SELF] = True
    results.clear_selection()


def fingerprint(freeword: UserFreewordQuery, only_user_name: str | None) -> tuple[object, ...]:
    """現在の検索条件を、変更検知しやすい不変値へ正規化する。"""
    return (
        only_user_name,
        freeword.text.strip(),
        freeword.target_user_name,
        freeword.target_display_name,
    )


def render() -> tuple[UserFreewordQuery, str | None, bool]:
    """sidebar：検索 UI。ウィジェットを描画し、現在の検索条件を返す。"""
    _init_state()
    st.button("入力をクリア", on_click=_clear, width="stretch")

    only_self = st.toggle(
        "ログインユーザーのみ表示",
        key=state.SEARCH_USER_ONLY_SELF,
        disabled=settings.IS_VISIBLE_ONLY_SELF_USER,
        help="Streamlit App にログインしている Snowflake ユーザーのみ表示します",
    )
    if settings.IS_VISIBLE_ONLY_SELF_USER:
        only_self = True
    only_user_name = user_context.current_user_name() if only_self else None

    with st.container(border=True):
        st.markdown("**フリーワード**")
        disabled = only_self
        st.text_input(
            "キーワード",
            key=state.SEARCH_USER_FREEWORD,
            placeholder="名前 / 表示名 で検索",
            label_visibility="collapsed",
            disabled=disabled,
        )
        st.caption("単語間に ` OR ` / ` AND ` を入れると組み合わせ検索ができます")
        cols = st.columns(2)
        with cols[0]:
            st.checkbox(
                "ユーザーの名前",
                key=state.SEARCH_USER_TARGET_USER_NAME,
                disabled=disabled,
            )
        with cols[1]:
            st.checkbox(
                "ユーザーの表示名",
                key=state.SEARCH_USER_TARGET_DISPLAY_NAME,
                disabled=disabled,
            )

    return (
        UserFreewordQuery(
            text="" if disabled else st.session_state.get(state.SEARCH_USER_FREEWORD, ""),
            target_user_name=st.session_state.get(state.SEARCH_USER_TARGET_USER_NAME, True),
            target_display_name=st.session_state.get(state.SEARCH_USER_TARGET_DISPLAY_NAME, True),
        ),
        only_user_name,
        only_self,
    )

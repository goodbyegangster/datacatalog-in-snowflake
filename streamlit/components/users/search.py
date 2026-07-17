"""ユーザーページの検索 component。"""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

import settings
from components.users import results
from logic.search import UserFreewordQuery
from runtime import state, user_context

CURRENT_USER_UNAVAILABLE_MESSAGE = (
    "ログインユーザーのみ表示が有効ですが、現在のログインユーザー名を取得できないため、"
    "ユーザー一覧を表示できません。"
)
FREEWORD_TARGET_KEYS = (
    state.SEARCH_USER_TARGET_USER_NAME,
    state.SEARCH_USER_TARGET_DISPLAY_NAME,
)


@dataclass(frozen=True)
class UserSearchCriteria:
    """ユーザー検索 UI から得た検索条件。"""

    freeword: UserFreewordQuery
    current_user_filter_name: str | None
    is_only_self_filter_enabled: bool


@dataclass(frozen=True)
class OnlySelfFilter:
    """ログインユーザーのみ表示フィルターの状態。"""

    is_enabled: bool
    current_user_filter_name: str | None


@dataclass(frozen=True)
class UserSearchFingerprint:
    """検索条件の変更検知に使う正規化済み値。"""

    current_user_filter_name: str | None
    freeword_text: str
    is_user_name_search_target_enabled: bool
    is_display_name_search_target_enabled: bool


def _build_default_values() -> dict[str, object]:
    """検索ウィジェットの初期値。"""
    return {
        state.SEARCH_USER_ONLY_SELF: settings.IS_VISIBLE_ONLY_SELF_USER,
        state.SEARCH_USER_FREEWORD: "",
        state.SEARCH_USER_TARGET_USER_NAME: True,
        state.SEARCH_USER_TARGET_DISPLAY_NAME: True,
    }


def get_preserved_widget_keys() -> list[str]:
    """ページをまたいで保持する検索 widget key を返す。

    SEARCH_USER_ONLY_SELF は settings.IS_VISIBLE_ONLY_SELF_USER と現在ユーザーに依存するため、
    ページ遷移をまたいで保持しない。
    """
    return [key for key in _build_default_values() if key != state.SEARCH_USER_ONLY_SELF]


def _initialize_state() -> None:
    """検索ウィジェットの初期値を session_state に寄せる。"""
    for key, value in _build_default_values().items():
        st.session_state.setdefault(key, value)
    if settings.IS_VISIBLE_ONLY_SELF_USER:
        st.session_state[state.SEARCH_USER_ONLY_SELF] = True


def _clear_search_inputs() -> None:
    """検索入力を全クリアする。"""
    for key, value in _build_default_values().items():
        st.session_state[key] = value
    if settings.IS_VISIBLE_ONLY_SELF_USER:
        st.session_state[state.SEARCH_USER_ONLY_SELF] = True
    results.clear_user_selection()


def set_all_users_view_for_navigation() -> None:
    """ユーザー指定の遷移時に、フリーワードを消して全ユーザー表示へ戻す。"""
    st.session_state[state.SEARCH_USER_FREEWORD] = ""
    if not settings.IS_VISIBLE_ONLY_SELF_USER:
        st.session_state[state.SEARCH_USER_ONLY_SELF] = False


def _is_freeword_target_disabled() -> bool:
    """フリーワード検索対象の選択が 1 つもないかどうか。"""
    return not any(st.session_state.get(key, True) for key in FREEWORD_TARGET_KEYS)


def build_fingerprint(criteria: UserSearchCriteria) -> UserSearchFingerprint:
    """現在の検索条件を、変更検知しやすい不変値へ正規化する。"""
    return UserSearchFingerprint(
        current_user_filter_name=criteria.current_user_filter_name,
        freeword_text=criteria.freeword.freeword_text.strip(),
        is_user_name_search_target_enabled=criteria.freeword.is_user_name_search_target_enabled,
        is_display_name_search_target_enabled=(
            criteria.freeword.is_display_name_search_target_enabled
        ),
    )


def _render_only_self_toggle() -> OnlySelfFilter:
    """ログインユーザーのみ表示 toggle を描画し、状態と対象ユーザー名を返す。"""
    is_only_self_filter_enabled = st.toggle(
        "ログインユーザーのみ表示",
        key=state.SEARCH_USER_ONLY_SELF,
        disabled=settings.IS_VISIBLE_ONLY_SELF_USER,
        help="Streamlit App にログインしている Snowflake ユーザーのみ表示します",
    )
    if settings.IS_VISIBLE_ONLY_SELF_USER:
        is_only_self_filter_enabled = True
    current_user_filter_name = (
        user_context.current_user_name() if is_only_self_filter_enabled else None
    )
    return OnlySelfFilter(
        is_enabled=is_only_self_filter_enabled,
        current_user_filter_name=current_user_filter_name,
    )


def _render_freeword_target_checkboxes(*, disabled: bool) -> None:
    """フリーワード検索対象 checkbox を描画する。"""
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


def _render_freeword_controls(*, is_only_self_filter_enabled: bool) -> UserFreewordQuery:
    """フリーワード入力と検索対象 checkbox を描画し、検索条件を返す。"""
    is_target_checkbox_disabled = is_only_self_filter_enabled
    is_freeword_input_disabled = is_only_self_filter_enabled or _is_freeword_target_disabled()
    if is_freeword_input_disabled:
        st.session_state[state.SEARCH_USER_FREEWORD] = ""

    st.text_input(
        "キーワード",
        key=state.SEARCH_USER_FREEWORD,
        placeholder="名前 / 表示名 で検索",
        label_visibility="collapsed",
        disabled=is_freeword_input_disabled,
    )
    st.caption("単語間に ` OR ` / ` AND ` を入れると組み合わせ検索ができます")
    _render_freeword_target_checkboxes(disabled=is_target_checkbox_disabled)

    return UserFreewordQuery(
        freeword_text=st.session_state.get(state.SEARCH_USER_FREEWORD, ""),
        is_user_name_search_target_enabled=st.session_state.get(
            state.SEARCH_USER_TARGET_USER_NAME,
            True,
        ),
        is_display_name_search_target_enabled=st.session_state.get(
            state.SEARCH_USER_TARGET_DISPLAY_NAME,
            True,
        ),
    )


def render() -> UserSearchCriteria:
    """sidebar：検索 UI。ウィジェットを描画し、現在の検索条件を返す。"""
    _initialize_state()
    st.button("入力をクリア", on_click=_clear_search_inputs, width="stretch")

    only_self_filter = _render_only_self_toggle()

    with st.container(border=True):
        st.markdown("**フリーワード**")
        freeword = _render_freeword_controls(
            is_only_self_filter_enabled=only_self_filter.is_enabled
        )

    return UserSearchCriteria(
        freeword=freeword,
        current_user_filter_name=only_self_filter.current_user_filter_name,
        is_only_self_filter_enabled=only_self_filter.is_enabled,
    )

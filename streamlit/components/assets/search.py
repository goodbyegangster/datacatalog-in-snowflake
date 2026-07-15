"""データ資産ページの検索 component。"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import streamlit as st

from catalog import schema
from components.assets import results
from logic import search
from logic.search import AssetSearchCriteria, FreewordQuery, TagSelection
from runtime import state
from settings import SELECTABLE_TAG_KEYS

if TYPE_CHECKING:
    from settings import SelectableTagKey

FREEWORD_TARGET_KEYS = (
    state.SEARCH_ASSET_TARGET_ASSET_NAME,
    state.SEARCH_ASSET_TARGET_ASSET_DESC,
    state.SEARCH_ASSET_TARGET_COLUMN_NAME,
    state.SEARCH_ASSET_TARGET_COLUMN_DESC,
)


def _defaults() -> dict[str, object]:
    """検索ウィジェットの初期値。"""
    return {
        state.SEARCH_ASSET_FREEWORD: "",
        state.SEARCH_ASSET_TARGET_ASSET_NAME: True,
        state.SEARCH_ASSET_TARGET_ASSET_DESC: True,
        state.SEARCH_ASSET_TARGET_COLUMN_NAME: True,
        state.SEARCH_ASSET_TARGET_COLUMN_DESC: True,
        state.SEARCH_ASSET_DATABASES: [],
        state.SEARCH_ASSET_SCHEMAS: [],
        state.SEARCH_ASSET_TYPES: [],
        state.SEARCH_ASSET_OP_HIERARCHY: "AND",
        state.SEARCH_ASSET_OP_TYPE: "AND",
        state.SEARCH_ASSET_OP_TAG: "AND",
    }


def _tag_allowed_values(tags: pd.DataFrame, tag_key: SelectableTagKey) -> list[str]:
    """TAGS マスターから、指定タグの allowed_values を取得する。"""
    T = schema.Tags
    mask = (
        (tags[T.TAG_DATABASE] == tag_key["DATABASE_NAME"])
        & (tags[T.TAG_SCHEMA] == tag_key["SCHEMA_NAME"])
        & (tags[T.TAG_NAME] == tag_key["TAG_NAME"])
    )
    values = tags.loc[mask, str(T.TAG_VALUE)].dropna().astype(str).tolist()
    return sorted(values)


def _tag_comment(tags: pd.DataFrame, tag_key: SelectableTagKey) -> str | None:
    """TAGS マスターから、指定タグのコメントを取得する。"""
    T = schema.Tags
    mask = (
        (tags[T.TAG_DATABASE] == tag_key["DATABASE_NAME"])
        & (tags[T.TAG_SCHEMA] == tag_key["SCHEMA_NAME"])
        & (tags[T.TAG_NAME] == tag_key["TAG_NAME"])
    )
    comments = [
        str(value).strip()
        for value in tags.loc[mask, str(T.TAG_COMMENT)].dropna().unique().tolist()
        if str(value).strip()
    ]
    if not comments:
        return None
    return "\n\n".join(sorted(comments))


def _tag_widget_key(tag_key: SelectableTagKey) -> str:
    return state.search_asset_tag_key(
        tag_key["DATABASE_NAME"], tag_key["SCHEMA_NAME"], tag_key["TAG_NAME"]
    )


def _init_state() -> None:
    """検索ウィジェットの初期値を session_state に寄せる。"""
    for key, value in _defaults().items():
        st.session_state.setdefault(key, value)
    for tag_key in SELECTABLE_TAG_KEYS:
        st.session_state.setdefault(_tag_widget_key(tag_key), [])


def _on_database_change() -> None:
    """DB 選択変更時、（親に依存する）スキーマ選択を未選択へリセットする。"""
    st.session_state[state.SEARCH_ASSET_SCHEMAS] = []


def _clear() -> None:
    """検索入力を全クリアする。"""
    for key, value in _defaults().items():
        st.session_state[key] = value
    for tag_key in SELECTABLE_TAG_KEYS:
        st.session_state[_tag_widget_key(tag_key)] = []
    results.clear_selection()


def _freeword_disabled() -> bool:
    """フリーワード検索対象が 1 つも選択されていないか。"""
    return not any(st.session_state.get(key, True) for key in FREEWORD_TARGET_KEYS)


def _render_combine_control(key: str) -> None:
    """カテゴリ間の結合（AND=必須 / OR=いずれか）を選ぶセグメントコントロール。"""
    st.segmented_control(
        "その他検索との結合条件",
        ["AND", "OR"],
        key=key,
    )


def _op_is_or(key: str) -> bool:
    return st.session_state.get(key) == "OR"


def has_condition(criteria: AssetSearchCriteria) -> bool:
    """いずれかの検索条件が入力/選択されているか（初期空欄判定に用いる）。"""
    return bool(
        criteria.freeword.text.strip()
        or criteria.selected_databases
        or criteria.selected_schemas
        or criteria.selected_types
        or any(t.selected for t in criteria.tag_selections)
    )


def fingerprint(criteria: AssetSearchCriteria) -> tuple[object, ...]:
    """現在の検索条件を、変更検知しやすい不変値へ正規化する。"""
    tags = tuple(
        (
            tag.tag_database,
            tag.tag_schema,
            tag.tag_name,
            tuple(sorted(tag.selected)),
        )
        for tag in criteria.tag_selections
        if tag.selected
    )
    return (
        criteria.freeword.text.strip(),
        criteria.freeword.target_asset_name,
        criteria.freeword.target_asset_desc,
        criteria.freeword.target_column_name,
        criteria.freeword.target_column_desc,
        tuple(sorted(criteria.selected_databases)),
        tuple(sorted(criteria.selected_schemas)),
        tuple(sorted(criteria.selected_types)),
        tags,
        criteria.hierarchy_or,
        criteria.type_or,
        criteria.tag_or,
    )


def render(assets: pd.DataFrame, tags: pd.DataFrame) -> AssetSearchCriteria:
    """sidebar：検索 UI。ウィジェットを描画し、現在の検索条件を返す。"""
    _init_state()
    st.button("入力をクリア", on_click=_clear, width="stretch")

    with st.container(border=True):
        st.markdown("**フリーワード**")
        freeword_disabled = _freeword_disabled()
        if freeword_disabled:
            st.session_state[state.SEARCH_ASSET_FREEWORD] = ""
        st.text_input(
            "キーワード",
            key=state.SEARCH_ASSET_FREEWORD,
            placeholder="名前 / 説明 で検索",
            label_visibility="collapsed",
            disabled=freeword_disabled,
        )
        st.caption("単語間に ` OR ` / ` AND ` を入れると組み合わせ検索ができます")
        cols = st.columns(2)
        with cols[0]:
            st.checkbox("オブジェクトの名前", key=state.SEARCH_ASSET_TARGET_ASSET_NAME)
            st.checkbox("カラムの名前", key=state.SEARCH_ASSET_TARGET_COLUMN_NAME)
        with cols[1]:
            st.checkbox("オブジェクトの説明", key=state.SEARCH_ASSET_TARGET_ASSET_DESC)
            st.checkbox("カラムの説明", key=state.SEARCH_ASSET_TARGET_COLUMN_DESC)

    dbs_now = st.session_state.get(state.SEARCH_ASSET_DATABASES, [])
    schemas_now = st.session_state.get(state.SEARCH_ASSET_SCHEMAS, [])
    with st.expander("データベース / スキーマ", expanded=bool(dbs_now or schemas_now)):
        _render_combine_control(state.SEARCH_ASSET_OP_HIERARCHY)
        st.multiselect(
            "データベース",
            search.scope_databases(assets),
            key=state.SEARCH_ASSET_DATABASES,
            on_change=_on_database_change,
        )
        selected_dbs = st.session_state.get(state.SEARCH_ASSET_DATABASES, [])
        st.multiselect(
            "スキーマ",
            search.scope_schemas(assets, selected_dbs),
            key=state.SEARCH_ASSET_SCHEMAS,
            help="データベースを選択すると候補が表示されます",
        )

    types_now = st.session_state.get(state.SEARCH_ASSET_TYPES, [])
    with st.expander("オブジェクト種別", expanded=bool(types_now)):
        _render_combine_control(state.SEARCH_ASSET_OP_TYPE)
        type_options = sorted(assets[schema.Assets.ASSET_TYPE].dropna().unique().tolist())
        st.multiselect(
            "種別",
            type_options,
            key=state.SEARCH_ASSET_TYPES,
            label_visibility="collapsed",
        )

    tag_selections: list[TagSelection] = []
    tag_widget_keys = [_tag_widget_key(t) for t in SELECTABLE_TAG_KEYS]
    any_tag = any(st.session_state.get(k, []) for k in tag_widget_keys)
    with st.expander("タグ", expanded=any_tag):
        _render_combine_control(state.SEARCH_ASSET_OP_TAG)
        for tag_key, widget_key in zip(SELECTABLE_TAG_KEYS, tag_widget_keys, strict=True):
            allowed = _tag_allowed_values(tags, tag_key)
            st.markdown(f"**{tag_key['TAG_NAME']}**")
            if comment := _tag_comment(tags, tag_key):
                st.caption(comment)
            st.multiselect(
                tag_key["TAG_NAME"],
                allowed,
                key=widget_key,
                label_visibility="collapsed",
            )
            tag_selections.append(
                TagSelection(
                    tag_database=tag_key["DATABASE_NAME"],
                    tag_schema=tag_key["SCHEMA_NAME"],
                    tag_name=tag_key["TAG_NAME"],
                    selected=st.session_state.get(widget_key, []),
                    allowed=allowed,
                )
            )

    return AssetSearchCriteria(
        freeword=FreewordQuery(
            text=st.session_state.get(state.SEARCH_ASSET_FREEWORD, ""),
            target_asset_name=st.session_state.get(state.SEARCH_ASSET_TARGET_ASSET_NAME, True),
            target_asset_desc=st.session_state.get(state.SEARCH_ASSET_TARGET_ASSET_DESC, True),
            target_column_name=st.session_state.get(state.SEARCH_ASSET_TARGET_COLUMN_NAME, True),
            target_column_desc=st.session_state.get(state.SEARCH_ASSET_TARGET_COLUMN_DESC, True),
        ),
        selected_databases=st.session_state.get(state.SEARCH_ASSET_DATABASES, []),
        selected_schemas=st.session_state.get(state.SEARCH_ASSET_SCHEMAS, []),
        selected_types=st.session_state.get(state.SEARCH_ASSET_TYPES, []),
        tag_selections=tag_selections,
        hierarchy_or=_op_is_or(state.SEARCH_ASSET_OP_HIERARCHY),
        type_or=_op_is_or(state.SEARCH_ASSET_OP_TYPE),
        tag_or=_op_is_or(state.SEARCH_ASSET_OP_TAG),
    )

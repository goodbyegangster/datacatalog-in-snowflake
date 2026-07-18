"""データ資産ページの検索 component。"""

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class TagSearchFingerprint:
    """タグ検索条件の変更検知に使う正規化済み値。"""

    tag_database: str
    tag_schema: str
    tag_name: str
    selected: tuple[str, ...]


@dataclass(frozen=True)
class AssetSearchFingerprint:
    """検索条件の変更検知に使う正規化済み値。"""

    freeword_text: str
    is_asset_name_search_target_enabled: bool
    is_asset_description_search_target_enabled: bool
    is_column_name_search_target_enabled: bool
    is_column_description_search_target_enabled: bool
    selected_databases: tuple[str, ...]
    selected_schemas: tuple[str, ...]
    selected_types: tuple[str, ...]
    tag_selections: tuple[TagSearchFingerprint, ...]
    is_hierarchy_or_enabled: bool
    is_type_or_enabled: bool
    is_tag_or_enabled: bool


@dataclass(frozen=True)
class _TagMasterMetadata:
    """TAGS マスターから取得したタグ検索 UI 用の値。"""

    value_options: list[str]
    comment: str | None


@dataclass(frozen=True)
class TagSearchMetadata:
    """タグ検索 UI の描画と検索条件生成に使う値。"""

    tag_database: str
    tag_schema: str
    tag_name: str
    widget_key: str
    value_options: list[str]
    comment: str | None


def _build_default_values() -> dict[str, object]:
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


def _build_tag_master_metadata_by_key(
    tags: pd.DataFrame,
) -> dict[tuple[str, str, str], _TagMasterMetadata]:
    """TAGS マスターをタグキーごとの UI 用 metadata にまとめる。"""
    tags_schema = schema.Tags
    values_by_key: dict[tuple[str, str, str], set[str]] = {}
    comments_by_key: dict[tuple[str, str, str], set[str]] = {}

    for tag_database, tag_schema, tag_name, tag_value, tag_comment in tags[
        [
            tags_schema.TAG_DATABASE,
            tags_schema.TAG_SCHEMA,
            tags_schema.TAG_NAME,
            tags_schema.TAG_VALUE,
            tags_schema.TAG_COMMENT,
        ]
    ].itertuples(index=False, name=None):
        key = (str(tag_database), str(tag_schema), str(tag_name))
        if pd.notna(tag_value):
            values_by_key.setdefault(key, set()).add(str(tag_value))
        if pd.notna(tag_comment) and (comment := str(tag_comment).strip()):
            comments_by_key.setdefault(key, set()).add(comment)

    return {
        key: _TagMasterMetadata(
            value_options=sorted(values),
            comment="\n\n".join(sorted(comments_by_key.get(key, set()))) or None,
        )
        for key, values in values_by_key.items()
    }


def _build_tag_search_metadata(tags: pd.DataFrame) -> list[TagSearchMetadata]:
    """検索対象タグごとの UI 用 metadata を組み立てる。"""
    metadata_by_key = _build_tag_master_metadata_by_key(tags)
    return [
        _build_tag_search_metadata_item(tag_key, metadata_by_key)
        for tag_key in SELECTABLE_TAG_KEYS
    ]


def _build_tag_search_metadata_item(
    tag_key: SelectableTagKey,
    metadata_by_key: dict[tuple[str, str, str], _TagMasterMetadata],
) -> TagSearchMetadata:
    """検索対象タグ 1 件分の UI 用 metadata を組み立てる。"""
    key = (
        tag_key["DATABASE_NAME"],
        tag_key["SCHEMA_NAME"],
        tag_key["TAG_NAME"],
    )
    metadata = metadata_by_key.get(key, _TagMasterMetadata(value_options=[], comment=None))
    return TagSearchMetadata(
        tag_database=tag_key["DATABASE_NAME"],
        tag_schema=tag_key["SCHEMA_NAME"],
        tag_name=tag_key["TAG_NAME"],
        widget_key=_build_tag_widget_key(tag_key),
        value_options=metadata.value_options,
        comment=metadata.comment,
    )


def _build_tag_selection(tag_metadata: TagSearchMetadata) -> TagSelection:
    """現在の session_state からタグ検索条件を組み立てる。"""
    return TagSelection(
        tag_database=tag_metadata.tag_database,
        tag_schema=tag_metadata.tag_schema,
        tag_name=tag_metadata.tag_name,
        selected=st.session_state.get(tag_metadata.widget_key, []),
        tag_value_options=tag_metadata.value_options,
    )


def _build_tag_widget_key(tag_key: SelectableTagKey) -> str:
    """指定タグの検索 widget key を組み立てる。"""
    return state.search_asset_tag_key(
        tag_key["DATABASE_NAME"], tag_key["SCHEMA_NAME"], tag_key["TAG_NAME"]
    )


def get_preserved_widget_keys() -> list[str]:
    """ページをまたいで保持する検索 widget key を返す。"""
    return [
        *list(_build_default_values()),
        *[_build_tag_widget_key(tag_key) for tag_key in SELECTABLE_TAG_KEYS],
    ]


def _initialize_state() -> None:
    """検索ウィジェットの初期値を session_state に寄せる。"""
    for key, value in _build_default_values().items():
        st.session_state.setdefault(key, value)
    for tag_key in SELECTABLE_TAG_KEYS:
        st.session_state.setdefault(_build_tag_widget_key(tag_key), [])


def _reset_schemas_on_database_change() -> None:
    """DB 選択変更時、（親に依存する）スキーマ選択を未選択へリセットする。"""
    st.session_state[state.SEARCH_ASSET_SCHEMAS] = []


def _clear_search_inputs() -> None:
    """検索入力を全クリアする。"""
    for key, value in _build_default_values().items():
        st.session_state[key] = value
    for tag_key in SELECTABLE_TAG_KEYS:
        st.session_state[_build_tag_widget_key(tag_key)] = []
    results.clear_asset_selection()


def _is_freeword_input_disabled() -> bool:
    """フリーワード検索対象が 1 つも選択されていないかどうか。"""
    return not any(st.session_state.get(key, True) for key in FREEWORD_TARGET_KEYS)


def _render_combine_control(key: str) -> None:
    """カテゴリ間の結合（AND=必須 / OR=いずれか）を選ぶセグメントコントロール。"""
    st.segmented_control(
        "その他検索との結合条件",
        ["AND", "OR"],
        key=key,
    )


def _is_or_operator_enabled(key: str) -> bool:
    """指定された結合条件 widget が OR かどうかを返す。"""
    return st.session_state.get(key) == "OR"


def has_search_condition(criteria: AssetSearchCriteria) -> bool:
    """いずれかの検索条件が入力/選択されているか（初期空欄判定に用いる）。"""
    return bool(
        criteria.freeword.text.strip()
        or criteria.selected_databases
        or criteria.selected_schemas
        or criteria.selected_types
        or any(t.selected for t in criteria.tag_selections)
    )


def build_fingerprint(criteria: AssetSearchCriteria) -> AssetSearchFingerprint:
    """現在の検索条件を、変更検知しやすい不変値へ正規化する。"""
    tags = tuple(
        TagSearchFingerprint(
            tag_database=tag.tag_database,
            tag_schema=tag.tag_schema,
            tag_name=tag.tag_name,
            selected=tuple(sorted(tag.selected)),
        )
        for tag in criteria.tag_selections
        if tag.selected
    )
    return AssetSearchFingerprint(
        freeword_text=criteria.freeword.text.strip(),
        is_asset_name_search_target_enabled=criteria.freeword.target_asset_name,
        is_asset_description_search_target_enabled=criteria.freeword.target_asset_desc,
        is_column_name_search_target_enabled=criteria.freeword.target_column_name,
        is_column_description_search_target_enabled=criteria.freeword.target_column_desc,
        selected_databases=tuple(sorted(criteria.selected_databases)),
        selected_schemas=tuple(sorted(criteria.selected_schemas)),
        selected_types=tuple(sorted(criteria.selected_types)),
        tag_selections=tags,
        is_hierarchy_or_enabled=criteria.is_hierarchy_or_enabled,
        is_type_or_enabled=criteria.is_type_or_enabled,
        is_tag_or_enabled=criteria.is_tag_or_enabled,
    )


def render(assets: pd.DataFrame, tags: pd.DataFrame) -> AssetSearchCriteria:
    """sidebar：検索 UI。ウィジェットを描画し、現在の検索条件を返す。"""
    _initialize_state()
    st.button("入力をクリア", on_click=_clear_search_inputs, width="stretch")

    with st.container(border=True):
        st.markdown("**フリーワード**")
        is_freeword_input_disabled = _is_freeword_input_disabled()
        if is_freeword_input_disabled:
            st.session_state[state.SEARCH_ASSET_FREEWORD] = ""
        st.text_input(
            "キーワード",
            key=state.SEARCH_ASSET_FREEWORD,
            placeholder="名前 / 説明 で検索",
            label_visibility="collapsed",
            disabled=is_freeword_input_disabled,
        )
        st.caption("単語間に ` OR ` / ` AND ` を入れると組み合わせ検索ができます")
        cols = st.columns(2)
        with cols[0]:
            st.checkbox("オブジェクトの名前", key=state.SEARCH_ASSET_TARGET_ASSET_NAME)
            st.checkbox("カラムの名前", key=state.SEARCH_ASSET_TARGET_COLUMN_NAME)
        with cols[1]:
            st.checkbox("オブジェクトの説明", key=state.SEARCH_ASSET_TARGET_ASSET_DESC)
            st.checkbox("カラムの説明", key=state.SEARCH_ASSET_TARGET_COLUMN_DESC)

    selected_database_names = st.session_state.get(state.SEARCH_ASSET_DATABASES, [])
    selected_schema_names = st.session_state.get(state.SEARCH_ASSET_SCHEMAS, [])
    with st.expander(
        "データベース / スキーマ",
        expanded=bool(selected_database_names or selected_schema_names),
    ):
        _render_combine_control(state.SEARCH_ASSET_OP_HIERARCHY)
        st.multiselect(
            "データベース",
            search.get_scope_database_names(assets),
            key=state.SEARCH_ASSET_DATABASES,
            on_change=_reset_schemas_on_database_change,
        )
        selected_database_names = st.session_state.get(state.SEARCH_ASSET_DATABASES, [])
        st.multiselect(
            "スキーマ",
            search.get_scope_schema_names(assets, selected_database_names),
            key=state.SEARCH_ASSET_SCHEMAS,
            help="データベースを選択すると候補が表示されます",
        )

    selected_asset_types = st.session_state.get(state.SEARCH_ASSET_TYPES, [])
    with st.expander("オブジェクト種別", expanded=bool(selected_asset_types)):
        _render_combine_control(state.SEARCH_ASSET_OP_TYPE)
        type_options = sorted(assets[schema.Assets.ASSET_TYPE].dropna().unique().tolist())
        st.multiselect(
            "種別",
            type_options,
            key=state.SEARCH_ASSET_TYPES,
            label_visibility="collapsed",
        )

    tag_metadata_list = _build_tag_search_metadata(tags)
    tag_widget_keys = [tag_metadata.widget_key for tag_metadata in tag_metadata_list]
    has_selected_tag_values = any(st.session_state.get(k, []) for k in tag_widget_keys)
    with st.expander("タグ", expanded=has_selected_tag_values):
        _render_combine_control(state.SEARCH_ASSET_OP_TAG)
        for tag_metadata in tag_metadata_list:
            st.markdown(f"**{tag_metadata.tag_name}**")
            if tag_metadata.comment:
                st.caption(tag_metadata.comment)
            st.multiselect(
                tag_metadata.tag_name,
                tag_metadata.value_options,
                key=tag_metadata.widget_key,
                label_visibility="collapsed",
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
        tag_selections=[
            _build_tag_selection(tag_metadata) for tag_metadata in tag_metadata_list
        ],
        is_hierarchy_or_enabled=_is_or_operator_enabled(state.SEARCH_ASSET_OP_HIERARCHY),
        is_type_or_enabled=_is_or_operator_enabled(state.SEARCH_ASSET_OP_TYPE),
        is_tag_or_enabled=_is_or_operator_enabled(state.SEARCH_ASSET_OP_TAG),
    )

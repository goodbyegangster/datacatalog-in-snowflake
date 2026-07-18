"""データ資産のタグ検索ロジック。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from catalog import schema


@dataclass
class TagSelection:
    """タグキー 1 件分の検索条件。``selected`` が空なら絞り込まない。"""

    tag_database: str
    tag_schema: str
    tag_name: str
    selected: list[str]
    tag_value_options: list[str]  # UI の選択肢。フィルタ判定には用いない。

    @property
    def is_unconstrained(self) -> bool:
        """タグ値が選択されていないか。"""
        return not self.selected


def _build_selected_tag_value_matcher(
    sel: TagSelection, wanted: set[str]
) -> Callable[[object], bool]:
    """タグ参照リストが選択されたタグキー・タグ値を含むか判定する関数を返す。"""

    def matches(tags: object) -> bool:
        if not isinstance(tags, list):
            return False
        return any(
            t.get("TAG_DATABASE") == sel.tag_database
            and t.get("TAG_SCHEMA") == sel.tag_schema
            and t.get("TAG_NAME") == sel.tag_name
            and t.get("TAG_VALUE") in wanted
            for t in tags
        )

    return matches


def _get_asset_ids_matching_asset_tags(
    assets: pd.DataFrame,
    matches: Callable[[object], bool],
) -> set[int]:
    """資産自身に付いたタグが検索条件に一致する TABLE_ID を返す。"""
    assets_schema = schema.Assets
    return set(assets.loc[assets[assets_schema.TAGS].map(matches), assets_schema.TABLE_ID])


def _get_asset_ids_matching_column_tags(
    columns: pd.DataFrame,
    matches: Callable[[object], bool],
) -> set[int]:
    """カラムに付いたタグが検索条件に一致する資産の TABLE_ID を返す。"""
    if columns.empty:
        return set()

    columns_schema = schema.Columns
    column_tag_matches = columns[columns_schema.TAGS].map(matches)
    return set(columns.loc[column_tag_matches, columns_schema.TABLE_ID])


def build_tag_mask(
    *, assets: pd.DataFrame, columns: pd.DataFrame, selections: list[TagSelection]
) -> pd.Series:
    """タグ検索条件に一致するデータ資産のマスクを組み立てる。

    各タグ条件について、資産自身のタグとカラムに付いたタグのどちらかが一致した資産を残す。
    複数のタグ条件がある場合は、全てのタグ条件に一致する資産だけを残す。
    """
    assets_schema = schema.Assets
    mask = pd.Series(data=True, index=assets.index)
    for sel in selections:
        if sel.is_unconstrained:
            continue
        matches = _build_selected_tag_value_matcher(sel, set(sel.selected))
        asset_tag_matched_ids = _get_asset_ids_matching_asset_tags(assets, matches)
        column_tag_matched_ids = _get_asset_ids_matching_column_tags(columns, matches)
        tag_matched_asset_ids = asset_tag_matched_ids | column_tag_matched_ids
        mask &= assets[assets_schema.TABLE_ID].isin(tag_matched_asset_ids)
    return mask

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


def _build_tag_value_matcher(sel: TagSelection, wanted: set[str]) -> Callable[[object], bool]:
    """タグ参照リストが選択タグ値を含むか判定する関数を返す。"""

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


def build_tag_mask(
    *, assets: pd.DataFrame, columns: pd.DataFrame, selections: list[TagSelection]
) -> pd.Series:
    """タグ検索条件に一致するデータ資産のマスクを組み立てる。

    資産自身のタグだけでなく、その資産のカラムに付いたタグも対象に含める。
    """
    assets_schema = schema.Assets
    mask = pd.Series(data=True, index=assets.index)
    for sel in selections:
        if sel.is_unconstrained:
            continue
        matches = _build_tag_value_matcher(sel, set(sel.selected))
        matched_ids = set(
            assets.loc[assets[assets_schema.TAGS].map(matches), assets_schema.TABLE_ID]
        )
        if not columns.empty:
            col_hit = columns[schema.Columns.TAGS].map(matches)
            matched_ids |= set(columns.loc[col_hit, schema.Columns.TABLE_ID])
        mask &= assets[assets_schema.TABLE_ID].isin(matched_ids)
    return mask

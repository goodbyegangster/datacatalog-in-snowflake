"""データ資産検索の純ロジック。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import pandas as pd

from catalog import schema
from logic.search.common import parse_freeword
from settings import DISPLAY_SCOPES


@dataclass
class FreewordQuery:
    """フリーワードと検索対象（4 種のチェックボックス。既定は全対象）。"""

    text: str = ""
    target_asset_name: bool = True
    target_asset_desc: bool = True
    target_column_name: bool = True
    target_column_desc: bool = True


def _ids_matching_token(
    token: str, assets: pd.DataFrame, columns: pd.DataFrame, fq: FreewordQuery
) -> set[int]:
    """1 トークンにヒットするデータ資産の TABLE_ID 集合。

    カラム名 / 説明にヒットした場合は、その所属データ資産を対象に含める。
    """
    A = schema.Assets
    C = schema.Columns
    needle = token.lower()
    ids: set[int] = set()

    def contains(series: pd.Series) -> pd.Series:
        return series.fillna("").str.lower().str.contains(needle, regex=False)

    if fq.target_asset_name:
        ids |= set(assets.loc[contains(assets[A.ASSET_NAME]), A.TABLE_ID])
    if fq.target_asset_desc:
        ids |= set(assets.loc[contains(assets[A.DESCRIPTION]), A.TABLE_ID])
    if fq.target_column_name:
        ids |= set(columns.loc[contains(columns[C.COLUMN_NAME]), C.TABLE_ID])
    if fq.target_column_desc:
        ids |= set(columns.loc[contains(columns[C.DESCRIPTION]), C.TABLE_ID])
    return ids


def freeword_asset_ids(
    fq: FreewordQuery, assets: pd.DataFrame, columns: pd.DataFrame
) -> set[int] | None:
    """フリーワードにマッチする TABLE_ID 集合。無制約（空入力）なら None。"""
    op, tokens = parse_freeword(fq.text)
    if not tokens:
        return None
    per_token = [_ids_matching_token(t, assets, columns, fq) for t in tokens]
    if op == "or":
        return set().union(*per_token)
    result = per_token[0]
    for s in per_token[1:]:
        result &= s
    return result


@dataclass
class TagSelection:
    """1 タグキーの選択状態。``selected`` が空なら無制約（絞り込まない）。"""

    tag_database: str
    tag_schema: str
    tag_name: str
    selected: list[str]
    allowed: list[str]  # UI の選択肢（allowed_values）。フィルタ判定には用いない。

    @property
    def is_unconstrained(self) -> bool:
        return not self.selected


@dataclass
class AssetSearchCriteria:
    """データ資産検索の条件一式。

    ``*_or`` は検索条件グループ間の結合指定。False = AND（必須・初期）、True = OR（いずれか）。
    """

    freeword: FreewordQuery = field(default_factory=FreewordQuery)
    selected_databases: list[str] = field(default_factory=list)
    selected_schemas: list[str] = field(default_factory=list)
    selected_types: list[str] = field(default_factory=list)
    tag_selections: list[TagSelection] = field(default_factory=list)
    hierarchy_or: bool = False
    type_or: bool = False
    tag_or: bool = False


def _tag_value_matcher(sel: TagSelection, wanted: set[str]) -> Callable[[object], bool]:
    """タグ列（object の list）が、指定タグの選択値のいずれかを含むか判定する関数を返す。"""

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


def _tag_mask(
    assets: pd.DataFrame, columns: pd.DataFrame, selections: list[TagSelection]
) -> pd.Series:
    """タグ絞り込みのブールマスク。未選択のタグは無制約として無視。

    タグは資産（テーブル / ビュー）自身だけでなく、**その資産のいずれかのカラム**に
    付与されている場合もヒットとみなす（例: PII はカラムに付くことが多い）。
    """
    A = schema.Assets
    mask = pd.Series(data=True, index=assets.index)
    for sel in selections:
        if sel.is_unconstrained:
            continue
        matches = _tag_value_matcher(sel, set(sel.selected))
        matched_ids = set(assets.loc[assets[A.TAGS].map(matches), A.TABLE_ID])
        if not columns.empty:
            col_hit = columns[schema.Columns.TAGS].map(matches)
            matched_ids |= set(columns.loc[col_hit, schema.Columns.TABLE_ID])
        mask &= assets[A.TABLE_ID].isin(matched_ids)
    return mask


def filter_assets(
    assets: pd.DataFrame, columns: pd.DataFrame, criteria: AssetSearchCriteria
) -> pd.DataFrame:
    """design-search の「page：データ資産」に従いデータ資産を絞り込む（バケット方式）。

    ``①フリーワード AND （AND 群を全て満たす） AND （OR 群のいずれかを満たす）``。
    未選択（無制約）の検索条件グループは AND / OR いずれの群にも入れない。
    """
    A = schema.Assets
    all_pass = pd.Series(True, index=assets.index)

    fw_ids = freeword_asset_ids(criteria.freeword, assets, columns)
    freeword_mask = all_pass if fw_ids is None else assets[A.TABLE_ID].isin(fw_ids)

    hierarchy_active = bool(criteria.selected_databases or criteria.selected_schemas)
    db_ok = (
        all_pass
        if not criteria.selected_databases
        else assets[A.DATABASE_NAME].isin(criteria.selected_databases)
    )
    schema_ok = (
        all_pass
        if not criteria.selected_schemas
        else assets[A.SCHEMA_NAME].isin(criteria.selected_schemas)
    )
    hierarchy_mask = db_ok & schema_ok

    type_active = bool(criteria.selected_types)
    asset_type_mask = assets[A.ASSET_TYPE].isin(criteria.selected_types) if type_active else all_pass

    tag_active = any(t.selected for t in criteria.tag_selections)
    tag_mask = _tag_mask(assets, columns, criteria.tag_selections)

    and_masks: list[pd.Series] = []
    or_masks: list[pd.Series] = []
    for active, mask, is_or in (
        (hierarchy_active, hierarchy_mask, criteria.hierarchy_or),
        (type_active, asset_type_mask, criteria.type_or),
        (tag_active, tag_mask, criteria.tag_or),
    ):
        if not active:
            continue
        (or_masks if is_or else and_masks).append(mask)

    group_and = all_pass.copy()
    for mask in and_masks:
        group_and &= mask
    if or_masks:
        group_or = pd.Series(False, index=assets.index)
        for mask in or_masks:
            group_or |= mask
    else:
        group_or = all_pass

    return assets[freeword_mask & group_and & group_or]


def scope_databases() -> list[str]:
    """DISPLAY_SCOPES に定義されたデータベース名（重複排除・定義順）。"""
    seen: list[str] = []
    for s in DISPLAY_SCOPES:
        if s["DATABASE_NAME"] not in seen:
            seen.append(s["DATABASE_NAME"])
    return seen


def scope_schemas(databases: list[str]) -> list[str]:
    """指定データベースに属するスキーマ名（DISPLAY_SCOPES 由来・重複排除・定義順）。"""
    seen: list[str] = []
    for s in DISPLAY_SCOPES:
        if s["DATABASE_NAME"] in databases and s["SCHEMA_NAME"] not in seen:
            seen.append(s["SCHEMA_NAME"])
    return seen

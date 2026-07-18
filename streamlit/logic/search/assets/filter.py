"""データ資産検索条件を合成する純ロジック。"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from catalog import schema
from logic.search.assets.freeword import FreewordQuery, get_freeword_asset_ids
from logic.search.assets.tags import TagSelection, build_tag_mask


@dataclass
class AssetSearchCriteria:
    """データ資産検索の条件一式。

    ``is_*_or_enabled`` は検索条件グループを OR 群として扱うかどうかを表す。
    """

    freeword: FreewordQuery = field(default_factory=FreewordQuery)
    selected_databases: list[str] = field(default_factory=list)
    selected_schemas: list[str] = field(default_factory=list)
    selected_types: list[str] = field(default_factory=list)
    tag_selections: list[TagSelection] = field(default_factory=list)
    is_hierarchy_or_enabled: bool = False
    is_type_or_enabled: bool = False
    is_tag_or_enabled: bool = False


def filter_assets(
    assets: pd.DataFrame, columns: pd.DataFrame, criteria: AssetSearchCriteria
) -> pd.DataFrame:
    """データ資産検索条件に一致する行だけを返す。

    フリーワード条件に加え、AND 群は全て満たし、OR 群はいずれかを満たす行を残す。
    未選択の検索条件グループは AND / OR いずれの群にも入れない。
    """
    assets_schema = schema.Assets
    all_pass = pd.Series(data=True, index=assets.index)

    fw_ids = get_freeword_asset_ids(criteria.freeword, assets, columns)
    freeword_mask = all_pass if fw_ids is None else assets[assets_schema.TABLE_ID].isin(fw_ids)

    hierarchy_active = bool(criteria.selected_databases or criteria.selected_schemas)
    db_ok = (
        all_pass
        if not criteria.selected_databases
        else assets[assets_schema.DATABASE_NAME].isin(criteria.selected_databases)
    )
    schema_ok = (
        all_pass
        if not criteria.selected_schemas
        else assets[assets_schema.SCHEMA_NAME].isin(criteria.selected_schemas)
    )
    hierarchy_mask = db_ok & schema_ok

    type_active = bool(criteria.selected_types)
    asset_type_mask = (
        assets[assets_schema.ASSET_TYPE].isin(criteria.selected_types) if type_active else all_pass
    )

    tag_active = any(t.selected for t in criteria.tag_selections)
    tag_mask = build_tag_mask(
        assets=assets,
        columns=columns,
        selections=criteria.tag_selections,
    )

    and_masks: list[pd.Series] = []
    or_masks: list[pd.Series] = []
    for active, mask, is_or in (
        (hierarchy_active, hierarchy_mask, criteria.is_hierarchy_or_enabled),
        (type_active, asset_type_mask, criteria.is_type_or_enabled),
        (tag_active, tag_mask, criteria.is_tag_or_enabled),
    ):
        if not active:
            continue
        (or_masks if is_or else and_masks).append(mask)

    group_and = all_pass.copy()
    for mask in and_masks:
        group_and &= mask
    if or_masks:
        group_or = pd.Series(data=False, index=assets.index)
        for mask in or_masks:
            group_or |= mask
    else:
        group_or = all_pass

    return assets[freeword_mask & group_and & group_or]


def get_scope_database_names(assets: pd.DataFrame) -> list[str]:
    """表示対象の資産に含まれるデータベース名（重複排除・ソート済み）。"""
    assets_schema = schema.Assets
    return sorted(assets[assets_schema.DATABASE_NAME].dropna().astype(str).unique().tolist())


def get_scope_schema_names(assets: pd.DataFrame, databases: list[str]) -> list[str]:
    """指定データベースに属する、表示対象資産のスキーマ名（重複排除・ソート済み）。"""
    assets_schema = schema.Assets
    if not databases:
        return []
    scoped = assets[assets[assets_schema.DATABASE_NAME].isin(databases)]
    return sorted(scoped[assets_schema.SCHEMA_NAME].dropna().astype(str).unique().tolist())

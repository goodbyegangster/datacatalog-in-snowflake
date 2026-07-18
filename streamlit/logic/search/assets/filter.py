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

    Attributes:
        freeword: オブジェクト名 / 説明、カラム名 / 説明へ適用するフリーワード条件。
        selected_databases: 対象データベース名。空ならデータベースでは絞り込まない。
        selected_schemas: 対象スキーマ名。空ならスキーマでは絞り込まない。
        selected_types: 対象オブジェクト種別。空なら種別では絞り込まない。
        tag_selections: タグキーごとのタグ値条件。タグ値未選択の条件は絞り込みに使わない。
        is_hierarchy_or_enabled: データベース / スキーマ条件を OR 群として扱うか。
        is_type_or_enabled: オブジェクト種別条件を OR 群として扱うか。
        is_tag_or_enabled: タグ条件を OR 群として扱うか。

    """

    freeword: FreewordQuery = field(default_factory=FreewordQuery)
    selected_databases: list[str] = field(default_factory=list)
    selected_schemas: list[str] = field(default_factory=list)
    selected_types: list[str] = field(default_factory=list)
    tag_selections: list[TagSelection] = field(default_factory=list)
    is_hierarchy_or_enabled: bool = False
    is_type_or_enabled: bool = False
    is_tag_or_enabled: bool = False


@dataclass(frozen=True)
class AssetSearchMaskResult:
    """検索条件 1 種類分の mask と合成方法。"""

    is_active: bool
    mask: pd.Series
    is_or_enabled: bool = False


def filter_assets(
    *,
    assets: pd.DataFrame,
    columns: pd.DataFrame,
    criteria: AssetSearchCriteria,
) -> pd.DataFrame:
    """データ資産検索条件に一致する行だけを返す。

    フリーワード条件は常に必須条件として扱う。データベース / スキーマ、オブジェクト種別、
    タグは検索条件グループごとに AND / OR 指定へ振り分けて合成する。
    """
    all_assets_mask = pd.Series(data=True, index=assets.index)

    freeword_mask = _build_freeword_mask(
        assets=assets,
        columns=columns,
        criteria=criteria,
        all_assets_mask=all_assets_mask,
    )
    category_mask = _combine_category_masks(
        all_assets_mask=all_assets_mask,
        category_masks=[
            _build_hierarchy_mask(
                assets=assets,
                criteria=criteria,
                all_assets_mask=all_assets_mask,
            ),
            _build_asset_type_mask(
                assets=assets,
                criteria=criteria,
                all_assets_mask=all_assets_mask,
            ),
            _build_tag_mask(assets=assets, columns=columns, criteria=criteria),
        ],
    )

    return assets[freeword_mask.mask & category_mask.mask]


def _build_freeword_mask(
    *,
    assets: pd.DataFrame,
    columns: pd.DataFrame,
    criteria: AssetSearchCriteria,
    all_assets_mask: pd.Series,
) -> AssetSearchMaskResult:
    """フリーワード検索条件の mask を組み立てる。"""
    assets_schema = schema.Assets
    fw_ids = get_freeword_asset_ids(criteria.freeword, assets, columns)
    freeword_mask = (
        all_assets_mask if fw_ids is None else assets[assets_schema.TABLE_ID].isin(fw_ids)
    )
    return AssetSearchMaskResult(
        is_active=fw_ids is not None,
        mask=freeword_mask,
    )


def _build_hierarchy_mask(
    *,
    assets: pd.DataFrame,
    criteria: AssetSearchCriteria,
    all_assets_mask: pd.Series,
) -> AssetSearchMaskResult:
    """データベース / スキーマ検索条件の mask を組み立てる。"""
    assets_schema = schema.Assets
    is_active = bool(criteria.selected_databases or criteria.selected_schemas)
    db_ok = (
        all_assets_mask
        if not criteria.selected_databases
        else assets[assets_schema.DATABASE_NAME].isin(criteria.selected_databases)
    )
    schema_ok = (
        all_assets_mask
        if not criteria.selected_schemas
        else assets[assets_schema.SCHEMA_NAME].isin(criteria.selected_schemas)
    )
    return AssetSearchMaskResult(
        is_active=is_active,
        mask=db_ok & schema_ok,
        is_or_enabled=criteria.is_hierarchy_or_enabled,
    )


def _build_asset_type_mask(
    *,
    assets: pd.DataFrame,
    criteria: AssetSearchCriteria,
    all_assets_mask: pd.Series,
) -> AssetSearchMaskResult:
    """オブジェクト種別検索条件の mask を組み立てる。"""
    assets_schema = schema.Assets
    is_active = bool(criteria.selected_types)
    return AssetSearchMaskResult(
        is_active=is_active,
        mask=assets[assets_schema.ASSET_TYPE].isin(criteria.selected_types)
        if is_active
        else all_assets_mask,
        is_or_enabled=criteria.is_type_or_enabled,
    )


def _build_tag_mask(
    *,
    assets: pd.DataFrame,
    columns: pd.DataFrame,
    criteria: AssetSearchCriteria,
) -> AssetSearchMaskResult:
    """タグ検索条件の mask を組み立てる。"""
    return AssetSearchMaskResult(
        is_active=any(t.selected for t in criteria.tag_selections),
        mask=build_tag_mask(
            assets=assets,
            columns=columns,
            selections=criteria.tag_selections,
        ),
        is_or_enabled=criteria.is_tag_or_enabled,
    )


def _combine_category_masks(
    *, all_assets_mask: pd.Series, category_masks: list[AssetSearchMaskResult]
) -> AssetSearchMaskResult:
    """AND / OR 指定に従ってカテゴリ条件の mask を合成する。"""
    and_masks: list[pd.Series] = []
    or_masks: list[pd.Series] = []
    for category_mask in category_masks:
        if not category_mask.is_active:
            continue
        (or_masks if category_mask.is_or_enabled else and_masks).append(category_mask.mask)

    group_and = all_assets_mask.copy()
    for mask in and_masks:
        group_and &= mask
    if or_masks:
        group_or = pd.Series(data=False, index=all_assets_mask.index)
        for mask in or_masks:
            group_or |= mask
    else:
        group_or = all_assets_mask

    return AssetSearchMaskResult(
        is_active=any(mask.is_active for mask in category_masks),
        mask=group_and & group_or,
    )


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

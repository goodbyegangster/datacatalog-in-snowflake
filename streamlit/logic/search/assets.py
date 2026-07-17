"""データ資産検索の純ロジック。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from numbers import Integral

import pandas as pd

from catalog import schema
from logic.search.common import parse_freeword

COLUMN_REASON_LIMIT = 2


def _to_int(value: object) -> int:
    """pandas 由来のスカラー値を TABLE_ID 用の int に正規化する。"""
    if isinstance(value, Integral):
        return int(value)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return int(str(value))


# --- Freeword query ---------------------------------------------------------


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
    assets_schema = schema.Assets
    columns_schema = schema.Columns
    needle = token.lower()
    ids: set[int] = set()

    def contains(series: pd.Series) -> pd.Series:
        return series.fillna("").str.lower().str.contains(needle, regex=False)

    if fq.target_asset_name:
        ids |= set(assets.loc[contains(assets[assets_schema.ASSET_NAME]), assets_schema.TABLE_ID])
    if fq.target_asset_desc:
        ids |= set(assets.loc[contains(assets[assets_schema.DESCRIPTION]), assets_schema.TABLE_ID])
    if fq.target_column_name:
        ids |= set(
            columns.loc[contains(columns[columns_schema.COLUMN_NAME]), columns_schema.TABLE_ID]
        )
    if fq.target_column_desc:
        ids |= set(
            columns.loc[contains(columns[columns_schema.DESCRIPTION]), columns_schema.TABLE_ID]
        )
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


# --- Freeword match reasons ------------------------------------------------


@dataclass
class FreewordMatchReason:
    """フリーワード一致理由の表示値。"""

    text: str = ""


@dataclass
class _FreewordMatchHit:
    """フリーワードが TABLE_ID 内のどこに hit したか。"""

    asset_name: bool = False
    asset_desc: bool = False
    column_names: list[str] = field(default_factory=list)
    column_desc_names: list[str] = field(default_factory=list)


def _ordered_column_names(columns: pd.DataFrame, mask: pd.Series) -> list[str]:
    """条件に一致したカラム名を表示順で重複排除して返す。"""
    columns_schema = schema.Columns
    matched = columns.loc[
        mask, [columns_schema.TABLE_ID, columns_schema.ORDINAL_POSITION, columns_schema.COLUMN_NAME]
    ]
    matched = matched.sort_values(
        [columns_schema.TABLE_ID, columns_schema.ORDINAL_POSITION, columns_schema.COLUMN_NAME]
    )
    return list(dict.fromkeys(matched[columns_schema.COLUMN_NAME].astype(str).tolist()))


def _merge_hits(left: _FreewordMatchHit, right: _FreewordMatchHit) -> _FreewordMatchHit:
    """複数トークンの一致理由を TABLE_ID 単位でまとめる。"""
    return _FreewordMatchHit(
        asset_name=left.asset_name or right.asset_name,
        asset_desc=left.asset_desc or right.asset_desc,
        column_names=list(dict.fromkeys([*left.column_names, *right.column_names])),
        column_desc_names=list(dict.fromkeys([*left.column_desc_names, *right.column_desc_names])),
    )


def _reasons_matching_token(
    token: str, assets: pd.DataFrame, columns: pd.DataFrame, fq: FreewordQuery
) -> dict[int, _FreewordMatchHit]:
    """1 トークンに hit した場所を TABLE_ID ごとに返す。"""
    assets_schema = schema.Assets
    columns_schema = schema.Columns
    needle = token.lower()
    reasons: dict[int, _FreewordMatchHit] = {}

    def contains(series: pd.Series) -> pd.Series:
        return series.fillna("").str.lower().str.contains(needle, regex=False)

    if fq.target_asset_name:
        for table_id in assets.loc[
            contains(assets[assets_schema.ASSET_NAME]), assets_schema.TABLE_ID
        ]:
            reasons.setdefault(int(table_id), _FreewordMatchHit()).asset_name = True
    if fq.target_asset_desc:
        for table_id in assets.loc[
            contains(assets[assets_schema.DESCRIPTION]), assets_schema.TABLE_ID
        ]:
            reasons.setdefault(int(table_id), _FreewordMatchHit()).asset_desc = True
    if fq.target_column_name:
        name_mask = contains(columns[columns_schema.COLUMN_NAME])
        for table_id, group in columns.loc[name_mask].groupby(columns_schema.TABLE_ID):
            reasons.setdefault(
                _to_int(table_id), _FreewordMatchHit()
            ).column_names = _ordered_column_names(group, pd.Series(data=True, index=group.index))
    if fq.target_column_desc:
        desc_mask = contains(columns[columns_schema.DESCRIPTION])
        for table_id, group in columns.loc[desc_mask].groupby(columns_schema.TABLE_ID):
            reasons.setdefault(
                _to_int(table_id), _FreewordMatchHit()
            ).column_desc_names = _ordered_column_names(
                group, pd.Series(data=True, index=group.index)
            )
    return reasons


def _format_object_target(hit: _FreewordMatchHit) -> str:
    object_parts: list[str] = []
    if hit.asset_name:
        object_parts.append("名前")
    if hit.asset_desc:
        object_parts.append("説明")
    return " / ".join(object_parts)


def _format_column_target(label: str, column_names: list[str]) -> str | None:
    if not column_names:
        return None
    visible = column_names[:COLUMN_REASON_LIMIT]
    suffix = (
        f" ほか{len(column_names) - COLUMN_REASON_LIMIT}件"
        if len(column_names) > COLUMN_REASON_LIMIT
        else ""
    )
    return f"{label} {', '.join(visible)}{suffix}"


def _format_column_targets(hit: _FreewordMatchHit) -> str:
    column_parts: list[str] = []
    if column_name_reason := _format_column_target("カラム名", hit.column_names):
        column_parts.append(column_name_reason)
    if column_desc_reason := _format_column_target("カラム説明", hit.column_desc_names):
        column_parts.append(column_desc_reason)
    return "、".join(column_parts)


def _format_reason(hit: _FreewordMatchHit) -> str:
    object_text = _format_object_target(hit)
    column_text = _format_column_targets(hit)

    match bool(object_text), bool(column_text):
        case True, True:
            return f"{object_text} に一致。{column_text} に一致。"
        case True, False:
            return f"{object_text} に一致。"
        case False, True:
            return f"{column_text} に一致。"
        case False, False:
            return ""


def freeword_match_reasons(
    fq: FreewordQuery, assets: pd.DataFrame, columns: pd.DataFrame
) -> dict[int, FreewordMatchReason]:
    """フリーワード検索の一致理由を TABLE_ID -> 表示値で返す。"""
    op, tokens = parse_freeword(fq.text)
    if not tokens:
        return {}

    per_token = [_reasons_matching_token(t, assets, columns, fq) for t in tokens]
    if op == "and":
        matched_ids = freeword_asset_ids(fq, assets, columns) or set()
    else:
        matched_ids = set().union(*(set(reasons) for reasons in per_token))

    reasons_by_id: dict[int, _FreewordMatchHit] = {}
    for token_reasons in per_token:
        for table_id in matched_ids & set(token_reasons):
            if table_id in reasons_by_id:
                reasons_by_id[table_id] = _merge_hits(
                    reasons_by_id[table_id], token_reasons[table_id]
                )
            else:
                reasons_by_id[table_id] = token_reasons[table_id]
    return {
        table_id: FreewordMatchReason(
            text=_format_reason(hit),
        )
        for table_id, hit in reasons_by_id.items()
    }


# --- Search criteria --------------------------------------------------------


@dataclass
class TagSelection:
    """1 タグキーの選択状態。``selected`` が空なら無制約（絞り込まない）。"""

    tag_database: str
    tag_schema: str
    tag_name: str
    selected: list[str]
    tag_value_options: list[str]  # UI の選択肢。フィルタ判定には用いない。

    @property
    def is_unconstrained(self) -> bool:
        """タグ値が選択されていないか。"""
        return not self.selected


@dataclass
class AssetSearchCriteria:
    """データ資産検索の条件一式。

    ``is_*_or_enabled`` は検索条件グループ間の結合指定。
    False = AND（必須・初期）、True = OR（いずれか）。
    """

    freeword: FreewordQuery = field(default_factory=FreewordQuery)
    selected_databases: list[str] = field(default_factory=list)
    selected_schemas: list[str] = field(default_factory=list)
    selected_types: list[str] = field(default_factory=list)
    tag_selections: list[TagSelection] = field(default_factory=list)
    is_hierarchy_or_enabled: bool = False
    is_type_or_enabled: bool = False
    is_tag_or_enabled: bool = False


# --- Asset filter -----------------------------------------------------------


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
    assets_schema = schema.Assets
    mask = pd.Series(data=True, index=assets.index)
    for sel in selections:
        if sel.is_unconstrained:
            continue
        matches = _tag_value_matcher(sel, set(sel.selected))
        matched_ids = set(
            assets.loc[assets[assets_schema.TAGS].map(matches), assets_schema.TABLE_ID]
        )
        if not columns.empty:
            col_hit = columns[schema.Columns.TAGS].map(matches)
            matched_ids |= set(columns.loc[col_hit, schema.Columns.TABLE_ID])
        mask &= assets[assets_schema.TABLE_ID].isin(matched_ids)
    return mask


def filter_assets(
    assets: pd.DataFrame, columns: pd.DataFrame, criteria: AssetSearchCriteria
) -> pd.DataFrame:
    """design-search の「page：データ資産」に従いデータ資産を絞り込む（バケット方式）。

    ``①フリーワード AND （AND 群を全て満たす） AND （OR 群のいずれかを満たす）``。
    未選択（無制約）の検索条件グループは AND / OR いずれの群にも入れない。
    """
    assets_schema = schema.Assets
    all_pass = pd.Series(data=True, index=assets.index)

    fw_ids = freeword_asset_ids(criteria.freeword, assets, columns)
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
    tag_mask = _tag_mask(assets, columns, criteria.tag_selections)

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


# --- Scope options ----------------------------------------------------------


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

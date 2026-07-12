"""検索・フィルタの純ロジック。

design-search.md の「page：データ資産」「page：ユーザー」の検索仕様を、Streamlit へ依存
しない純関数として実装する（ウィジェットや session_state は views 側が扱う）。DataFrame を
入力に受け、フィルタ済み DataFrame を返す。列参照は ``catalog.schema`` の StrEnum を用いる。

仕様上の解釈（design-implementation の確定事項）:
- フリーワードは ` OR ` があれば OR、無ければ ` AND ` で分割（部分一致・大小無視・リテラル）。
- カテゴリ2〜4 の初期は **未選択**。**未選択のカテゴリは無制約**（絞り込まない）、値を選ぶと
  そのカテゴリで絞り込む（当初設計の「全選択 = 全件」を否定し、未選択 = 無制約とする）。
- カテゴリ間の結合は **バケット方式**。カテゴリ 2〜4 それぞれに AND / OR を持たせ、
  ``AND`` のカテゴリは全て必須、``OR`` のカテゴリはいずれか 1 つ満たせばよい。
  最終 = ``①フリーワード AND （AND 群を全て満たす） AND （OR 群のいずれかを満たす）``。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import pandas as pd

from catalog import schema
from settings import DISPLAY_SCOPES

# --- フリーワード ---------------------------------------------------------


def parse_freeword(text: str) -> tuple[str, list[str]]:
    """フリーワードを (結合演算子, トークン列) に分解する。

    ` OR ` を含めば OR、無く ` AND ` を含めば AND、いずれも無ければ単一トークン（AND 扱い）。
    空文字・空白のみなら空トークン列（= 無制約）を返す。
    """
    text = (text or "").strip()
    if not text:
        return ("and", [])
    if " OR " in text:
        return ("or", [t.strip() for t in text.split(" OR ") if t.strip()])
    if " AND " in text:
        return ("and", [t.strip() for t in text.split(" AND ") if t.strip()])
    return ("and", [text])


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


# --- データ資産の検索 -----------------------------------------------------


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

    ``*_or`` はカテゴリ間結合の指定。False = AND（必須・初期）、True = OR（いずれか）。
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
    """タグ絞り込み（カテゴリ4）のブールマスク。未選択のタグは無制約として無視。

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
    未選択（無制約）のカテゴリは AND / OR いずれの群にも入れない。
    """
    A = schema.Assets
    all_pass = pd.Series(True, index=assets.index)

    # カテゴリ1：フリーワード（空入力は無制約）
    fw_ids = freeword_asset_ids(criteria.freeword, assets, columns)
    cat1 = all_pass if fw_ids is None else assets[A.TABLE_ID].isin(fw_ids)

    # カテゴリ2：階層（DB / スキーマ）。各プルダウンは未選択なら無制約。
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
    cat2 = db_ok & schema_ok

    # カテゴリ3：オブジェクト種別
    type_active = bool(criteria.selected_types)
    cat3 = assets[A.ASSET_TYPE].isin(criteria.selected_types) if type_active else all_pass

    # カテゴリ4：タグ（資産自身 or そのカラムに付与されたタグでヒット）
    tag_active = any(t.selected for t in criteria.tag_selections)
    cat4 = _tag_mask(assets, columns, criteria.tag_selections)

    # 有効なカテゴリを AND 群 / OR 群へ振り分ける
    and_masks: list[pd.Series] = []
    or_masks: list[pd.Series] = []
    for active, mask, is_or in (
        (hierarchy_active, cat2, criteria.hierarchy_or),
        (type_active, cat3, criteria.type_or),
        (tag_active, cat4, criteria.tag_or),
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

    return assets[cat1 & group_and & group_or]


# --- 検索プルダウンの選択肢（DISPLAY_SCOPES が唯一の正） -------------------


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


# --- ユーザーの検索（Step 3 後半で利用） ---------------------------------


@dataclass
class UserFreewordQuery:
    """ユーザーのフリーワードと検索対象（名前 / 表示名）。"""

    text: str = ""
    target_user_name: bool = True
    target_display_name: bool = True


def filter_users(
    users: pd.DataFrame, freeword: UserFreewordQuery, only_user_name: str | None = None
) -> pd.DataFrame:
    """ユーザーを絞り込む。``only_user_name`` 指定時は自ユーザーのみ。"""
    U = schema.Users
    df = users
    if only_user_name is not None:
        df = df[df[U.USER_NAME] == only_user_name]

    op, tokens = parse_freeword(freeword.text)
    if not tokens:
        return df

    def token_mask(token: str) -> pd.Series:
        needle = token.lower()
        mask = pd.Series(False, index=df.index)
        if freeword.target_user_name:
            mask |= df[U.USER_NAME].fillna("").str.lower().str.contains(needle, regex=False)
        if freeword.target_display_name:
            mask |= df[U.DISPLAY_NAME].fillna("").str.lower().str.contains(needle, regex=False)
        return mask

    masks = [token_mask(t) for t in tokens]
    combined = masks[0]
    for m in masks[1:]:
        combined = combined | m if op == "or" else combined & m
    return df[combined]

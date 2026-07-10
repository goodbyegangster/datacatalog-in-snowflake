"""カタログ表へのデータアクセス層。

design-model.md のカタログ表（CATALOG スキーマ）を pandas DataFrame として取得する。
UI 層はここだけを通じてデータへアクセスし、SQL / クエリはこのモジュールに集約する。
結果は ``@st.cache_data`` でキャッシュする（TTL はマスター更新間隔に合わせ長め）。

列名は ``lib.schema`` の StrEnum を用いて参照する。DataFrame の列ラベルは Enum の値
（= 文字列）と一致し、``_normalize`` が列の存在検証と並び替えを行う。

配列列（TAGS / FOREIGN_KEYS / USER_ROLES / ASSET_ROLES）は Snowpark ``to_pandas`` では
VARIANT が JSON 文字列で返るため、``_parse_json_column`` で list / dict へパースして揃える。
DISPLAY_SCOPES に属さないデータ資産は公開対象外のため、資産系の表は取得後に絞り込む。
"""

from __future__ import annotations

import json
from enum import StrEnum

import pandas as pd
import streamlit as st
from snowflake.snowpark import Session

from lib import schema
from settings import CATALOG_LOCATION, DISPLAY_SCOPES

# マスター更新（task は 3 時間ごと）に合わせ、キャッシュは長めに設定する。
CACHE_TTL = 3600


def _catalog_fqn(table_name: str) -> str:
    """CATALOG_LOCATION を前置した、カタログ表の完全修飾名を返す。"""
    return f'{CATALOG_LOCATION["DATABASE_NAME"]}.{CATALOG_LOCATION["SCHEMA_NAME"]}.{table_name}'


def _read_table(session: Session, table_name: str) -> pd.DataFrame:
    """カタログ表を DataFrame として読み込む（列名は文字列へ正規化）。"""
    df = session.table(_catalog_fqn(table_name)).to_pandas()
    df.columns = df.columns.map(str)
    return df


def _normalize(df: pd.DataFrame, columns: type[StrEnum]) -> pd.DataFrame:
    """想定列の存在を検証し、Enum で定義した列順に並べ替えて返す。"""
    expected = [str(c) for c in columns]
    missing = set(expected) - set(df.columns)
    if missing:
        message = f"カタログ表 {columns.__name__} に想定列がありません: {sorted(missing)}"
        raise ValueError(message)
    return df.loc[:, expected].reset_index(drop=True)


def _parse_json_column(df: pd.DataFrame, column: StrEnum) -> None:
    """VARIANT 由来の JSON 文字列列を list / dict へインプレースで変換する。

    Snowpark ``to_pandas`` は ARRAY / OBJECT を JSON 文字列で返す。NULL や欠損は
    空配列に正規化する（SQL 側で coalesce 済みだが防御的に扱う）。
    """
    col = str(column)
    if col not in df.columns:
        return

    def convert(value: object) -> object:
        if isinstance(value, str):
            return json.loads(value)
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return []
        return value

    df[col] = df[col].map(convert)


def _filter_display_scopes(df: pd.DataFrame, db_col: StrEnum, schema_col: StrEnum) -> pd.DataFrame:
    """DISPLAY_SCOPES（公開対象の DB / スキーマ）に属する行だけを残す。"""
    scopes = {(s["DATABASE_NAME"], s["SCHEMA_NAME"]) for s in DISPLAY_SCOPES}
    keys = pd.Series(zip(df[str(db_col)], df[str(schema_col)], strict=True), index=df.index)
    return df[keys.isin(scopes)]


@st.cache_data(ttl=CACHE_TTL)
def load_assets(_session: Session) -> pd.DataFrame:
    """CATALOG.ASSETS。DISPLAY_SCOPES に含まれる資産のみ。"""
    A = schema.Assets
    df = _read_table(_session, "ASSETS")
    _parse_json_column(df, A.TAGS)
    df = _filter_display_scopes(df, A.DATABASE_NAME, A.SCHEMA_NAME)
    return _normalize(df, schema.Assets)


@st.cache_data(ttl=CACHE_TTL)
def load_columns(_session: Session) -> pd.DataFrame:
    """CATALOG.COLUMNS。DISPLAY_SCOPES に含まれる資産のカラムのみ。"""
    C = schema.Columns
    df = _read_table(_session, "COLUMNS")
    _parse_json_column(df, C.TAGS)
    _parse_json_column(df, C.FOREIGN_KEYS)
    df = _filter_display_scopes(df, C.DATABASE_NAME, C.SCHEMA_NAME)
    return _normalize(df, schema.Columns)


@st.cache_data(ttl=CACHE_TTL)
def load_users(_session: Session) -> pd.DataFrame:
    """CATALOG.USERS。"""
    df = _read_table(_session, "USERS")
    return _normalize(df, schema.Users)


@st.cache_data(ttl=CACHE_TTL)
def load_tags(_session: Session) -> pd.DataFrame:
    """CATALOG.TAGS（検索プルダウン用の allowed_values マスター）。"""
    df = _read_table(_session, "TAGS")
    return _normalize(df, schema.Tags)


@st.cache_data(ttl=CACHE_TTL)
def load_access_edges(_session: Session) -> pd.DataFrame:
    """CATALOG.ACCESS_EDGES（ロール継承・権限付与の有向エッジ）。"""
    df = _read_table(_session, "ACCESS_EDGES")
    return _normalize(df, schema.AccessEdges)


@st.cache_data(ttl=CACHE_TTL)
def load_asset_visibility(_session: Session) -> pd.DataFrame:
    """CATALOG.ASSET_VISIBILITY（user↔asset の到達ペア）。DISPLAY_SCOPES の資産のみ。"""
    V = schema.AssetVisibility
    df = _read_table(_session, "ASSET_VISIBILITY")
    _parse_json_column(df, V.USER_ROLES)
    _parse_json_column(df, V.ASSET_ROLES)
    df = _filter_display_scopes(df, V.DATABASE_NAME, V.SCHEMA_NAME)
    return _normalize(df, schema.AssetVisibility)

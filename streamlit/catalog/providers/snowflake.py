"""Snowflake-backed catalog data access."""

from __future__ import annotations

import json
from enum import StrEnum

import pandas as pd
import streamlit as st
from snowflake.snowpark import Session

from catalog import schema
from infrastructure.snowflake import get_session
from settings import CATALOG_LOCATION, DISPLAY_SCOPES

CACHE_TTL = 3600


def _build_catalog_fqn(table_name: str) -> str:
    """CATALOG_LOCATION を前置した、カタログ表の完全修飾名を返す。"""
    return f"{CATALOG_LOCATION['DATABASE_NAME']}.{CATALOG_LOCATION['SCHEMA_NAME']}.{table_name}"


def _read_catalog_table(session: Session, table_name: str) -> pd.DataFrame:
    """カタログ表を DataFrame として読み込む（列名は文字列へ正規化）。"""
    df = session.table(_build_catalog_fqn(table_name)).to_pandas()
    df.columns = df.columns.map(str)
    return df


def _normalize_catalog_table(df: pd.DataFrame, columns: type[StrEnum]) -> pd.DataFrame:
    """想定列の存在を検証し、Enum で定義した列順に並べ替えて返す。"""
    expected = [str(c) for c in columns]
    missing = set(expected) - set(df.columns)
    if missing:
        message = f"カタログ表 {columns.__name__} に想定列がありません: {sorted(missing)}"
        raise ValueError(message)
    return df.loc[:, expected].reset_index(drop=True)


def _parse_json_column(df: pd.DataFrame, column: StrEnum) -> pd.DataFrame:
    """VARIANT 由来の JSON 文字列列を list / dict へ変換した DataFrame を返す。"""
    col = str(column)
    if col not in df.columns:
        return df

    def convert_json_value(value: object) -> object:
        if isinstance(value, str):
            return json.loads(value)
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return []
        return value

    parsed = df.copy()
    parsed[col] = parsed[col].map(convert_json_value)
    return parsed


def _filter_rows_by_display_scopes(
    df: pd.DataFrame, db_col: StrEnum, schema_col: StrEnum
) -> pd.DataFrame:
    """DISPLAY_SCOPES（公開対象の DB / スキーマ）に属する行だけを残す。"""
    scopes = {(s["DATABASE_NAME"], s["SCHEMA_NAME"]) for s in DISPLAY_SCOPES}
    keys = pd.Series(list(zip(df[str(db_col)], df[str(schema_col)], strict=True)), index=df.index)
    return df[keys.isin(scopes)]


@st.cache_data(ttl=CACHE_TTL)
def load_assets() -> pd.DataFrame:
    """CATALOG.ASSETS。DISPLAY_SCOPES に含まれる資産のみ。"""
    assets_schema = schema.Assets
    df = _read_catalog_table(get_session(), "ASSETS")
    df = _parse_json_column(df, assets_schema.TAGS)
    df = _filter_rows_by_display_scopes(
        df, assets_schema.DATABASE_NAME, assets_schema.SCHEMA_NAME
    )
    return _normalize_catalog_table(df, schema.Assets)


@st.cache_data(ttl=CACHE_TTL)
def load_columns() -> pd.DataFrame:
    """CATALOG.COLUMNS。DISPLAY_SCOPES に含まれる資産のカラムのみ。"""
    columns_schema = schema.Columns
    df = _read_catalog_table(get_session(), "COLUMNS")
    df = _parse_json_column(df, columns_schema.TAGS)
    df = _parse_json_column(df, columns_schema.FOREIGN_KEYS)
    df = _filter_rows_by_display_scopes(
        df, columns_schema.DATABASE_NAME, columns_schema.SCHEMA_NAME
    )
    return _normalize_catalog_table(df, schema.Columns)


@st.cache_data(ttl=CACHE_TTL)
def load_users() -> pd.DataFrame:
    """CATALOG.USERS。"""
    df = _read_catalog_table(get_session(), "USERS")
    return _normalize_catalog_table(df, schema.Users)


@st.cache_data(ttl=CACHE_TTL)
def load_tags() -> pd.DataFrame:
    """CATALOG.TAGS（検索プルダウン用の allowed_values マスター）。"""
    df = _read_catalog_table(get_session(), "TAGS")
    return _normalize_catalog_table(df, schema.Tags)


@st.cache_data(ttl=CACHE_TTL)
def load_access_edges() -> pd.DataFrame:
    """CATALOG.ACCESS_EDGES（ロール継承・権限付与の有向エッジ）。"""
    df = _read_catalog_table(get_session(), "ACCESS_EDGES")
    return _normalize_catalog_table(df, schema.AccessEdges)


@st.cache_data(ttl=CACHE_TTL)
def load_asset_visibility() -> pd.DataFrame:
    """CATALOG.ASSET_VISIBILITY（user↔asset の到達ペア）。DISPLAY_SCOPES の資産のみ。"""
    visibility_schema = schema.AssetVisibility
    df = _read_catalog_table(get_session(), "ASSET_VISIBILITY")
    df = _parse_json_column(df, visibility_schema.USER_ROLES)
    df = _parse_json_column(df, visibility_schema.ASSET_ROLES)
    df = _filter_rows_by_display_scopes(
        df, visibility_schema.DATABASE_NAME, visibility_schema.SCHEMA_NAME
    )
    return _normalize_catalog_table(df, schema.AssetVisibility)

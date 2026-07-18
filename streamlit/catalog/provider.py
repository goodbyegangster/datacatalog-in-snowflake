"""Catalog data access facade."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Literal, Protocol

import pandas as pd

from catalog.providers import fake, snowflake

CatalogDataMode = Literal["snowflake", "fake"]


class CatalogProvider(Protocol):
    """catalog provider module が満たすべき読み込み関数セット。"""

    load_assets: Callable[[], pd.DataFrame]
    load_columns: Callable[[], pd.DataFrame]
    load_users: Callable[[], pd.DataFrame]
    load_tags: Callable[[], pd.DataFrame]
    load_access_edges: Callable[[], pd.DataFrame]
    load_asset_visibility: Callable[[], pd.DataFrame]


_FAKE_PROVIDER: CatalogProvider = fake
_SNOWFLAKE_PROVIDER: CatalogProvider = snowflake


def get_data_mode() -> CatalogDataMode:
    """環境変数 CATALOG_DATA_MODE からカタログデータの取得元を返す。

    ``CATALOG_DATA_MODE=fake`` のときだけ fake catalog を使い、未指定時や
    それ以外の値では Snowflake を使う。
    """
    mode = os.getenv("CATALOG_DATA_MODE", "snowflake").lower()
    if mode == "fake":
        return "fake"
    return "snowflake"


def _provider() -> CatalogProvider:
    """現在のデータ取得モードに対応する provider module を返す。

    fake catalog は Snowflake 接続なしで画面を起動するために使い、snowflake
    provider は Snowflake 上の CATALOG テーブルを読む。
    """
    if get_data_mode() == "fake":
        return _FAKE_PROVIDER
    return _SNOWFLAKE_PROVIDER


def load_assets() -> pd.DataFrame:
    """データ資産カタログを読み込む。"""
    return _provider().load_assets()


def load_columns() -> pd.DataFrame:
    """カラムカタログを読み込む。"""
    return _provider().load_columns()


def load_users() -> pd.DataFrame:
    """ユーザーカタログを読み込む。"""
    return _provider().load_users()


def load_tags() -> pd.DataFrame:
    """タグカタログを読み込む。"""
    return _provider().load_tags()


def load_access_edges() -> pd.DataFrame:
    """アクセス経路エッジを読み込む。"""
    return _provider().load_access_edges()


def load_asset_visibility() -> pd.DataFrame:
    """ユーザー別の資産閲覧可否を読み込む。"""
    return _provider().load_asset_visibility()

"""Catalog data access facade.

``CATALOG_DATA_MODE=fake`` のときは Snowflake 接続不要の fake catalog を使い、
それ以外は Snowflake 上の CATALOG テーブルを読む。
"""

from __future__ import annotations

import os
from typing import Literal

import pandas as pd

CatalogDataMode = Literal["snowflake", "fake"]


def data_mode() -> CatalogDataMode:
    """カタログデータの取得元を返す。未指定時は Snowflake。"""
    mode = os.getenv("CATALOG_DATA_MODE", "snowflake").lower()
    if mode == "fake":
        return "fake"
    return "snowflake"


def _provider():
    if data_mode() == "fake":
        from lib import catalog_fake

        return catalog_fake

    from lib import catalog_snowflake

    return catalog_snowflake


def load_assets() -> pd.DataFrame:
    return _provider().load_assets()


def load_columns() -> pd.DataFrame:
    return _provider().load_columns()


def load_users() -> pd.DataFrame:
    return _provider().load_users()


def load_tags() -> pd.DataFrame:
    return _provider().load_tags()


def load_access_edges() -> pd.DataFrame:
    return _provider().load_access_edges()


def load_asset_visibility() -> pd.DataFrame:
    return _provider().load_asset_visibility()

from __future__ import annotations

import pandas as pd

from catalog.providers import fake as catalog_fake

DB = catalog_fake.DB
TAG_SCHEMA = catalog_fake.TAG_SCHEMA


def tag_ref(tag_name: str, tag_value: str) -> dict[str, str]:
    return {
        "TAG_DATABASE": DB,
        "TAG_SCHEMA": TAG_SCHEMA,
        "TAG_NAME": tag_name,
        "TAG_VALUE": tag_value,
    }


def assets() -> pd.DataFrame:
    return catalog_fake.load_assets()


def columns() -> pd.DataFrame:
    return catalog_fake.load_columns()


def users() -> pd.DataFrame:
    return catalog_fake.load_users()


def tags() -> pd.DataFrame:
    return catalog_fake.load_tags()


def asset_visibility() -> pd.DataFrame:
    return catalog_fake.load_asset_visibility()


def access_edges() -> pd.DataFrame:
    return catalog_fake.load_access_edges()

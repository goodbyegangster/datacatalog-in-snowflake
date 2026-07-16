from __future__ import annotations

import pandas as pd

from catalog.providers import fake as catalog_fake

DB = catalog_fake.DB
TAG_SCHEMA = catalog_fake.TAG_SCHEMA


def tag_ref(tag_name: str, tag_value: str) -> dict[str, str]:
    """テスト用のタグ参照を返す。"""
    return {
        "TAG_DATABASE": DB,
        "TAG_SCHEMA": TAG_SCHEMA,
        "TAG_NAME": tag_name,
        "TAG_VALUE": tag_value,
    }


def assets() -> pd.DataFrame:
    """Fake の資産 fixture を返す。"""
    return catalog_fake.load_assets()


def columns() -> pd.DataFrame:
    """Fake のカラム fixture を返す。"""
    return catalog_fake.load_columns()


def users() -> pd.DataFrame:
    """Fake のユーザー fixture を返す。"""
    return catalog_fake.load_users()


def tags() -> pd.DataFrame:
    """Fake のタグ fixture を返す。"""
    return catalog_fake.load_tags()


def asset_visibility() -> pd.DataFrame:
    """Fake の資産閲覧可否 fixture を返す。"""
    return catalog_fake.load_asset_visibility()


def access_edges() -> pd.DataFrame:
    """Fake のアクセス経路 fixture を返す。"""
    return catalog_fake.load_access_edges()

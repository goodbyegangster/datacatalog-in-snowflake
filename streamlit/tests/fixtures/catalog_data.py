from __future__ import annotations

import pandas as pd

import settings
from catalog.providers import fake as catalog_fake


def database_name() -> str:
    """テスト実行時点の settings に基づくデータベース名を返す。"""
    return settings.CATALOG_LOCATION["DATABASE_NAME"]


def tag_schema_name(tag_name: str) -> str:
    """テスト実行時点の settings に基づくタグスキーマ名を返す。"""
    for tag_key in settings.SELECTABLE_TAG_KEYS:
        if tag_key["TAG_NAME"] == tag_name:
            return tag_key["SCHEMA_NAME"]
    message = f"settings.SELECTABLE_TAG_KEYS にタグが定義されていません: {tag_name}"
    raise ValueError(message)


def asset_fqn(schema_name: str, asset_name: str) -> str:
    """テスト用のデータ資産 FQN を返す。"""
    return f"{database_name()}.{schema_name}.{asset_name}"


def tag_ref(tag_name: str, tag_value: str) -> dict[str, str]:
    """テスト用のタグ参照を返す。"""
    return {
        "TAG_DATABASE": database_name(),
        "TAG_SCHEMA": tag_schema_name(tag_name),
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

"""Snowflake 接続なしで画面を起動するための fake catalog provider."""

from __future__ import annotations

import pandas as pd

import settings
from catalog import schema


def _get_database_name() -> str:
    """Fake catalog が参照するデータベース名を settings から返す。"""
    return settings.CATALOG_LOCATION["DATABASE_NAME"]


def _find_selectable_tag_key(tag_name: str) -> settings.SelectableTagKey:
    """Fake tag 名に対応する settings のタグキーを返す。"""
    for tag_key in settings.SELECTABLE_TAG_KEYS:
        if tag_key["TAG_NAME"] == tag_name:
            return tag_key
    message = f"settings.SELECTABLE_TAG_KEYS に fake tag が定義されていません: {tag_name}"
    raise ValueError(message)


def _build_tag_ref(tag_name: str, tag_value: str) -> dict[str, str]:
    """資産やカラムに埋め込むタグ参照を作る。"""
    tag_key = _find_selectable_tag_key(tag_name)
    return {
        "TAG_DATABASE": tag_key["DATABASE_NAME"],
        "TAG_SCHEMA": tag_key["SCHEMA_NAME"],
        "TAG_NAME": tag_name,
        "TAG_VALUE": tag_value,
    }


def _build_tag_row(tag_name: str, tag_value: str, tag_comment: str) -> dict[str, str]:
    """タグ一覧として返すタグ行を作る。"""
    tag_key = _find_selectable_tag_key(tag_name)
    return {
        "TAG_DATABASE": tag_key["DATABASE_NAME"],
        "TAG_SCHEMA": tag_key["SCHEMA_NAME"],
        "TAG_NAME": tag_name,
        "TAG_VALUE": tag_value,
        "TAG_COMMENT": tag_comment,
    }


def load_assets() -> pd.DataFrame:
    """Fake のデータ資産カタログを返す。"""
    assets_schema = schema.Assets
    db = _get_database_name()
    return pd.DataFrame(
        [
            {
                assets_schema.TABLE_ID: 1,
                assets_schema.DATABASE_NAME: db,
                assets_schema.SCHEMA_NAME: "DATA_SALES",
                assets_schema.ASSET_NAME: "ORDERS",
                assets_schema.ASSET_TYPE: "BASE TABLE",
                assets_schema.DESCRIPTION: "Sales order facts",
                assets_schema.ROW_COUNT: 120,
                assets_schema.BYTES: 4096,
                assets_schema.TAGS: [_build_tag_ref("DATA_DOMAIN", "SALES")],
                assets_schema.CONTACT_STEWARD: "DATA_STEWARD",
                assets_schema.CONTACT_SUPPORT: "DATA_SUPPORT",
                assets_schema.CONTACT_ACCESS_APPROVAL: "DATA_APPROVER",
                assets_schema.CONTACT_SECURITY_COMPLIANCE: "SECURITY",
                assets_schema.IS_PUBLIC_VISIBILITY: False,
            },
            {
                assets_schema.TABLE_ID: 2,
                assets_schema.DATABASE_NAME: db,
                assets_schema.SCHEMA_NAME: "DATA_AD",
                assets_schema.ASSET_NAME: "CAMPAIGN_LEADS",
                assets_schema.ASSET_TYPE: "VIEW",
                assets_schema.DESCRIPTION: "Marketing leads",
                assets_schema.ROW_COUNT: 50,
                assets_schema.BYTES: 2048,
                assets_schema.TAGS: [_build_tag_ref("DATA_DOMAIN", "MARKETING")],
                assets_schema.CONTACT_STEWARD: "AD_STEWARD",
                assets_schema.CONTACT_SUPPORT: "AD_SUPPORT",
                assets_schema.CONTACT_ACCESS_APPROVAL: "AD_APPROVER",
                assets_schema.CONTACT_SECURITY_COMPLIANCE: "SECURITY",
                assets_schema.IS_PUBLIC_VISIBILITY: True,
            },
            {
                assets_schema.TABLE_ID: 3,
                assets_schema.DATABASE_NAME: db,
                assets_schema.SCHEMA_NAME: "DATA_SALES",
                assets_schema.ASSET_NAME: "CUSTOMERS",
                assets_schema.ASSET_TYPE: "DYNAMIC TABLE",
                assets_schema.DESCRIPTION: "Customer master",
                assets_schema.ROW_COUNT: 30,
                assets_schema.BYTES: 1024,
                assets_schema.TAGS: [_build_tag_ref("DATA_CATEGORY", "MASTER")],
                assets_schema.CONTACT_STEWARD: "DATA_STEWARD",
                assets_schema.CONTACT_SUPPORT: "DATA_SUPPORT",
                assets_schema.CONTACT_ACCESS_APPROVAL: "DATA_APPROVER",
                assets_schema.CONTACT_SECURITY_COMPLIANCE: "SECURITY",
                assets_schema.IS_PUBLIC_VISIBILITY: False,
            },
        ]
    )


def load_columns() -> pd.DataFrame:
    """Fake のカラムカタログを返す。"""
    columns_schema = schema.Columns
    db = _get_database_name()
    return pd.DataFrame(
        [
            {
                columns_schema.TABLE_ID: 1,
                columns_schema.DATABASE_NAME: db,
                columns_schema.SCHEMA_NAME: "DATA_SALES",
                columns_schema.TABLE_NAME: "ORDERS",
                columns_schema.COLUMN_NAME: "ORDER_ID",
                columns_schema.ORDINAL_POSITION: 1,
                columns_schema.DATA_TYPE: "NUMBER",
                columns_schema.DESCRIPTION: "Order identifier",
                columns_schema.TAGS: [],
                columns_schema.IS_PRIMARY_KEY: True,
                columns_schema.IS_UNIQUE_KEY: True,
                columns_schema.FOREIGN_KEYS: [],
                columns_schema.IS_NULLABLE: False,
                columns_schema.MASKING_POLICY_NAME: None,
            },
            {
                columns_schema.TABLE_ID: 1,
                columns_schema.DATABASE_NAME: db,
                columns_schema.SCHEMA_NAME: "DATA_SALES",
                columns_schema.TABLE_NAME: "ORDERS",
                columns_schema.COLUMN_NAME: "AMOUNT",
                columns_schema.ORDINAL_POSITION: 2,
                columns_schema.DATA_TYPE: "NUMBER",
                columns_schema.DESCRIPTION: "Order amount",
                columns_schema.TAGS: [_build_tag_ref("SENSITIVITY", "CONFIDENTIAL")],
                columns_schema.IS_PRIMARY_KEY: False,
                columns_schema.IS_UNIQUE_KEY: False,
                columns_schema.FOREIGN_KEYS: [],
                columns_schema.IS_NULLABLE: False,
                columns_schema.MASKING_POLICY_NAME: None,
            },
            {
                columns_schema.TABLE_ID: 2,
                columns_schema.DATABASE_NAME: db,
                columns_schema.SCHEMA_NAME: "DATA_AD",
                columns_schema.TABLE_NAME: "CAMPAIGN_LEADS",
                columns_schema.COLUMN_NAME: "EMAIL",
                columns_schema.ORDINAL_POSITION: 1,
                columns_schema.DATA_TYPE: "VARCHAR",
                columns_schema.DESCRIPTION: "Lead email address",
                columns_schema.TAGS: [_build_tag_ref("PII", "YES")],
                columns_schema.IS_PRIMARY_KEY: False,
                columns_schema.IS_UNIQUE_KEY: False,
                columns_schema.FOREIGN_KEYS: [],
                columns_schema.IS_NULLABLE: True,
                columns_schema.MASKING_POLICY_NAME: "MASK_EMAIL",
            },
            {
                columns_schema.TABLE_ID: 3,
                columns_schema.DATABASE_NAME: db,
                columns_schema.SCHEMA_NAME: "DATA_SALES",
                columns_schema.TABLE_NAME: "CUSTOMERS",
                columns_schema.COLUMN_NAME: "CUSTOMER_EMAIL",
                columns_schema.ORDINAL_POSITION: 1,
                columns_schema.DATA_TYPE: "VARCHAR",
                columns_schema.DESCRIPTION: "Customer email address",
                columns_schema.TAGS: [_build_tag_ref("PII", "YES")],
                columns_schema.IS_PRIMARY_KEY: False,
                columns_schema.IS_UNIQUE_KEY: False,
                columns_schema.FOREIGN_KEYS: [],
                columns_schema.IS_NULLABLE: True,
                columns_schema.MASKING_POLICY_NAME: "MASK_EMAIL",
            },
        ]
    )


def load_users() -> pd.DataFrame:
    """Fake のユーザーカタログを返す。"""
    users_schema = schema.Users
    return pd.DataFrame(
        [
            {
                users_schema.USER_NAME: "ALICE",
                users_schema.DISPLAY_NAME: "Alice Analytics",
                users_schema.USER_TYPE: "PERSON",
                users_schema.DISABLED: False,
            },
            {
                users_schema.USER_NAME: "BOB",
                users_schema.DISPLAY_NAME: "Bob Builder",
                users_schema.USER_TYPE: "PERSON",
                users_schema.DISABLED: False,
            },
            {
                users_schema.USER_NAME: "SVC_ETL",
                users_schema.DISPLAY_NAME: "ETL Service",
                users_schema.USER_TYPE: "SERVICE",
                users_schema.DISABLED: False,
            },
        ]
    )


def load_tags() -> pd.DataFrame:
    """Fake のタグカタログを返す。"""
    return pd.DataFrame(
        [
            _build_tag_row("DATA_CATEGORY", "MASTER", "データ資産の分類"),
            _build_tag_row("DATA_DOMAIN", "SALES", "業務ドメイン"),
            _build_tag_row("DATA_DOMAIN", "MARKETING", "業務ドメイン"),
            _build_tag_row("PII", "YES", "個人情報の有無"),
            _build_tag_row("SENSITIVITY", "CONFIDENTIAL", "機密度"),
        ]
    )


def load_asset_visibility() -> pd.DataFrame:
    """Fake の資産閲覧可否を返す。"""
    visibility_schema = schema.AssetVisibility
    db = _get_database_name()
    return pd.DataFrame(
        [
            {
                visibility_schema.USER_NAME: "ALICE",
                visibility_schema.TABLE_ID: 1,
                visibility_schema.DATABASE_NAME: db,
                visibility_schema.SCHEMA_NAME: "DATA_SALES",
                visibility_schema.ASSET_NAME: "ORDERS",
                visibility_schema.USER_ROLES: ["ANALYST"],
                visibility_schema.ASSET_ROLES: ["SALES_READER"],
            },
            {
                visibility_schema.USER_NAME: "BOB",
                visibility_schema.TABLE_ID: 2,
                visibility_schema.DATABASE_NAME: db,
                visibility_schema.SCHEMA_NAME: "DATA_AD",
                visibility_schema.ASSET_NAME: "CAMPAIGN_LEADS",
                visibility_schema.USER_ROLES: ["MARKETER"],
                visibility_schema.ASSET_ROLES: ["AD_READER"],
            },
        ]
    )


def load_access_edges() -> pd.DataFrame:
    """Fake のアクセス経路エッジを返す。"""
    edges_schema = schema.AccessEdges
    db = _get_database_name()
    return pd.DataFrame(
        [
            {
                edges_schema.SOURCE_NODE: "ALICE",
                edges_schema.SOURCE_TYPE: "USER",
                edges_schema.TARGET_NODE: "ANALYST",
                edges_schema.TARGET_TYPE: "ROLE",
                edges_schema.RELATION_TYPE: "USER_TO_ROLE",
                edges_schema.PRIVILEGE: None,
                edges_schema.GRANTED_ON: "ROLE",
            },
            {
                edges_schema.SOURCE_NODE: "ANALYST",
                edges_schema.SOURCE_TYPE: "ROLE",
                edges_schema.TARGET_NODE: "SALES_READER",
                edges_schema.TARGET_TYPE: "ROLE",
                edges_schema.RELATION_TYPE: "ROLE_TO_ROLE",
                edges_schema.PRIVILEGE: "USAGE",
                edges_schema.GRANTED_ON: "ROLE",
            },
            {
                edges_schema.SOURCE_NODE: "SALES_READER",
                edges_schema.SOURCE_TYPE: "ROLE",
                edges_schema.TARGET_NODE: f"{db}.DATA_SALES.ORDERS",
                edges_schema.TARGET_TYPE: "ASSET",
                edges_schema.RELATION_TYPE: "ROLE_TO_ASSET",
                edges_schema.PRIVILEGE: "SELECT",
                edges_schema.GRANTED_ON: "TABLE",
            },
            {
                edges_schema.SOURCE_NODE: "BOB",
                edges_schema.SOURCE_TYPE: "USER",
                edges_schema.TARGET_NODE: "MARKETER",
                edges_schema.TARGET_TYPE: "ROLE",
                edges_schema.RELATION_TYPE: "USER_TO_ROLE",
                edges_schema.PRIVILEGE: None,
                edges_schema.GRANTED_ON: "ROLE",
            },
            {
                edges_schema.SOURCE_NODE: "MARKETER",
                edges_schema.SOURCE_TYPE: "ROLE",
                edges_schema.TARGET_NODE: "AD_READER",
                edges_schema.TARGET_TYPE: "ROLE",
                edges_schema.RELATION_TYPE: "ROLE_TO_ROLE",
                edges_schema.PRIVILEGE: "USAGE",
                edges_schema.GRANTED_ON: "ROLE",
            },
            {
                edges_schema.SOURCE_NODE: "AD_READER",
                edges_schema.SOURCE_TYPE: "ROLE",
                edges_schema.TARGET_NODE: f"{db}.DATA_AD.CAMPAIGN_LEADS",
                edges_schema.TARGET_TYPE: "ASSET",
                edges_schema.RELATION_TYPE: "ROLE_TO_ASSET",
                edges_schema.PRIVILEGE: "SELECT",
                edges_schema.GRANTED_ON: "TABLE",
            },
        ]
    )

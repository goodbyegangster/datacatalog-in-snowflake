"""Snowflake 接続なしで画面を起動するための fake catalog provider."""

from __future__ import annotations

import pandas as pd

from catalog import schema

DB = "hogehoge"
TAG_SCHEMA = "TAG"


def _tag_ref(tag_name: str, tag_value: str) -> dict[str, str]:
    return {
        "TAG_DATABASE": DB,
        "TAG_SCHEMA": TAG_SCHEMA,
        "TAG_NAME": tag_name,
        "TAG_VALUE": tag_value,
    }


def _tag_row(tag_name: str, tag_value: str, tag_comment: str) -> dict[str, str]:
    return {
        "TAG_DATABASE": DB,
        "TAG_SCHEMA": TAG_SCHEMA,
        "TAG_NAME": tag_name,
        "TAG_VALUE": tag_value,
        "TAG_COMMENT": tag_comment,
    }


def load_assets() -> pd.DataFrame:
    A = schema.Assets
    return pd.DataFrame(
        [
            {
                A.TABLE_ID: 1,
                A.DATABASE_NAME: DB,
                A.SCHEMA_NAME: "DATA_SALES",
                A.ASSET_NAME: "ORDERS",
                A.ASSET_TYPE: "BASE TABLE",
                A.DESCRIPTION: "Sales order facts",
                A.ROW_COUNT: 120,
                A.BYTES: 4096,
                A.TAGS: [_tag_ref("DATA_DOMAIN", "SALES")],
                A.CONTACT_STEWARD: "DATA_STEWARD",
                A.CONTACT_SUPPORT: "DATA_SUPPORT",
                A.CONTACT_ACCESS_APPROVAL: "DATA_APPROVER",
                A.CONTACT_SECURITY_COMPLIANCE: "SECURITY",
                A.IS_PUBLIC_VISIBILITY: False,
            },
            {
                A.TABLE_ID: 2,
                A.DATABASE_NAME: DB,
                A.SCHEMA_NAME: "DATA_AD",
                A.ASSET_NAME: "CAMPAIGN_LEADS",
                A.ASSET_TYPE: "VIEW",
                A.DESCRIPTION: "Marketing leads",
                A.ROW_COUNT: 50,
                A.BYTES: 2048,
                A.TAGS: [_tag_ref("DATA_DOMAIN", "MARKETING")],
                A.CONTACT_STEWARD: "AD_STEWARD",
                A.CONTACT_SUPPORT: "AD_SUPPORT",
                A.CONTACT_ACCESS_APPROVAL: "AD_APPROVER",
                A.CONTACT_SECURITY_COMPLIANCE: "SECURITY",
                A.IS_PUBLIC_VISIBILITY: True,
            },
            {
                A.TABLE_ID: 3,
                A.DATABASE_NAME: DB,
                A.SCHEMA_NAME: "DATA_SALES",
                A.ASSET_NAME: "CUSTOMERS",
                A.ASSET_TYPE: "DYNAMIC TABLE",
                A.DESCRIPTION: "Customer master",
                A.ROW_COUNT: 30,
                A.BYTES: 1024,
                A.TAGS: [_tag_ref("DATA_CATEGORY", "MASTER")],
                A.CONTACT_STEWARD: "DATA_STEWARD",
                A.CONTACT_SUPPORT: "DATA_SUPPORT",
                A.CONTACT_ACCESS_APPROVAL: "DATA_APPROVER",
                A.CONTACT_SECURITY_COMPLIANCE: "SECURITY",
                A.IS_PUBLIC_VISIBILITY: False,
            },
        ]
    )


def load_columns() -> pd.DataFrame:
    C = schema.Columns
    return pd.DataFrame(
        [
            {
                C.TABLE_ID: 1,
                C.DATABASE_NAME: DB,
                C.SCHEMA_NAME: "DATA_SALES",
                C.TABLE_NAME: "ORDERS",
                C.COLUMN_NAME: "ORDER_ID",
                C.ORDINAL_POSITION: 1,
                C.DATA_TYPE: "NUMBER",
                C.DESCRIPTION: "Order identifier",
                C.TAGS: [],
                C.IS_PRIMARY_KEY: True,
                C.IS_UNIQUE_KEY: True,
                C.FOREIGN_KEYS: [],
                C.IS_NULLABLE: False,
                C.MASKING_POLICY_NAME: None,
            },
            {
                C.TABLE_ID: 1,
                C.DATABASE_NAME: DB,
                C.SCHEMA_NAME: "DATA_SALES",
                C.TABLE_NAME: "ORDERS",
                C.COLUMN_NAME: "AMOUNT",
                C.ORDINAL_POSITION: 2,
                C.DATA_TYPE: "NUMBER",
                C.DESCRIPTION: "Order amount",
                C.TAGS: [_tag_ref("SENSITIVITY", "CONFIDENTIAL")],
                C.IS_PRIMARY_KEY: False,
                C.IS_UNIQUE_KEY: False,
                C.FOREIGN_KEYS: [],
                C.IS_NULLABLE: False,
                C.MASKING_POLICY_NAME: None,
            },
            {
                C.TABLE_ID: 2,
                C.DATABASE_NAME: DB,
                C.SCHEMA_NAME: "DATA_AD",
                C.TABLE_NAME: "CAMPAIGN_LEADS",
                C.COLUMN_NAME: "EMAIL",
                C.ORDINAL_POSITION: 1,
                C.DATA_TYPE: "VARCHAR",
                C.DESCRIPTION: "Lead email address",
                C.TAGS: [_tag_ref("PII", "YES")],
                C.IS_PRIMARY_KEY: False,
                C.IS_UNIQUE_KEY: False,
                C.FOREIGN_KEYS: [],
                C.IS_NULLABLE: True,
                C.MASKING_POLICY_NAME: "MASK_EMAIL",
            },
            {
                C.TABLE_ID: 3,
                C.DATABASE_NAME: DB,
                C.SCHEMA_NAME: "DATA_SALES",
                C.TABLE_NAME: "CUSTOMERS",
                C.COLUMN_NAME: "CUSTOMER_EMAIL",
                C.ORDINAL_POSITION: 1,
                C.DATA_TYPE: "VARCHAR",
                C.DESCRIPTION: "Customer email address",
                C.TAGS: [_tag_ref("PII", "YES")],
                C.IS_PRIMARY_KEY: False,
                C.IS_UNIQUE_KEY: False,
                C.FOREIGN_KEYS: [],
                C.IS_NULLABLE: True,
                C.MASKING_POLICY_NAME: "MASK_EMAIL",
            },
        ]
    )


def load_users() -> pd.DataFrame:
    U = schema.Users
    return pd.DataFrame(
        [
            {U.USER_NAME: "ALICE", U.DISPLAY_NAME: "Alice Analytics", U.USER_TYPE: "PERSON", U.DISABLED: False},
            {U.USER_NAME: "BOB", U.DISPLAY_NAME: "Bob Builder", U.USER_TYPE: "PERSON", U.DISABLED: False},
            {U.USER_NAME: "SVC_ETL", U.DISPLAY_NAME: "ETL Service", U.USER_TYPE: "SERVICE", U.DISABLED: False},
        ]
    )


def load_tags() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _tag_row("DATA_CATEGORY", "MASTER", "データ資産の分類"),
            _tag_row("DATA_DOMAIN", "SALES", "業務ドメイン"),
            _tag_row("DATA_DOMAIN", "MARKETING", "業務ドメイン"),
            _tag_row("PII", "YES", "個人情報の有無"),
            _tag_row("SENSITIVITY", "CONFIDENTIAL", "機密度"),
        ]
    )


def load_asset_visibility() -> pd.DataFrame:
    V = schema.AssetVisibility
    return pd.DataFrame(
        [
            {
                V.USER_NAME: "ALICE",
                V.TABLE_ID: 1,
                V.DATABASE_NAME: DB,
                V.SCHEMA_NAME: "DATA_SALES",
                V.ASSET_NAME: "ORDERS",
                V.USER_ROLES: ["ANALYST"],
                V.ASSET_ROLES: ["SALES_READER"],
            },
            {
                V.USER_NAME: "BOB",
                V.TABLE_ID: 2,
                V.DATABASE_NAME: DB,
                V.SCHEMA_NAME: "DATA_AD",
                V.ASSET_NAME: "CAMPAIGN_LEADS",
                V.USER_ROLES: ["MARKETER"],
                V.ASSET_ROLES: ["AD_READER"],
            },
        ]
    )


def load_access_edges() -> pd.DataFrame:
    E = schema.AccessEdges
    return pd.DataFrame(
        [
            {
                E.SOURCE_NODE: "ALICE",
                E.SOURCE_TYPE: "USER",
                E.TARGET_NODE: "ANALYST",
                E.TARGET_TYPE: "ROLE",
                E.RELATION_TYPE: "USER_TO_ROLE",
                E.PRIVILEGE: None,
                E.GRANTED_ON: "ROLE",
            },
            {
                E.SOURCE_NODE: "ANALYST",
                E.SOURCE_TYPE: "ROLE",
                E.TARGET_NODE: "SALES_READER",
                E.TARGET_TYPE: "ROLE",
                E.RELATION_TYPE: "ROLE_TO_ROLE",
                E.PRIVILEGE: "USAGE",
                E.GRANTED_ON: "ROLE",
            },
            {
                E.SOURCE_NODE: "SALES_READER",
                E.SOURCE_TYPE: "ROLE",
                E.TARGET_NODE: f"{DB}.DATA_SALES.ORDERS",
                E.TARGET_TYPE: "ASSET",
                E.RELATION_TYPE: "ROLE_TO_ASSET",
                E.PRIVILEGE: "SELECT",
                E.GRANTED_ON: "TABLE",
            },
            {
                E.SOURCE_NODE: "BOB",
                E.SOURCE_TYPE: "USER",
                E.TARGET_NODE: "MARKETER",
                E.TARGET_TYPE: "ROLE",
                E.RELATION_TYPE: "USER_TO_ROLE",
                E.PRIVILEGE: None,
                E.GRANTED_ON: "ROLE",
            },
            {
                E.SOURCE_NODE: "MARKETER",
                E.SOURCE_TYPE: "ROLE",
                E.TARGET_NODE: "AD_READER",
                E.TARGET_TYPE: "ROLE",
                E.RELATION_TYPE: "ROLE_TO_ROLE",
                E.PRIVILEGE: "USAGE",
                E.GRANTED_ON: "ROLE",
            },
            {
                E.SOURCE_NODE: "AD_READER",
                E.SOURCE_TYPE: "ROLE",
                E.TARGET_NODE: f"{DB}.DATA_AD.CAMPAIGN_LEADS",
                E.TARGET_TYPE: "ASSET",
                E.RELATION_TYPE: "ROLE_TO_ASSET",
                E.PRIVILEGE: "SELECT",
                E.GRANTED_ON: "TABLE",
            },
        ]
    )

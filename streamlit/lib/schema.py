"""カタログ表のスキーマ定義（列名と行の型）。

各カタログ表について、列名を ``StrEnum``（1 表 = 1 クラス）で定数化し、行の型を
``TypedDict`` で記述する。UI / ロジック層は magic string ではなく列 Enum を用いて
DataFrame を参照する（例: ``df[Assets.ASSET_NAME]``）。

``StrEnum`` メンバーは str のサブクラスであり ``str(member) == member.value``。
DataFrame の列ラベルは Enum の値（= 文字列）と一致させる（``catalog._frame`` が保証する）。
列の並び・名称は design-model.md および dcm の refresh procedure と一致させること。
"""

from __future__ import annotations

from enum import StrEnum
from typing import TypedDict

# --- 配列列に含まれる object の型 ---------------------------------------------


class TagRef(TypedDict):
    """TAGS 列（ASSETS / COLUMNS）の 1 要素、および TAGS 表の 1 行。"""

    TAG_DATABASE: str
    TAG_SCHEMA: str
    TAG_NAME: str
    TAG_VALUE: str


class ForeignKeyRef(TypedDict):
    """COLUMNS.FOREIGN_KEYS 列の 1 要素（参照先）。"""

    REFERENCED_DATABASE: str
    REFERENCED_SCHEMA: str
    REFERENCED_TABLE: str
    REFERENCED_COLUMN: str


# --- CATALOG.ASSETS ----------------------------------------------------------


class Assets(StrEnum):
    TABLE_ID = "TABLE_ID"
    DATABASE_NAME = "DATABASE_NAME"
    SCHEMA_NAME = "SCHEMA_NAME"
    ASSET_NAME = "ASSET_NAME"
    ASSET_TYPE = "ASSET_TYPE"
    DESCRIPTION = "DESCRIPTION"
    ROW_COUNT = "ROW_COUNT"
    BYTES = "BYTES"
    TAGS = "TAGS"
    CONTACT_STEWARD = "CONTACT_STEWARD"
    CONTACT_SUPPORT = "CONTACT_SUPPORT"
    CONTACT_ACCESS_APPROVAL = "CONTACT_ACCESS_APPROVAL"
    CONTACT_SECURITY_COMPLIANCE = "CONTACT_SECURITY_COMPLIANCE"
    IS_PUBLIC_VISIBILITY = "IS_PUBLIC_VISIBILITY"


class AssetRow(TypedDict):
    TABLE_ID: int
    DATABASE_NAME: str
    SCHEMA_NAME: str
    ASSET_NAME: str
    ASSET_TYPE: str
    DESCRIPTION: str | None
    ROW_COUNT: int | None
    BYTES: int | None
    TAGS: list[TagRef]
    CONTACT_STEWARD: str | None
    CONTACT_SUPPORT: str | None
    CONTACT_ACCESS_APPROVAL: str | None
    CONTACT_SECURITY_COMPLIANCE: str | None
    IS_PUBLIC_VISIBILITY: bool


# --- CATALOG.COLUMNS ---------------------------------------------------------


class Columns(StrEnum):
    TABLE_ID = "TABLE_ID"
    DATABASE_NAME = "DATABASE_NAME"
    SCHEMA_NAME = "SCHEMA_NAME"
    TABLE_NAME = "TABLE_NAME"
    COLUMN_NAME = "COLUMN_NAME"
    ORDINAL_POSITION = "ORDINAL_POSITION"
    DATA_TYPE = "DATA_TYPE"
    DESCRIPTION = "DESCRIPTION"
    TAGS = "TAGS"
    IS_PRIMARY_KEY = "IS_PRIMARY_KEY"
    IS_UNIQUE_KEY = "IS_UNIQUE_KEY"
    FOREIGN_KEYS = "FOREIGN_KEYS"
    IS_NULLABLE = "IS_NULLABLE"
    MASKING_POLICY_NAME = "MASKING_POLICY_NAME"


class ColumnRow(TypedDict):
    TABLE_ID: int
    DATABASE_NAME: str
    SCHEMA_NAME: str
    TABLE_NAME: str
    COLUMN_NAME: str
    ORDINAL_POSITION: int
    DATA_TYPE: str
    DESCRIPTION: str | None
    TAGS: list[TagRef]
    IS_PRIMARY_KEY: bool
    IS_UNIQUE_KEY: bool
    FOREIGN_KEYS: list[ForeignKeyRef]
    IS_NULLABLE: bool
    MASKING_POLICY_NAME: str | None


# --- CATALOG.USERS -----------------------------------------------------------


class Users(StrEnum):
    USER_NAME = "USER_NAME"
    DISPLAY_NAME = "DISPLAY_NAME"
    USER_TYPE = "USER_TYPE"
    DISABLED = "DISABLED"


class UserRow(TypedDict):
    USER_NAME: str
    DISPLAY_NAME: str | None
    USER_TYPE: str
    DISABLED: bool


# --- CATALOG.TAGS ------------------------------------------------------------


class Tags(StrEnum):
    TAG_DATABASE = "TAG_DATABASE"
    TAG_SCHEMA = "TAG_SCHEMA"
    TAG_NAME = "TAG_NAME"
    TAG_VALUE = "TAG_VALUE"


# TAGS 表の 1 行は TagRef と同一形。
TagRow = TagRef


# --- CATALOG.ACCESS_EDGES ----------------------------------------------------


class AccessEdges(StrEnum):
    SOURCE_NODE = "SOURCE_NODE"
    SOURCE_TYPE = "SOURCE_TYPE"
    TARGET_NODE = "TARGET_NODE"
    TARGET_TYPE = "TARGET_TYPE"
    RELATION_TYPE = "RELATION_TYPE"
    PRIVILEGE = "PRIVILEGE"
    GRANTED_ON = "GRANTED_ON"


class AccessEdgeRow(TypedDict):
    SOURCE_NODE: str
    SOURCE_TYPE: str
    TARGET_NODE: str
    TARGET_TYPE: str
    RELATION_TYPE: str
    PRIVILEGE: str | None
    GRANTED_ON: str


# --- CATALOG.ASSET_VISIBILITY ------------------------------------------------


class AssetVisibility(StrEnum):
    USER_NAME = "USER_NAME"
    TABLE_ID = "TABLE_ID"
    DATABASE_NAME = "DATABASE_NAME"
    SCHEMA_NAME = "SCHEMA_NAME"
    ASSET_NAME = "ASSET_NAME"
    USER_ROLES = "USER_ROLES"
    ASSET_ROLES = "ASSET_ROLES"


class AssetVisibilityRow(TypedDict):
    USER_NAME: str
    TABLE_ID: int
    DATABASE_NAME: str
    SCHEMA_NAME: str
    ASSET_NAME: str
    USER_ROLES: list[str]
    ASSET_ROLES: list[str]

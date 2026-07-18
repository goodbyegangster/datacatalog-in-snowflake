"""カタログ DataFrame の列名と行型を定義する。

UI / ロジック層はこの module の StrEnum を使って列参照する。
"""

from __future__ import annotations

from enum import StrEnum
from typing import TypedDict

# --- list[dict] として扱う列の要素型 ------------------------------------------


class TagRef(TypedDict):
    """ASSETS.TAGS / COLUMNS.TAGS の 1 要素。"""

    TAG_DATABASE: str
    TAG_SCHEMA: str
    TAG_NAME: str
    TAG_VALUE: str


class ForeignKeyRef(TypedDict):
    """COLUMNS.FOREIGN_KEYS の 1 要素。"""

    REFERENCED_DATABASE: str
    REFERENCED_SCHEMA: str
    REFERENCED_TABLE: str
    REFERENCED_COLUMN: str


# --- CATALOG.ASSETS ----------------------------------------------------------


class Assets(StrEnum):
    """CATALOG.ASSETS の列名。"""

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
    """CATALOG.ASSETS の行型。"""

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
    """CATALOG.COLUMNS の列名。"""

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
    """CATALOG.COLUMNS の行型。"""

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
    """CATALOG.USERS の列名。"""

    USER_NAME = "USER_NAME"
    DISPLAY_NAME = "DISPLAY_NAME"
    USER_TYPE = "USER_TYPE"
    DISABLED = "DISABLED"


class UserRow(TypedDict):
    """CATALOG.USERS の行型。"""

    USER_NAME: str
    DISPLAY_NAME: str | None
    USER_TYPE: str
    DISABLED: bool


# --- CATALOG.TAGS ------------------------------------------------------------


class Tags(StrEnum):
    """CATALOG.TAGS の列名。"""

    TAG_DATABASE = "TAG_DATABASE"
    TAG_SCHEMA = "TAG_SCHEMA"
    TAG_NAME = "TAG_NAME"
    TAG_VALUE = "TAG_VALUE"
    TAG_COMMENT = "TAG_COMMENT"


class TagRow(TypedDict):
    """CATALOG.TAGS 表の 1 行。"""

    TAG_DATABASE: str
    TAG_SCHEMA: str
    TAG_NAME: str
    TAG_VALUE: str
    TAG_COMMENT: str | None


# --- CATALOG.ACCESS_EDGES ----------------------------------------------------


class AccessEdges(StrEnum):
    """CATALOG.ACCESS_EDGES の列名。"""

    SOURCE_NODE = "SOURCE_NODE"
    SOURCE_TYPE = "SOURCE_TYPE"
    TARGET_NODE = "TARGET_NODE"
    TARGET_TYPE = "TARGET_TYPE"
    RELATION_TYPE = "RELATION_TYPE"
    PRIVILEGE = "PRIVILEGE"
    GRANTED_ON = "GRANTED_ON"


class AccessEdgeRow(TypedDict):
    """CATALOG.ACCESS_EDGES の行型。"""

    SOURCE_NODE: str
    SOURCE_TYPE: str
    TARGET_NODE: str
    TARGET_TYPE: str
    RELATION_TYPE: str
    PRIVILEGE: str | None
    GRANTED_ON: str


# --- CATALOG.ASSET_VISIBILITY ------------------------------------------------


class AssetVisibility(StrEnum):
    """CATALOG.ASSET_VISIBILITY の列名。"""

    USER_NAME = "USER_NAME"
    TABLE_ID = "TABLE_ID"
    DATABASE_NAME = "DATABASE_NAME"
    SCHEMA_NAME = "SCHEMA_NAME"
    ASSET_NAME = "ASSET_NAME"
    USER_ROLES = "USER_ROLES"
    ASSET_ROLES = "ASSET_ROLES"


class AssetVisibilityRow(TypedDict):
    """CATALOG.ASSET_VISIBILITY の行型。"""

    USER_NAME: str
    TABLE_ID: int
    DATABASE_NAME: str
    SCHEMA_NAME: str
    ASSET_NAME: str
    USER_ROLES: list[str]
    ASSET_ROLES: list[str]

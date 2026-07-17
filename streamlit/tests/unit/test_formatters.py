# ruff: noqa: S101

from __future__ import annotations

from components.common import formatters


def test_format_roles_returns_empty_string_for_non_list() -> None:
    """list 以外は空文字を返す。"""
    assert formatters.format_roles("ANALYST") == ""


def test_format_roles_returns_sorted_roles() -> None:
    """ロール配列を昇順のカンマ区切りにする。"""
    assert formatters.format_roles(["SALES_READER", "ANALYST"]) == "ANALYST, SALES_READER"


def test_format_name_path_returns_dot_joined_parts() -> None:
    """名前の構成要素を dot 区切りにする。"""
    assert formatters.format_name_path(["DB", "SCHEMA", "TABLE", "COLUMN"]) == (
        "DB.SCHEMA.TABLE.COLUMN"
    )


def test_format_asset_fqn_returns_three_part_name() -> None:
    """データ資産 FQN を生成する。"""
    assert (
        formatters.format_asset_fqn(
            database_name="DB",
            schema_name="SCHEMA",
            asset_name="TABLE",
        )
        == "DB.SCHEMA.TABLE"
    )

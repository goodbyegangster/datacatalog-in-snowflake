"""Component 表示用の値整形 helper。"""

from __future__ import annotations

from collections.abc import Iterable


def format_roles(roles: object) -> str:
    """ロール配列を dataframe 表示向けに整形する。"""
    if not isinstance(roles, list) or not roles:
        return ""
    return ", ".join(sorted(str(role) for role in roles))


def format_name_path(parts: Iterable[object]) -> str:
    """名前の構成要素を dot 区切りの表示文字列へ整形する。"""
    return ".".join(str(part) for part in parts)


def format_asset_fqn(
    *,
    database_name: object,
    schema_name: object,
    asset_name: object,
) -> str:
    """データ資産の FQN を表示文字列へ整形する。"""
    return format_name_path([database_name, schema_name, asset_name])

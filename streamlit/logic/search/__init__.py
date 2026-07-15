"""検索・フィルタの純ロジック。

design-search.md の「page：データ資産」「page：ユーザー」の検索仕様を、Streamlit へ依存
しない純関数として実装する（ウィジェットや session_state は views 側が扱う）。DataFrame を
入力に受け、フィルタ済み DataFrame を返す。列参照は ``catalog.schema`` の StrEnum を用いる。
"""

from __future__ import annotations

from logic.search.assets import (
    AssetSearchCriteria,
    FreewordMatchReason,
    FreewordQuery,
    TagSelection,
    filter_assets,
    freeword_asset_ids,
    freeword_match_reasons,
    scope_databases,
    scope_schemas,
)
from logic.search.common import parse_freeword
from logic.search.users import UserFreewordQuery, filter_users

__all__ = [
    "AssetSearchCriteria",
    "FreewordQuery",
    "FreewordMatchReason",
    "TagSelection",
    "UserFreewordQuery",
    "filter_assets",
    "filter_users",
    "freeword_asset_ids",
    "freeword_match_reasons",
    "parse_freeword",
    "scope_databases",
    "scope_schemas",
]

"""ユーザー検索の純ロジック。"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from catalog import schema
from logic.search.common import parse_freeword


@dataclass
class UserFreewordQuery:
    """ユーザーのフリーワードと検索対象（名前 / 表示名）。"""

    freeword_text: str = ""
    is_user_name_search_target_enabled: bool = True
    is_display_name_search_target_enabled: bool = True


def filter_users(
    users: pd.DataFrame,
    freeword: UserFreewordQuery,
    current_user_filter_name: str | None = None,
) -> pd.DataFrame:
    """ユーザーを絞り込む。``current_user_filter_name`` 指定時は自ユーザーのみ。"""
    users_schema = schema.Users
    df = users
    if current_user_filter_name is not None:
        df = df[df[users_schema.USER_NAME] == current_user_filter_name]

    op, tokens = parse_freeword(freeword.freeword_text)
    if not tokens:
        return df

    def token_mask(token: str) -> pd.Series:
        """1 トークンに一致するユーザー行の mask を返す。"""
        needle = token.lower()
        mask = pd.Series(data=False, index=df.index)
        if freeword.is_user_name_search_target_enabled:
            mask |= (
                df[users_schema.USER_NAME].fillna("").str.lower().str.contains(needle, regex=False)
            )
        if freeword.is_display_name_search_target_enabled:
            mask |= (
                df[users_schema.DISPLAY_NAME]
                .fillna("")
                .str.lower()
                .str.contains(needle, regex=False)
            )
        return mask

    masks = [token_mask(t) for t in tokens]
    combined = masks[0]
    for m in masks[1:]:
        combined = combined | m if op == "or" else combined & m
    return df[combined]

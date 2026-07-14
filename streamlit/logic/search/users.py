"""ユーザー検索の純ロジック。"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from catalog import schema
from logic.search.common import parse_freeword


@dataclass
class UserFreewordQuery:
    """ユーザーのフリーワードと検索対象（名前 / 表示名）。"""

    text: str = ""
    target_user_name: bool = True
    target_display_name: bool = True


def filter_users(
    users: pd.DataFrame, freeword: UserFreewordQuery, only_user_name: str | None = None
) -> pd.DataFrame:
    """ユーザーを絞り込む。``only_user_name`` 指定時は自ユーザーのみ。"""
    U = schema.Users
    df = users
    if only_user_name is not None:
        df = df[df[U.USER_NAME] == only_user_name]

    op, tokens = parse_freeword(freeword.text)
    if not tokens:
        return df

    def token_mask(token: str) -> pd.Series:
        needle = token.lower()
        mask = pd.Series(False, index=df.index)
        if freeword.target_user_name:
            mask |= df[U.USER_NAME].fillna("").str.lower().str.contains(needle, regex=False)
        if freeword.target_display_name:
            mask |= df[U.DISPLAY_NAME].fillna("").str.lower().str.contains(needle, regex=False)
        return mask

    masks = [token_mask(t) for t in tokens]
    combined = masks[0]
    for m in masks[1:]:
        combined = combined | m if op == "or" else combined & m
    return df[combined]

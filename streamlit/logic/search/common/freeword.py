"""フリーワード検索条件の解析ロジック。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

FreewordOperator = Literal["and", "or"]


@dataclass(frozen=True)
class FreewordParseResult:
    """フリーワードを検索条件へ分解した結果。

    Attributes:
        operator: トークン同士の結合方法。``OR`` 指定時だけ ``"or"`` になる。
        tokens: 空白を除去した検索トークン。空ならフリーワード条件なしとして扱う。

    """

    operator: FreewordOperator
    tokens: list[str]


def parse_freeword(text: str) -> FreewordParseResult:
    """フリーワードを結合方法と検索トークンへ分解する。

    - `` OR `` を含む場合は OR 条件として分割する。
    - `` OR `` を含まず `` AND `` を含む場合は AND 条件として分割する。
    - どちらも含まない場合は、入力全体を 1 トークンの AND 条件として扱う。
    - 空文字または空白のみの場合は、フリーワード条件なしとして扱う。

    """
    text = (text or "").strip()
    if not text:
        return FreewordParseResult(operator="and", tokens=[])
    if " OR " in text:
        return FreewordParseResult(
            operator="or",
            tokens=[t.strip() for t in text.split(" OR ") if t.strip()],
        )
    if " AND " in text:
        return FreewordParseResult(
            operator="and",
            tokens=[t.strip() for t in text.split(" AND ") if t.strip()],
        )
    return FreewordParseResult(operator="and", tokens=[text])

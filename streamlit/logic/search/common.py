"""検索ロジック共通の小さな helper。"""

from __future__ import annotations


def parse_freeword(text: str) -> tuple[str, list[str]]:
    """フリーワードを (結合演算子, トークン列) に分解する。

    ` OR ` を含めば OR、無く ` AND ` を含めば AND、いずれも無ければ単一トークン（AND 扱い）。
    空文字・空白のみなら空トークン列（= 無制約）を返す。
    """
    text = (text or "").strip()
    if not text:
        return ("and", [])
    if " OR " in text:
        return ("or", [t.strip() for t in text.split(" OR ") if t.strip()])
    if " AND " in text:
        return ("and", [t.strip() for t in text.split(" AND ") if t.strip()])
    return ("and", [text])

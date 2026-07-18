"""カタログ DataFrame の変換処理を提供する。"""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from settings import DisplayScope


def filter_rows_by_display_scopes(
    df: pd.DataFrame,
    *,
    db_col: StrEnum,
    schema_col: StrEnum,
    display_scopes: Sequence[DisplayScope],
) -> pd.DataFrame:
    """DISPLAY_SCOPES に属する DB / スキーマの行だけを返す。"""
    scopes = {(s["DATABASE_NAME"], s["SCHEMA_NAME"]) for s in display_scopes}
    keys = pd.Series(list(zip(df[str(db_col)], df[str(schema_col)], strict=True)), index=df.index)
    return df[keys.isin(scopes)]

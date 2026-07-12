"""データ資産詳細の統計情報 tab component。"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from catalog import schema


def render(asset: pd.Series) -> None:
    """統計情報 tab を表示する。"""
    A = schema.Assets
    row_count = asset[A.ROW_COUNT]
    n_bytes = asset[A.BYTES]
    display = pd.DataFrame(
        [
            {"項目": "行数", "値": f"{int(row_count):,}" if pd.notna(row_count) else "-"},
            {
                "項目": "データサイズ (bytes)",
                "値": f"{int(n_bytes):,}" if pd.notna(n_bytes) else "-",
            },
        ]
    )
    st.dataframe(
        display,
        hide_index=True,
        width="stretch",
        column_config={
            "項目": st.column_config.TextColumn(width="medium"),
            "値": st.column_config.TextColumn(width="medium"),
        },
    )

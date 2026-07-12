"""データ資産ページの一覧 component。"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from catalog import schema
from runtime import state

RESULTS_KEY = "asset_table"

_COLUMN_CONFIG = {
    "データベース": st.column_config.TextColumn(width="small"),
    "スキーマ": st.column_config.TextColumn(width="small"),
    "名前": st.column_config.TextColumn(width="medium"),
    "オブジェクト種別": st.column_config.TextColumn(width="small"),
    "説明": st.column_config.TextColumn(width="large"),
}
_COMPACT_COLUMN_CONFIG = {
    "名前": st.column_config.TextColumn(width="medium"),
}


def clear_selection() -> None:
    """検索条件と整合しなくなった一覧/詳細の選択状態を解除する。"""
    st.session_state.pop(state.ASSET_SELECTED_TABLE_ID, None)
    st.session_state.pop(RESULTS_KEY, None)


def render(assets: pd.DataFrame, *, compact: bool = False) -> int | None:
    """データ資産一覧を表示し、選択中の TABLE_ID を返す。"""
    A = schema.Assets
    ordered = assets.sort_values([A.DATABASE_NAME, A.SCHEMA_NAME, A.ASSET_NAME]).reset_index(
        drop=True
    )

    if compact:
        display = pd.DataFrame({"名前": ordered[A.ASSET_NAME]}).reset_index(drop=True)
        column_config = _COMPACT_COLUMN_CONFIG
    else:
        display = pd.DataFrame(
            {
                "データベース": ordered[A.DATABASE_NAME],
                "スキーマ": ordered[A.SCHEMA_NAME],
                "名前": ordered[A.ASSET_NAME],
                "オブジェクト種別": ordered[A.ASSET_TYPE],
                "説明": ordered[A.DESCRIPTION],
            }
        ).reset_index(drop=True)
        column_config = _COLUMN_CONFIG

    event = st.dataframe(
        display,
        column_config=column_config,
        hide_index=True,
        height="auto",
        width="stretch",
        selection_mode="single-cell",
        on_select="rerun",
        key=RESULTS_KEY,
    )

    cells = event.selection.cells
    if cells and cells[0][0] < len(ordered):
        return int(ordered.iloc[cells[0][0]][A.TABLE_ID])
    return None

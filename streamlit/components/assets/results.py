"""データ資産ページの一覧 component。"""

from __future__ import annotations

from collections.abc import Mapping
from numbers import Integral

import pandas as pd
import streamlit as st

from catalog import schema
from logic.search import FreewordMatchReason
from runtime import state

RESULTS_KEY = "asset_table"

_COLUMN_CONFIG = {
    "データベース": st.column_config.TextColumn(width="small"),
    "スキーマ": st.column_config.TextColumn(width="small"),
    "名前": st.column_config.TextColumn(width="medium"),
    "オブジェクト種別": st.column_config.TextColumn(width="small"),
    "説明": st.column_config.TextColumn(width="large"),
    "フリーワード一致": st.column_config.TextColumn(width="large"),
}
_COMPACT_COLUMN_CONFIG = {
    "名前": st.column_config.TextColumn(width="medium"),
}


def _table_id_key(value: object) -> int:
    if isinstance(value, Integral):
        return int(value)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return int(str(value))


def _freeword_reason_text(table_id: object, reasons: Mapping[int, FreewordMatchReason]) -> str:
    return reasons.get(_table_id_key(table_id), FreewordMatchReason()).text


def clear_selection() -> None:
    """検索条件と整合しなくなった一覧/詳細の選択状態を解除する。"""
    st.session_state.pop(state.ASSET_SELECTED_TABLE_ID, None)
    st.session_state.pop(RESULTS_KEY, None)


def render(
    assets: pd.DataFrame,
    *,
    compact: bool = False,
    freeword_reasons: Mapping[int, FreewordMatchReason] | None = None,
) -> int | None:
    """データ資産一覧を表示し、選択中の TABLE_ID を返す。"""
    assets_schema = schema.Assets
    ordered = assets.sort_values(
        [assets_schema.DATABASE_NAME, assets_schema.SCHEMA_NAME, assets_schema.ASSET_NAME]
    ).reset_index(drop=True)
    reasons = freeword_reasons or {}

    if compact:
        display = pd.DataFrame({"名前": ordered[assets_schema.ASSET_NAME]}).reset_index(drop=True)
        column_config = _COMPACT_COLUMN_CONFIG
    else:
        display = pd.DataFrame(
            {
                "データベース": ordered[assets_schema.DATABASE_NAME],
                "スキーマ": ordered[assets_schema.SCHEMA_NAME],
                "名前": ordered[assets_schema.ASSET_NAME],
                "オブジェクト種別": ordered[assets_schema.ASSET_TYPE],
                "説明": ordered[assets_schema.DESCRIPTION],
                "フリーワード一致": ordered[assets_schema.TABLE_ID]
                .astype(int)
                .map(lambda table_id: _freeword_reason_text(table_id, reasons)),
            }
        ).reset_index(drop=True)
        column_config = _COLUMN_CONFIG

    st.caption(f"検索結果: {len(display)}")
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

    cells = event.get("selection", {}).get("cells", [])
    if cells and cells[0][0] < len(ordered):
        return int(ordered.iloc[cells[0][0]][assets_schema.TABLE_ID])
    return None

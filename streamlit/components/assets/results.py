"""データ資産ページの一覧 component。"""

from __future__ import annotations

from collections.abc import Mapping
from numbers import Integral

import pandas as pd
import streamlit as st

from catalog import schema
from components.common import dataframe_selection
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


def _convert_table_id_to_key(value: object) -> int:
    """TABLE_ID 値を一致理由 lookup 用の int key に変換する。"""
    if isinstance(value, Integral):
        return int(value)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return int(str(value))


def _get_freeword_reason_text(
    table_id: object,
    reasons: Mapping[int, FreewordMatchReason],
) -> str:
    """TABLE_ID に対応するフリーワード一致理由の表示文字列を返す。"""
    return reasons.get(_convert_table_id_to_key(table_id), FreewordMatchReason()).text


def clear_asset_selection() -> None:
    """選択中データ資産と一覧 widget の選択状態を解除する。"""
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
                .map(lambda table_id: _get_freeword_reason_text(table_id, reasons)),
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

    row_index = dataframe_selection.get_selected_row_index(event, len(ordered))
    if row_index is not None:
        return int(ordered.iloc[row_index][assets_schema.TABLE_ID])
    return None

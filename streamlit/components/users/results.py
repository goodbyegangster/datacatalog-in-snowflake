"""ユーザーページの一覧 component。"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from catalog import schema
from runtime import state

RESULTS_KEY = "user_table"

_COLUMN_CONFIG = {
    "名前": st.column_config.TextColumn(width="medium"),
    "表示名": st.column_config.TextColumn(width="large"),
    "タイプ": st.column_config.TextColumn(width="small"),
    "ステータス": st.column_config.TextColumn(width="small"),
}
_COMPACT_COLUMN_CONFIG = {
    "名前": st.column_config.TextColumn(width="medium"),
}


def clear_selection() -> None:
    """一覧/詳細の選択状態を解除する。"""
    st.session_state.pop(state.USER_SELECTED_NAME, None)
    st.session_state.pop(RESULTS_KEY, None)


def render(users: pd.DataFrame, *, compact: bool = False) -> str | None:
    """ユーザー一覧を表示し、選択中の USER_NAME を返す。"""
    U = schema.Users
    ordered = users.sort_values(U.USER_NAME).reset_index(drop=True)

    if compact:
        display = pd.DataFrame({"名前": ordered[U.USER_NAME]}).reset_index(drop=True)
        column_config = _COMPACT_COLUMN_CONFIG
    else:
        display = pd.DataFrame(
            {
                "名前": ordered[U.USER_NAME],
                "表示名": ordered[U.DISPLAY_NAME],
                "タイプ": ordered[U.USER_TYPE],
                "ステータス": ordered[U.DISABLED].map(lambda d: "無効" if d else "有効"),
            }
        ).reset_index(drop=True)
        column_config = _COLUMN_CONFIG

    event = st.dataframe(
        display,
        column_config=column_config,
        hide_index=True,
        height="stretch",
        width="stretch",
        selection_mode="single-cell",
        on_select="rerun",
        key=RESULTS_KEY,
    )

    cells = event.selection.cells
    if cells and cells[0][0] < len(ordered):
        return str(ordered.iloc[cells[0][0]][U.USER_NAME])
    return None

"""ユーザーページの一覧 component。"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from catalog import schema
from components.common import dataframe_selection
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
    users_schema = schema.Users
    ordered = users.sort_values(users_schema.USER_NAME).reset_index(drop=True)

    if compact:
        display = pd.DataFrame({"名前": ordered[users_schema.USER_NAME]}).reset_index(drop=True)
        column_config = _COMPACT_COLUMN_CONFIG
    else:
        display = pd.DataFrame(
            {
                "名前": ordered[users_schema.USER_NAME],
                "表示名": ordered[users_schema.DISPLAY_NAME],
                "タイプ": ordered[users_schema.USER_TYPE],
                "ステータス": ordered[users_schema.DISABLED].map(lambda d: "無効" if d else "有効"),
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
        return str(ordered.iloc[row_index][users_schema.USER_NAME])
    return None

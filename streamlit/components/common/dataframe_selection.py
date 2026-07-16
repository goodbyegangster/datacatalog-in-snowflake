"""dataframe の選択 event を扱う。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from streamlit.elements.arrow import DataframeState


def get_selected_row_index(event: DataframeState, row_count: int) -> int | None:
    """single-cell selection の選択行位置を返す。"""
    cells = event.get("selection", {}).get("cells", [])
    if not cells:
        return None

    row_index = cells[0][0]
    if row_index < 0 or row_index >= row_count:
        return None
    return int(row_index)

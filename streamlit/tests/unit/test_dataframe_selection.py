# ruff: noqa: S101

from __future__ import annotations

from typing import Any, cast

from components.common import dataframe_selection


def event_with_cells(cells: list[tuple[int, str]]) -> Any:
    """テスト用の dataframe selection event を返す。"""
    return {"selection": {"cells": cells}}


def test_get_selected_row_index_returns_none_when_no_cell_is_selected() -> None:
    """セル選択がない場合は None を返す。"""
    assert dataframe_selection.get_selected_row_index(event_with_cells([]), 3) is None


def test_get_selected_row_index_returns_selected_row_position() -> None:
    """セル選択がある場合は選択行位置を返す。"""
    assert dataframe_selection.get_selected_row_index(event_with_cells([(1, "名前")]), 3) == 1


def test_get_selected_row_index_returns_none_when_row_is_out_of_range() -> None:
    """選択行位置が行数外の場合は None を返す。"""
    assert dataframe_selection.get_selected_row_index(event_with_cells([(3, "名前")]), 3) is None


def test_get_selected_row_index_returns_none_when_row_is_negative() -> None:
    """選択行位置が負数の場合は None を返す。"""
    assert dataframe_selection.get_selected_row_index(event_with_cells([(-1, "名前")]), 3) is None


def test_get_selected_row_index_returns_none_without_selection_key() -> None:
    """selection key がない場合は None を返す。"""
    assert dataframe_selection.get_selected_row_index(cast("Any", {}), 3) is None

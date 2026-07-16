# ruff: noqa: S101

from __future__ import annotations

import streamlit as st

from runtime import navigation, state


def test_resolve_graph_target_returns_value_object() -> None:
    """graph 表示対象を値オブジェクトとして解決する。"""
    st.session_state[state.NAV_GRAPH_USER_NAME] = "ALICE"
    st.session_state[state.NAV_GRAPH_TABLE_ID] = "1"
    st.session_state[state.NAV_GRAPH_ASSET_FQN] = "DB.SCHEMA.ORDERS"

    target = navigation.resolve_graph_target()

    assert target == navigation.GraphTarget(
        user_name="ALICE",
        table_id=1,
        asset_fqn="DB.SCHEMA.ORDERS",
    )


def test_resolve_graph_target_returns_none_for_incomplete_state() -> None:
    """graph 表示対象が欠けている場合は None を返す。"""
    st.session_state[state.NAV_GRAPH_USER_NAME] = "ALICE"
    st.session_state[state.NAV_GRAPH_TABLE_ID] = "not-an-int"
    st.session_state[state.NAV_GRAPH_ASSET_FQN] = "DB.SCHEMA.ORDERS"

    assert navigation.resolve_graph_target() is None

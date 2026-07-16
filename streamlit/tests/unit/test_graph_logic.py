# ruff: noqa: S101

from __future__ import annotations

import pandas as pd

from catalog import schema
from logic import graph


def edge(source: str, target: str, relation_type: str, privilege: str | None = None) -> dict:
    """ACCESS_EDGES の 1 行を作る。"""
    edges_schema = schema.AccessEdges
    return {
        edges_schema.SOURCE_NODE: source,
        edges_schema.SOURCE_TYPE: "USER" if relation_type == "USER_TO_ROLE" else "ROLE",
        edges_schema.TARGET_NODE: target,
        edges_schema.TARGET_TYPE: "TABLE" if relation_type == "ROLE_TO_ASSET" else "ROLE",
        edges_schema.RELATION_TYPE: relation_type,
        edges_schema.PRIVILEGE: privilege,
        edges_schema.GRANTED_ON: "TABLE" if relation_type == "ROLE_TO_ASSET" else "ROLE",
    }


def test_build_user_asset_graph_returns_dot_for_reachable_asset() -> None:
    """到達可能な資産の経路と DOT を返す。"""
    edges = pd.DataFrame(
        [
            edge("ALICE", "ANALYST", "USER_TO_ROLE"),
            edge("ANALYST", "SALES_READER", "ROLE_TO_ROLE", "USAGE"),
            edge("SALES_READER", "DB.SCHEMA.ORDERS", "ROLE_TO_ASSET", "SELECT"),
        ]
    )

    result = graph.build_user_asset_graph(
        edges,
        user_name="ALICE",
        asset_fqn="DB.SCHEMA.ORDERS",
    )

    assert result.paths == [["ALICE", "ANALYST", "SALES_READER", "DB.SCHEMA.ORDERS"]]
    assert '"ALICE" -> "ANALYST"' in result.dot
    assert '"SALES_READER" -> "DB.SCHEMA.ORDERS" [label="SELECT"]' in result.dot
    assert 'label="凡例"' not in result.dot


def test_legend_dot_returns_node_legend() -> None:
    """凡例 DOT にユーザー、ロール、資産ノードを含める。"""
    result = graph.legend_dot()

    assert 'label="凡例"' in result
    assert "legend_user" in result
    assert 'label="ユーザー"' in result
    assert "shape=oval" in result
    assert 'fillcolor="#E3F2FD"' in result
    assert "legend_role" in result
    assert 'label="ロール"' in result
    assert 'fillcolor="white"' in result
    assert "legend_asset" in result
    assert 'label="データ資産"' in result
    assert 'fillcolor="#FFF3E0"' in result


def test_find_user_asset_paths_keeps_multiple_diamond_paths() -> None:
    """ダイヤモンド型の複数経路を維持する。"""
    edges = pd.DataFrame(
        [
            edge("ALICE", "ROLE_A", "USER_TO_ROLE"),
            edge("ROLE_A", "ROLE_B", "ROLE_TO_ROLE", "USAGE"),
            edge("ROLE_A", "ROLE_C", "ROLE_TO_ROLE", "USAGE"),
            edge("ROLE_B", "ROLE_D", "ROLE_TO_ROLE", "USAGE"),
            edge("ROLE_C", "ROLE_D", "ROLE_TO_ROLE", "USAGE"),
            edge("ROLE_D", "DB.SCHEMA.ORDERS", "ROLE_TO_ASSET", "SELECT"),
        ]
    )

    paths = graph.find_user_asset_paths(
        edges,
        user_name="ALICE",
        asset_fqn="DB.SCHEMA.ORDERS",
    )

    assert paths == [
        ["ALICE", "ROLE_A", "ROLE_B", "ROLE_D", "DB.SCHEMA.ORDERS"],
        ["ALICE", "ROLE_A", "ROLE_C", "ROLE_D", "DB.SCHEMA.ORDERS"],
    ]


def test_build_user_asset_graph_returns_empty_paths_when_unreachable() -> None:
    """到達不能な場合は空の経路を返す。"""
    edges = pd.DataFrame([edge("BOB", "ANALYST", "USER_TO_ROLE")])

    result = graph.build_user_asset_graph(
        edges,
        user_name="ALICE",
        asset_fqn="DB.SCHEMA.ORDERS",
    )

    assert result.paths == []
    assert '"ALICE"' in result.dot
    assert '"DB.SCHEMA.ORDERS"' in result.dot


def test_build_user_asset_graph_marks_path_limit_exceeded() -> None:
    """経路数上限を超えたことを返す。"""
    edges = pd.DataFrame(
        [
            edge("ALICE", "ROLE_A", "USER_TO_ROLE"),
            edge("ALICE", "ROLE_B", "USER_TO_ROLE"),
            edge("ROLE_A", "DB.SCHEMA.ORDERS", "ROLE_TO_ASSET", "SELECT"),
            edge("ROLE_B", "DB.SCHEMA.ORDERS", "ROLE_TO_ASSET", "SELECT"),
        ]
    )

    result = graph.build_user_asset_graph(
        edges,
        user_name="ALICE",
        asset_fqn="DB.SCHEMA.ORDERS",
        max_paths=1,
    )

    assert result.paths == [["ALICE", "ROLE_A", "DB.SCHEMA.ORDERS"]]
    assert result.path_limit_exceeded is True

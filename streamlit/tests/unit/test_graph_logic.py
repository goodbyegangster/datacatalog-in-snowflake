# ruff: noqa: S101

from __future__ import annotations

import pandas as pd

from catalog import schema
from logic import graph


def edge(source: str, target: str, relation_type: str, privilege: str | None = None) -> dict:
    E = schema.AccessEdges
    return {
        E.SOURCE_NODE: source,
        E.SOURCE_TYPE: "USER" if relation_type == "USER_TO_ROLE" else "ROLE",
        E.TARGET_NODE: target,
        E.TARGET_TYPE: "TABLE" if relation_type == "ROLE_TO_ASSET" else "ROLE",
        E.RELATION_TYPE: relation_type,
        E.PRIVILEGE: privilege,
        E.GRANTED_ON: "TABLE" if relation_type == "ROLE_TO_ASSET" else "ROLE",
    }


def test_build_user_asset_graph_returns_dot_for_reachable_asset() -> None:
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
    result = graph.legend_dot()

    assert 'label="凡例"' in result
    assert '"__legend_user__" [label="User", shape=oval' in result
    assert '"__legend_role__" [label="Role", shape=box' in result
    assert '"__legend_asset__" [label="Asset", shape=box' in result


def test_find_user_asset_paths_keeps_multiple_diamond_paths() -> None:
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
    edges = pd.DataFrame(
        [
            edge("ALICE", "ROLE_A", "USER_TO_ROLE"),
            edge("ALICE", "ROLE_B", "USER_TO_ROLE"),
            edge("ROLE_A", "DB.SCHEMA.ORDERS", "ROLE_TO_ASSET", "SELECT"),
            edge("ROLE_B", "DB.SCHEMA.ORDERS", "ROLE_TO_ASSET", "SELECT"),
        ]
    )

    paths, path_limit_exceeded = graph._find_user_asset_paths(
        edges,
        user_name="ALICE",
        asset_fqn="DB.SCHEMA.ORDERS",
        max_paths=1,
    )

    assert paths == [["ALICE", "ROLE_A", "DB.SCHEMA.ORDERS"]]
    assert path_limit_exceeded is True

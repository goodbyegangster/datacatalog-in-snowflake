"""ロール継承 graph の経路探索と DOT 生成。"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import pandas as pd

from lib import schema

GRAPH_RELATION_TYPES = {"USER_TO_ROLE", "ROLE_TO_ROLE", "ROLE_TO_ASSET"}


@dataclass(frozen=True)
class UserAssetGraph:
    """ユーザーからデータ資産までの経路探索結果。"""

    paths: list[list[str]]
    dot: str
    path_limit_exceeded: bool = False


def find_user_asset_paths(
    edges: pd.DataFrame,
    *,
    user_name: str,
    asset_fqn: str,
    max_depth: int = 50,
    max_paths: int = 500,
) -> list[list[str]]:
    """ACCESS_EDGES から user -> asset の全単純経路を探索する。"""
    paths, _ = _find_user_asset_paths(
        edges,
        user_name=user_name,
        asset_fqn=asset_fqn,
        max_depth=max_depth,
        max_paths=max_paths,
    )
    return paths


def _find_user_asset_paths(
    edges: pd.DataFrame,
    *,
    user_name: str,
    asset_fqn: str,
    max_depth: int = 50,
    max_paths: int = 500,
) -> tuple[list[list[str]], bool]:
    """ACCESS_EDGES から user -> asset の全単純経路を探索し、上限超過も返す。"""
    E = schema.AccessEdges
    usable = edges[edges[E.RELATION_TYPE].isin(GRAPH_RELATION_TYPES)]
    adjacency: dict[str, list[str]] = defaultdict(list)
    for row in usable.itertuples(index=False):
        source = str(getattr(row, E.SOURCE_NODE))
        target = str(getattr(row, E.TARGET_NODE))
        adjacency[source].append(target)

    for targets in adjacency.values():
        targets.sort()

    paths: list[list[str]] = []
    path_limit_exceeded = False

    def walk(node: str, path: list[str]) -> None:
        nonlocal path_limit_exceeded
        if len(paths) >= max_paths:
            path_limit_exceeded = True
            return
        if node == asset_fqn:
            paths.append(path.copy())
            return
        if len(path) >= max_depth:
            return

        for next_node in adjacency.get(node, []):
            if next_node in path:
                continue
            path.append(next_node)
            walk(next_node, path)
            path.pop()

    walk(user_name, [user_name])
    return paths, path_limit_exceeded


def build_user_asset_graph(
    edges: pd.DataFrame,
    *,
    user_name: str,
    asset_fqn: str,
) -> UserAssetGraph:
    """user -> asset の経路を DOT graph として返す。"""
    paths, path_limit_exceeded = _find_user_asset_paths(
        edges, user_name=user_name, asset_fqn=asset_fqn
    )
    return UserAssetGraph(
        paths=paths,
        dot=paths_to_dot(paths, user_name, asset_fqn, edges),
        path_limit_exceeded=path_limit_exceeded,
    )


def paths_to_dot(
    paths: list[list[str]],
    user_name: str,
    asset_fqn: str,
    edges: pd.DataFrame,
) -> str:
    """探索経路を Graphviz DOT へ変換する。"""
    E = schema.AccessEdges
    edge_labels = {
        (str(row[E.SOURCE_NODE]), str(row[E.TARGET_NODE])): str(row[E.PRIVILEGE] or "")
        for _, row in edges.iterrows()
    }
    graph_edges = {
        (path[index], path[index + 1]) for path in paths for index in range(len(path) - 1)
    }
    graph_nodes = {node for path in paths for node in path} | {user_name, asset_fqn}

    lines = [
        "digraph G {",
        "  rankdir=LR;",
        '  graph [fontname="sans-serif"];',
        '  node [shape=box, style="rounded,filled", fontname="sans-serif", fillcolor="white"];',
        '  edge [fontname="sans-serif"];',
    ]
    for node in sorted(graph_nodes):
        attrs = []
        if node == user_name:
            attrs.extend(["shape=oval", 'fillcolor="#E3F2FD"'])
        elif node == asset_fqn:
            attrs.extend(['fillcolor="#FFF3E0"'])
        attr_text = f" [{', '.join(attrs)}]" if attrs else ""
        lines.append(f'  "{_dot_escape(node)}"{attr_text};')

    for source, target in sorted(graph_edges):
        label = edge_labels.get((source, target), "")
        label_text = f' [label="{_dot_escape(label)}"]' if label else ""
        lines.append(f'  "{_dot_escape(source)}" -> "{_dot_escape(target)}"{label_text};')

    lines.append("}")
    return "\n".join(lines)


def _dot_escape(value: str) -> str:
    """DOT の quoted string 用に最低限のエスケープを行う。"""
    return value.replace("\\", "\\\\").replace('"', '\\"')

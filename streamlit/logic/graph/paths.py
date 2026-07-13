"""ACCESS_EDGES から user -> asset のロール継承経路を探索する。"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import pandas as pd

from catalog import schema
from logic.graph import dot_renderer

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
        dot=dot_renderer.paths_to_dot(paths, user_name, asset_fqn, edges),
        path_limit_exceeded=path_limit_exceeded,
    )

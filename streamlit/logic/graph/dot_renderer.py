"""ロール継承 graph の DOT 文字列を生成する。"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import pandas as pd
from jinja2 import Environment, PackageLoader, select_autoescape

from catalog import schema


@dataclass(frozen=True)
class DotNode:
    """DOT node の描画情報。"""

    id: str
    attrs: str = ""


@dataclass(frozen=True)
class DotEdge:
    """DOT edge の描画情報。"""

    source: str
    target: str
    attrs: str = ""


def paths_to_dot(
    paths: list[list[str]],
    user_name: str,
    asset_fqn: str,
    edges: pd.DataFrame,
) -> str:
    """探索経路を Graphviz DOT へ変換する。"""
    graph_edges = {
        (path[index], path[index + 1]) for path in paths for index in range(len(path) - 1)
    }
    graph_nodes = {node for path in paths for node in path} | {user_name, asset_fqn}

    return _render_template(
        "user_asset_graph.dot.j2",
        nodes=_user_asset_nodes(graph_nodes, user_name, asset_fqn),
        edges=_user_asset_edges(graph_edges, edges),
    )


def legend_dot() -> str:
    """ロール継承 graph の凡例を DOT として返す。"""
    return _render_template("legend.dot.j2")


def _user_asset_nodes(
    graph_nodes: set[str],
    user_name: str,
    asset_fqn: str,
) -> list[DotNode]:
    nodes: list[DotNode] = []
    for node in sorted(graph_nodes):
        attrs = ""
        if node == user_name:
            attrs = 'shape=oval, fillcolor="#E3F2FD"'
        elif node == asset_fqn:
            attrs = 'fillcolor="#FFF3E0"'
        nodes.append(DotNode(id=node, attrs=attrs))
    return nodes


def _user_asset_edges(
    graph_edges: set[tuple[str, str]],
    edges: pd.DataFrame,
) -> list[DotEdge]:
    E = schema.AccessEdges
    edge_labels = {
        (str(row[E.SOURCE_NODE]), str(row[E.TARGET_NODE])): str(row[E.PRIVILEGE] or "")
        for _, row in edges.iterrows()
    }
    dot_edges: list[DotEdge] = []
    for source, target in sorted(graph_edges):
        label = edge_labels.get((source, target), "")
        attrs = f'label={_dot_quote(label)}' if label else ""
        dot_edges.append(DotEdge(source=source, target=target, attrs=attrs))
    return dot_edges


def _render_template(template_name: str, **context: object) -> str:
    template = _template_environment().get_template(template_name)
    return template.render(**context).strip()


@lru_cache(maxsize=1)
def _template_environment() -> Environment:
    environment = Environment(
        loader=PackageLoader("logic.graph", "templates"),
        autoescape=select_autoescape(default=False),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.filters["dot_quote"] = _dot_quote
    return environment


def _dot_quote(value: str) -> str:
    """DOT の quoted string を返す。"""
    return f'"{_dot_escape(value)}"'


def _dot_escape(value: str) -> str:
    """DOT の quoted string 用に最低限のエスケープを行う。"""
    return value.replace("\\", "\\\\").replace('"', '\\"')

"""View ロール継承グラフ。"""

from __future__ import annotations

import streamlit as st

import styles
from catalog import provider as catalog
from logic import graph
from runtime import navigation
from views.common import error_handling


def _render_navigation_buttons(user_name: str, table_id: int) -> None:
    """対象の詳細ページへ戻るためのボタンを表示する。"""
    return_page = navigation.resolve_graph_return_page()
    left_col, right_col = st.columns(2)
    if return_page == "assets":
        with left_col:
            if st.button("データ資産に戻る", icon=":material/arrow_back:", width="stretch"):
                navigation.return_from_graph("assets", user_name=user_name, table_id=table_id)
        with right_col:
            if st.button("ユーザーを開く", icon=":material/person_search:", width="stretch"):
                navigation.open_user_page(user_name)
        return

    if return_page == "users":
        with left_col:
            if st.button("ユーザーに戻る", icon=":material/arrow_back:", width="stretch"):
                navigation.return_from_graph("users", user_name=user_name, table_id=table_id)
        with right_col:
            if st.button("データ資産を開く", icon=":material/table_view:", width="stretch"):
                navigation.open_asset_page(table_id)
        return

    with left_col:
        if st.button("ユーザーを開く", icon=":material/person_search:", width="stretch"):
            navigation.open_user_page(user_name)
    with right_col:
        if st.button("データ資産を開く", icon=":material/table_view:", width="stretch"):
            navigation.open_asset_page(table_id)


def main() -> None:
    """ロール継承グラフページを描画する。"""
    st.title("🌐 ロール継承グラフ", anchor=False)
    styles.render_base_css()
    styles.render_page_css("hide_sidebar.css")

    target = navigation.resolve_graph_target()
    if target is None:
        st.info("ロール継承グラフの表示対象が選択されていません。")
        return

    _render_navigation_buttons(target.user_name, target.table_id)
    st.markdown(f"**{target.user_name}** から **{target.asset_fqn}** までのロール継承")

    try:
        edges = catalog.load_access_edges()
    except Exception as exc:
        error_handling.render_catalog_load_error(exc)
        return

    result = graph.build_user_asset_graph(
        edges,
        user_name=target.user_name,
        asset_fqn=target.asset_fqn,
    )
    if result.path_limit_exceeded:
        st.warning("経路が多すぎるため表示できません。")
        return
    if not result.paths:
        st.warning("ロール継承 graph の経路が見つかりませんでした。")
        return

    st.caption(f"{len(result.paths)} 経路")
    st.graphviz_chart(result.dot, width="stretch")
    st.graphviz_chart(graph.legend_dot())


main()

"""page：ロール継承グラフ。

データ資産 / ユーザー画面から選択された user -> asset のロール継承経路を、
ページ全幅で表示する。ページ間の受け渡しは query parameter ではなく
``st.session_state`` に積まれた一時 state を利用する。
"""

from __future__ import annotations

import streamlit as st

import styles
from catalog import provider as catalog
from logic import graph
from runtime import state

RETURN_PAGE_PATHS = {
    "assets": "views/assets.py",
    "users": "views/users.py",
}


def _graph_target() -> tuple[str | None, int | None, str | None]:
    """session_state から graph 表示対象を取得する。"""
    user_name = st.session_state.get(state.NAV_GRAPH_USER_NAME)
    table_id = st.session_state.get(state.NAV_GRAPH_TABLE_ID)
    asset_fqn = st.session_state.get(state.NAV_GRAPH_ASSET_FQN)
    try:
        normalized_table_id = None if table_id is None else int(table_id)
    except (TypeError, ValueError):
        normalized_table_id = None
    return (
        None if user_name is None else str(user_name),
        normalized_table_id,
        None if asset_fqn is None else str(asset_fqn),
    )


def _return_page() -> str | None:
    """session_state から graph 表示元ページを取得する。"""
    value = st.session_state.get(state.NAV_GRAPH_RETURN_PAGE)
    if value not in RETURN_PAGE_PATHS:
        return None
    return str(value)


def _return_to_source(return_page: str, *, user_name: str, table_id: int) -> None:
    """graph 表示元ページへ戻る。"""
    if return_page == "assets":
        st.session_state[state.ASSET_SELECTED_TABLE_ID] = table_id
    elif return_page == "users":
        st.session_state[state.USER_SELECTED_NAME] = user_name
    st.switch_page(RETURN_PAGE_PATHS[return_page])


def _render_navigation_buttons(user_name: str, table_id: int) -> None:
    """対象の詳細ページへ戻るためのボタンを表示する。"""
    return_page = _return_page()
    left_col, right_col = st.columns(2)
    if return_page == "assets":
        with left_col:
            if st.button("データ資産に戻る", icon=":material/arrow_back:", width="stretch"):
                _return_to_source("assets", user_name=user_name, table_id=table_id)
        with right_col:
            if st.button("ユーザーを開く", icon=":material/person_search:", width="stretch"):
                st.session_state[state.NAV_TO_USER_NAME] = user_name
                st.switch_page("views/users.py")
        return

    if return_page == "users":
        with left_col:
            if st.button("ユーザーに戻る", icon=":material/arrow_back:", width="stretch"):
                _return_to_source("users", user_name=user_name, table_id=table_id)
        with right_col:
            if st.button("データ資産を開く", icon=":material/table_view:", width="stretch"):
                st.session_state[state.NAV_TO_TABLE_ID] = table_id
                st.switch_page("views/assets.py")
        return

    with left_col:
        if st.button("ユーザーを開く", icon=":material/person_search:", width="stretch"):
            st.session_state[state.NAV_TO_USER_NAME] = user_name
            st.switch_page("views/users.py")
    with right_col:
        if st.button("データ資産を開く", icon=":material/table_view:", width="stretch"):
            st.session_state[state.NAV_TO_TABLE_ID] = table_id
            st.switch_page("views/assets.py")


def main() -> None:
    st.title("🌐 ロール継承グラフ", anchor=False)
    styles.render_base_css()
    styles.render_page_css("hide_sidebar.css")

    user_name, table_id, asset_fqn = _graph_target()
    if user_name is None or table_id is None or asset_fqn is None:
        st.info("ロール継承グラフの表示対象が選択されていません。")
        return

    _render_navigation_buttons(user_name, table_id)
    st.markdown(f"**{user_name}** から **{asset_fqn}** までのロール継承")

    try:
        edges = catalog.load_access_edges()
    except Exception as exc:
        st.error(
            "データの取得に失敗しました。接続設定やカタログテーブルの生成状況をご確認ください。"
        )
        if catalog.data_mode() == "fake":
            st.exception(exc)
        return

    result = graph.build_user_asset_graph(edges, user_name=user_name, asset_fqn=asset_fqn)
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

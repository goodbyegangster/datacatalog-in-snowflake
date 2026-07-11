"""page：ユーザー。

design-view.md の「page：ユーザー」に対応。left pane（検索）と main pane（一覧 / 詳細）を
1:3 で配置し、行選択で main を 1:2 に分割して詳細ペインを表示する。初期は全ユーザー表示。

Step 1（画面ファースト）につき、検索 UI はプレースホルダ、データはモック。
実データ接続は Step 2、検索は Step 3、グラフは Step 4 で実装する。
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import catalog, schema, state


def render_search() -> None:
    """left pane：検索 UI（Step 1 はプレースホルダ）。"""
    st.subheader("検索")
    st.radio("表示範囲", options=["全ユーザー", "自ユーザー"], key="user_scope", disabled=True)
    st.text_input("フリーワード", key="user_freeword", placeholder="名前 / 表示名 で検索", disabled=True)
    st.caption("※ 検索機能は Step 3 で実装します。")


def render_table(users: pd.DataFrame) -> None:
    """main pane：一覧（st.dataframe）。行選択を session_state へ保存する。"""
    U = schema.Users
    ordered = users.sort_values(U.USER_NAME).reset_index(drop=True)

    display = pd.DataFrame(
        {
            "名前": ordered[U.USER_NAME],
            "表示名": ordered[U.DISPLAY_NAME],
            "タイプ": ordered[U.USER_TYPE],
            "ステータス": ordered[U.DISABLED].map(lambda d: "無効" if d else "有効"),
        }
    )

    event = st.dataframe(
        display,
        hide_index=True,
        width="stretch",
        selection_mode="single-row",
        on_select="rerun",
        key="user_table",
    )

    rows = event.selection.rows
    if rows:
        st.session_state[state.USER_SELECTED_NAME] = str(ordered.loc[rows[0], U.USER_NAME])


def render_detail(user_name: str, users: pd.DataFrame, visibility: pd.DataFrame,
                  edges: pd.DataFrame) -> None:
    """右カラム：シングル：ユーザーの詳細ペイン。"""
    U = schema.Users
    match = users[users[U.USER_NAME] == user_name]
    if match.empty:
        st.error("選択されたユーザーが見つかりませんでした。")
        return
    user = match.iloc[0]

    # --- 詳細ペイン上部 ---
    st.subheader(user[U.USER_NAME])
    st.text(f"表示名: {user[U.DISPLAY_NAME] or ''}")
    st.text(f"タイプ: {user[U.USER_TYPE]}")
    st.text(f"ステータス: {'無効' if user[U.DISABLED] else '有効'}")

    # --- 詳細ペイン下部：付与ロール / 閲覧可能なデータ資産 ---
    E = schema.AccessEdges
    direct_roles = sorted(
        edges[(edges[E.SOURCE_NODE] == user_name) & (edges[E.RELATION_TYPE] == "USER_TO_ROLE")][
            E.TARGET_NODE
        ].tolist()
    )
    st.text(f"直接付与ロール: {', '.join(direct_roles)}")

    V = schema.AssetVisibility
    vis = visibility[visibility[V.USER_NAME] == user_name]
    st.markdown("**閲覧可能なデータ資産**")
    if vis.empty:
        st.caption("閲覧可能なデータ資産がありません。")
    else:
        st.dataframe(
            vis[[V.DATABASE_NAME, V.SCHEMA_NAME, V.ASSET_NAME, V.USER_ROLES]].rename(
                columns={
                    V.DATABASE_NAME: "データベース",
                    V.SCHEMA_NAME: "スキーマ",
                    V.ASSET_NAME: "名前",
                    V.USER_ROLES: "起点ロール",
                }
            ),
            hide_index=True,
            width="stretch",
        )
    st.button("ロール継承グラフを表示", disabled=True, help="Step 4 で実装します。")


def main() -> None:
    st.title("👤 ユーザー")

    left, main_pane = st.columns([1, 3])
    with left:
        render_search()

    with main_pane:
        try:
            users = catalog.load_users()
            visibility = catalog.load_asset_visibility()
            edges = catalog.load_access_edges()
        except Exception:  # traceback は出さず日本語メッセージのみ表示する
            st.error("データの取得に失敗しました。接続設定やカタログテーブルの生成状況をご確認ください。")
            return

        selected = st.session_state.get(state.USER_SELECTED_NAME)
        if selected is None:
            render_table(users)
        else:
            list_col, detail_col = st.columns([1, 2])
            with list_col:
                render_table(users)
            with detail_col:
                render_detail(selected, users, visibility, edges)


main()

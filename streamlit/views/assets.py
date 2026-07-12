"""page：データ資産。

design-view.md の「page：データ資産」に対応。検索 UI は sidebar に配置し、本文側に
一覧 / 詳細を表示する。検索仕様は design-search.md、検索ロジックは ``lib.search`` を参照。

初期状態は一覧を空欄表示とし、検索入力に応じてインタラクティブに結果を表示する。
ユーザータブでは、行選択後のボタン操作でロール継承グラフを表示する。
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.assets import detail as asset_detail
from components.assets import search as asset_search
from components.assets import table as asset_table
from components.shared.styles import loader as styles
from catalog import provider as catalog
from catalog import schema
from lib import search, state


def _render_base_css() -> None:
    """全ページ共通 CSS を適用する。"""
    styles.render_base_css()


def _consume_nav_to_table_id(assets: pd.DataFrame) -> int | None:
    """ページ間遷移で指定されたデータ資産 ID を取り出し、存在する場合のみ返す。"""
    table_id = st.session_state.pop(state.NAV_TO_TABLE_ID, None)
    if table_id is None:
        return None
    try:
        normalized = int(table_id)
    except (TypeError, ValueError):
        return None

    A = schema.Assets
    if normalized in set(assets[A.TABLE_ID].astype(int).tolist()):
        st.session_state[state.ASSET_SELECTED_TABLE_ID] = normalized
        return normalized
    return None


def main() -> None:
    st.title("🗂️ データ資産", anchor=False)
    _render_base_css()

    main_pane = st.container()

    try:
        assets = catalog.load_assets()
        columns = catalog.load_columns()
        tags = catalog.load_tags()
        visibility = catalog.load_asset_visibility()
    except Exception as exc:
        with main_pane:
            st.error(
                "データの取得に失敗しました。接続設定やカタログテーブルの生成状況をご確認ください。"
            )
            if catalog.data_mode() == "fake":
                st.exception(exc)
        return

    nav_table_id = _consume_nav_to_table_id(assets)

    with st.sidebar:
        criteria = asset_search.render(assets, tags)

    with main_pane:
        if not asset_search.has_condition(criteria):
            previous_search = st.session_state.get(state.ASSET_SEARCH_FINGERPRINT) is not None
            selected_table_id = st.session_state.get(state.ASSET_SELECTED_TABLE_ID)
            if nav_table_id is not None:
                st.session_state.pop(state.ASSET_SEARCH_FINGERPRINT, None)
                st.session_state[state.ASSET_SELECTED_TABLE_ID] = nav_table_id
                selected_table_id = nav_table_id
                previous_search = False

            if selected_table_id is not None and not previous_search:
                list_col, detail_col = st.columns([1, 3])
                with list_col:
                    st.info("検索条件が未指定のため、一覧は非表示です。")
                with detail_col:
                    asset_detail.render(selected_table_id, assets, columns, visibility)
            else:
                asset_table.clear_selection()
                st.session_state.pop(state.ASSET_SEARCH_FINGERPRINT, None)
                st.info("サイドバーの検索条件を指定すると、一覧が表示されます。")
            return

        search_fingerprint = asset_search.fingerprint(criteria)
        if st.session_state.get(state.ASSET_SEARCH_FINGERPRINT) != search_fingerprint:
            asset_table.clear_selection()
            st.session_state[state.ASSET_SEARCH_FINGERPRINT] = search_fingerprint

        filtered = search.filter_assets(assets, columns, criteria)
        if filtered.empty:
            asset_table.clear_selection()
            st.info("該当するデータ資産がありません。検索条件を変更してください。")
            return

        prior = st.session_state.get(state.ASSET_SELECTED_TABLE_ID)
        if prior is None:
            selected_now = asset_table.render(filtered)
        else:
            list_col, detail_col = st.columns([1, 3])
            with list_col:
                selected_now = asset_table.render(filtered, compact=True)
            with detail_col:
                asset_detail.render(prior, assets, columns, visibility)

        # 選択セルがない rerun は、詳細ペイン内の操作でも発生するため既存詳細を維持する。
        if selected_now is not None and selected_now != prior:
            st.session_state[state.ASSET_SELECTED_TABLE_ID] = selected_now
            st.rerun()


main()

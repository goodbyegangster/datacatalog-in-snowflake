"""View データ資産。"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

import styles
from catalog import provider as catalog
from catalog import schema
from components.assets import detail as asset_detail
from components.assets import results as asset_results
from components.assets import search as asset_search
from logic import search
from runtime import state
from views.common import error_handling


@dataclass(frozen=True)
class AssetCatalogData:
    """データ資産ページで利用するカタログデータ。"""

    assets: pd.DataFrame
    columns: pd.DataFrame
    tags: pd.DataFrame
    visibility: pd.DataFrame


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

    assets_schema = schema.Assets
    if normalized in set(assets[assets_schema.TABLE_ID].astype(int).tolist()):
        st.session_state[state.ASSET_SELECTED_TABLE_ID] = normalized
        return normalized
    return None


def _load_catalog_data() -> AssetCatalogData | None:
    try:
        assets = catalog.load_assets()
        columns = catalog.load_columns()
        tags = catalog.load_tags()
        visibility = catalog.load_asset_visibility()
    except Exception as exc:
        error_handling.render_catalog_load_error(exc)
        return None
    return AssetCatalogData(
        assets=assets,
        columns=columns,
        tags=tags,
        visibility=visibility,
    )


def _render_without_condition(
    nav_table_id: int | None,
    assets: pd.DataFrame,
    columns: pd.DataFrame,
    visibility: pd.DataFrame,
) -> None:
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
        asset_results.clear_selection()
        st.session_state.pop(state.ASSET_SEARCH_FINGERPRINT, None)
        st.info("サイドバーの検索条件を指定すると、一覧が表示されます。")


def _render_filtered_assets(
    assets: pd.DataFrame,
    columns: pd.DataFrame,
    visibility: pd.DataFrame,
    criteria: search.AssetSearchCriteria,
) -> None:
    search_fingerprint = asset_search.fingerprint(criteria)
    if st.session_state.get(state.ASSET_SEARCH_FINGERPRINT) != search_fingerprint:
        asset_results.clear_selection()
        st.session_state[state.ASSET_SEARCH_FINGERPRINT] = search_fingerprint

    filtered = search.filter_assets(assets, columns, criteria)
    if filtered.empty:
        asset_results.clear_selection()
        st.info("該当するデータ資産がありません。検索条件を変更してください。")
        return

    freeword_reasons = search.freeword_match_reasons(criteria.freeword, assets, columns)
    prior = st.session_state.get(state.ASSET_SELECTED_TABLE_ID)
    if prior is None:
        selected_now = asset_results.render(filtered, freeword_reasons=freeword_reasons)
    else:
        list_col, detail_col = st.columns([1, 3])
        with list_col:
            selected_now = asset_results.render(
                filtered,
                compact=True,
                freeword_reasons=freeword_reasons,
            )
        with detail_col:
            asset_detail.render(prior, assets, columns, visibility)

    # 選択セルがない rerun は、詳細ペイン内の操作でも発生するため既存詳細を維持する。
    if selected_now is not None and selected_now != prior:
        st.session_state[state.ASSET_SELECTED_TABLE_ID] = selected_now
        st.rerun()


def main() -> None:
    """データ資産ページを描画する。"""
    st.title("🗂️ データ資産", anchor=False)
    _render_base_css()

    main_pane = st.container()
    with main_pane:
        catalog_data = _load_catalog_data()
    if catalog_data is None:
        return

    nav_table_id = _consume_nav_to_table_id(catalog_data.assets)

    with st.sidebar:
        criteria = asset_search.render(catalog_data.assets, catalog_data.tags)

    with main_pane:
        if not asset_search.has_condition(criteria):
            _render_without_condition(
                nav_table_id,
                catalog_data.assets,
                catalog_data.columns,
                catalog_data.visibility,
            )
            return
        _render_filtered_assets(
            catalog_data.assets,
            catalog_data.columns,
            catalog_data.visibility,
            criteria,
        )


main()

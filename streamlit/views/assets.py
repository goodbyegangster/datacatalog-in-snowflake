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


def _get_nav_table_id_to_show(assets: pd.DataFrame) -> int | None:
    """遷移元から指定された表示対象のデータ資産 ID を返す。

    取得した NAV_TO_TABLE_ID は session_state から削除する。
    """
    table_id = st.session_state.pop(state.NAV_TO_TABLE_ID, None)
    if table_id is None:
        return None
    try:
        normalized = int(table_id)
    except (TypeError, ValueError):
        return None

    assets_schema = schema.Assets
    if normalized in set(assets[assets_schema.TABLE_ID].astype(int).tolist()):
        return normalized
    return None


def _load_catalog_data() -> AssetCatalogData | None:
    """データ資産ページで利用するカタログデータを読み込む。"""
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


def _render_assets_without_search_condition(
    *,
    nav_table_id: int | None,
    catalog_data: AssetCatalogData,
) -> None:
    """検索条件未指定時に、遷移指定または既存選択がある場合は詳細を表示し、なければ案内を表示する。"""
    has_active_search_fingerprint = st.session_state.get(state.ASSET_SEARCH_FINGERPRINT) is not None
    selected_table_id: int | None = st.session_state.get(state.ASSET_SELECTED_TABLE_ID)
    if nav_table_id is not None:
        st.session_state.pop(state.ASSET_SEARCH_FINGERPRINT, None)
        selected_table_id = nav_table_id
        has_active_search_fingerprint = False

    should_show_selected_asset_detail = (
        selected_table_id is not None and not has_active_search_fingerprint
    )
    if should_show_selected_asset_detail and selected_table_id is not None:
        list_col, detail_col = st.columns([1, 3])
        with list_col:
            st.info("検索条件が未指定のため、一覧は非表示です。")
        with detail_col:
            asset_detail.render(
                selected_table_id,
                catalog_data.assets,
                catalog_data.columns,
                catalog_data.visibility,
            )
    else:
        asset_results.clear_asset_selection()
        st.session_state.pop(state.ASSET_SEARCH_FINGERPRINT, None)
        st.info("サイドバーの検索条件を指定すると、一覧が表示されます。")


def _clear_selection_when_search_changed(criteria: search.AssetSearchCriteria) -> None:
    """検索条件変更時に選択状態を解除する。"""
    search_fingerprint = asset_search.build_fingerprint(criteria)
    if st.session_state.get(state.ASSET_SEARCH_FINGERPRINT) != search_fingerprint:
        asset_results.clear_asset_selection()
        st.session_state[state.ASSET_SEARCH_FINGERPRINT] = search_fingerprint


def _rerun_when_selection_changed(selected_now: int | None, prior: int | None) -> None:
    """選択データ資産が変わった場合に詳細ペインを更新する。"""
    # 詳細ペイン内の操作でも selected_now は None になり得るため、既存詳細を維持する。
    if selected_now is not None and selected_now != prior:
        st.session_state[state.ASSET_SELECTED_TABLE_ID] = selected_now
        st.rerun()


def _render_assets_with_detail(
    *,
    filtered: pd.DataFrame,
    catalog_data: AssetCatalogData,
    criteria: search.AssetSearchCriteria,
) -> None:
    """データ資産検索結果と選択データ資産の詳細を表示する。"""
    freeword_reasons = search.build_freeword_match_reasons(
        criteria.freeword,
        catalog_data.assets,
        catalog_data.columns,
    )
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
            asset_detail.render(
                prior,
                catalog_data.assets,
                catalog_data.columns,
                catalog_data.visibility,
            )

    _rerun_when_selection_changed(selected_now, prior)


def _render_filtered_assets(
    *,
    catalog_data: AssetCatalogData,
    criteria: search.AssetSearchCriteria,
) -> None:
    """検索条件に一致するデータ資産一覧と詳細を表示する。"""
    filtered = search.filter_assets(
        assets=catalog_data.assets,
        columns=catalog_data.columns,
        criteria=criteria,
    )
    if filtered.empty:
        asset_results.clear_asset_selection()
        st.info("該当するデータ資産がありません。検索条件を変更してください。")
        return

    _render_assets_with_detail(
        filtered=filtered,
        catalog_data=catalog_data,
        criteria=criteria,
    )


def main() -> None:
    """データ資産ページを描画する。"""
    st.title("🗂️ データ資産", anchor=False)
    _render_base_css()

    main_pane = st.container()
    with main_pane:
        catalog_data = _load_catalog_data()
    if catalog_data is None:
        return

    with st.sidebar:
        criteria = asset_search.render(catalog_data.assets, catalog_data.tags)

    has_search_condition = asset_search.has_search_condition(criteria)
    if has_search_condition:
        _clear_selection_when_search_changed(criteria)

    nav_table_id = _get_nav_table_id_to_show(catalog_data.assets)
    if nav_table_id is not None:
        st.session_state[state.ASSET_SELECTED_TABLE_ID] = nav_table_id

    with main_pane:
        if not has_search_condition:
            _render_assets_without_search_condition(
                nav_table_id=nav_table_id,
                catalog_data=catalog_data,
            )
            return
        _render_filtered_assets(
            catalog_data=catalog_data,
            criteria=criteria,
        )


main()

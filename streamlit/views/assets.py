"""page：データ資産。

design-view.md の「page：データ資産」に対応。left pane（検索）と main pane（一覧 / 詳細）を
1:3 で配置し、行選択で main を 1:2 に分割して詳細ペインを表示する。検索仕様は
design-search.md、検索ロジックは ``lib.search`` を参照。

初期状態は一覧を空欄表示とし、「検索」押下で結果を表示する（design-view 準拠）。
グラフ表示は Step 4 で実装する。
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import catalog, schema, search, state
from lib.connection import get_session
from lib.search import AssetSearchCriteria, FreewordQuery, TagSelection
from settings import SELECTABLE_TAG_KEYS

PAGE_SIZE = 100

# 一覧テーブルの行選択ウィジェットの key（閉じる際に選択状態も解除するため定数化）。
_ASSET_TABLE_KEY = "asset_table"

# 一覧の列表示設定（列幅）。キーは表示用 DataFrame の列名と一致させる。
_ASSET_COLUMN_CONFIG = {
    "データベース": st.column_config.TextColumn(width="small"),
    "スキーマ": st.column_config.TextColumn(width="small"),
    "名前": st.column_config.TextColumn(width="medium"),
    "種別": st.column_config.TextColumn(width="small"),
    "説明": st.column_config.TextColumn(width="large"),
}


def _fmt_tags(tags: list[dict]) -> str:
    """TAGS 列（object の list）を表示用の文字列へ整形する。"""
    if not isinstance(tags, list) or not tags:
        return ""
    return ", ".join(f"{t['TAG_NAME']}={t['TAG_VALUE']}" for t in tags)


def _tag_allowed_values(tags: pd.DataFrame, tag_key: dict) -> list[str]:
    """TAGS マスターから、指定タグの allowed_values を取得する。"""
    T = schema.Tags
    mask = (
        (tags[T.TAG_DATABASE] == tag_key["DATABASE_NAME"])
        & (tags[T.TAG_SCHEMA] == tag_key["SCHEMA_NAME"])
        & (tags[T.TAG_NAME] == tag_key["TAG_NAME"])
    )
    return sorted(tags.loc[mask, T.TAG_VALUE].tolist())


def _nonce() -> int:
    """検索ウィジェットのキー世代。"""
    return st.session_state.get(state.ASSET_SEARCH_NONCE, 0)


def _wk(base: str) -> str:
    """世代付きウィジェットキー（クリア時に世代が変わり、確実にリセットされる）。"""
    return f"{base}__{_nonce()}"


def _on_database_change() -> None:
    """DB 選択変更時、（親に依存する）スキーマ選択を未選択へリセットする。"""
    st.session_state[_wk(state.SEARCH_ASSET_SCHEMAS)] = []


def _clear_search() -> None:
    """検索入力を全クリアする。キー世代を進めることで全ウィジェットを初期化する。"""
    st.session_state[state.ASSET_SEARCH_NONCE] = _nonce() + 1
    st.session_state[state.ASSET_SELECTED_TABLE_ID] = None
    st.session_state.pop(_ASSET_TABLE_KEY, None)
    # アコーディオンの開閉ラッチも閉じる
    for latch in (
        state.ASSET_EXPANDED_HIERARCHY,
        state.ASSET_EXPANDED_TYPE,
        state.ASSET_EXPANDED_TAG,
    ):
        st.session_state.pop(latch, None)


def _render_combine_control(key: str) -> None:
    """カテゴリ間の結合（AND=必須 / OR=いずれか）を選ぶセグメントコントロール。"""
    st.segmented_control(
        "他カテゴリとの結合", ["AND", "OR"], default="AND", key=key,
        help="AND = このカテゴリを必須にする / OR = OR 指定カテゴリのいずれかを満たせばよい",
    )


def _op_is_or(key: str) -> bool:
    return st.session_state.get(key) == "OR"


def _latched_expanded(latch_key: str, *, has_selection: bool) -> bool:
    """アコーディオンの開閉。選択が入ったら開いたまま保持し、解除では閉じない。"""
    if has_selection:
        st.session_state[latch_key] = True
    return st.session_state.get(latch_key, False)


def has_search_condition(criteria: AssetSearchCriteria) -> bool:
    """いずれかの検索条件が入力/選択されているか（初期空欄判定に用いる）。"""
    return bool(
        criteria.freeword.text.strip()
        or criteria.selected_databases
        or criteria.selected_schemas
        or criteria.selected_types
        or any(t.selected for t in criteria.tag_selections)
    )


def render_search(assets: pd.DataFrame, tags: pd.DataFrame) -> AssetSearchCriteria:
    """left pane：検索 UI。ウィジェットを描画し、現在の検索条件を返す。"""
    st.button("入力をクリア", on_click=_clear_search, width="stretch")

    # カテゴリ1：フリーワード
    with st.container(border=True):
        st.markdown("**フリーワード**")
        st.text_input(
            "キーワード", key=_wk(state.SEARCH_ASSET_FREEWORD),
            placeholder="名前 / 説明 で検索", label_visibility="collapsed",
        )
        st.caption("複数語は ` OR ` / ` AND ` で結合できます。")
        cols = st.columns(2)
        with cols[0]:
            st.checkbox(
                "テーブル / ビューの名前", value=True, key=_wk(state.SEARCH_ASSET_TARGET_ASSET_NAME)
            )
            st.checkbox("カラムの名前", value=True, key=_wk(state.SEARCH_ASSET_TARGET_COLUMN_NAME))
        with cols[1]:
            st.checkbox(
                "テーブル / ビューの説明", value=True, key=_wk(state.SEARCH_ASSET_TARGET_ASSET_DESC)
            )
            st.checkbox("カラムの説明", value=True, key=_wk(state.SEARCH_ASSET_TARGET_COLUMN_DESC))

    # カテゴリ2：階層（DB → スキーマ連動）
    dbs_now = st.session_state.get(_wk(state.SEARCH_ASSET_DATABASES), [])
    schemas_now = st.session_state.get(_wk(state.SEARCH_ASSET_SCHEMAS), [])
    hierarchy_expanded = _latched_expanded(
        state.ASSET_EXPANDED_HIERARCHY, has_selection=bool(dbs_now or schemas_now)
    )
    with st.expander("階層（データベース / スキーマ）", expanded=hierarchy_expanded):
        _render_combine_control(_wk(state.SEARCH_ASSET_OP_HIERARCHY))
        db_options = search.scope_databases()
        st.multiselect(
            "データベース", db_options,
            key=_wk(state.SEARCH_ASSET_DATABASES), on_change=_on_database_change,
        )
        selected_dbs = st.session_state.get(_wk(state.SEARCH_ASSET_DATABASES), [])
        schema_options = search.scope_schemas(selected_dbs)
        st.multiselect(
            "スキーマ", schema_options, key=_wk(state.SEARCH_ASSET_SCHEMAS),
            help="データベースを選択すると候補が表示されます。",
        )

    # カテゴリ3：オブジェクト種別
    types_now = st.session_state.get(_wk(state.SEARCH_ASSET_TYPES), [])
    type_expanded = _latched_expanded(state.ASSET_EXPANDED_TYPE, has_selection=bool(types_now))
    with st.expander("オブジェクト種別", expanded=type_expanded):
        _render_combine_control(_wk(state.SEARCH_ASSET_OP_TYPE))
        type_options = sorted(assets[schema.Assets.ASSET_TYPE].dropna().unique().tolist())
        st.multiselect(
            "種別", type_options, key=_wk(state.SEARCH_ASSET_TYPES), label_visibility="collapsed",
        )

    # カテゴリ4：タグ
    tag_selections: list[TagSelection] = []
    tag_widget_keys = [
        _wk(state.search_asset_tag_key(t["DATABASE_NAME"], t["SCHEMA_NAME"], t["TAG_NAME"]))
        for t in SELECTABLE_TAG_KEYS
    ]
    any_tag = any(st.session_state.get(k, []) for k in tag_widget_keys)
    tag_expanded = _latched_expanded(state.ASSET_EXPANDED_TAG, has_selection=any_tag)
    with st.expander("タグ", expanded=tag_expanded):
        _render_combine_control(_wk(state.SEARCH_ASSET_OP_TAG))
        for tag_key, widget_key in zip(SELECTABLE_TAG_KEYS, tag_widget_keys, strict=True):
            allowed = _tag_allowed_values(tags, tag_key)
            st.multiselect(tag_key["TAG_NAME"], allowed, key=widget_key)
            tag_selections.append(
                TagSelection(
                    tag_database=tag_key["DATABASE_NAME"],
                    tag_schema=tag_key["SCHEMA_NAME"],
                    tag_name=tag_key["TAG_NAME"],
                    selected=st.session_state.get(widget_key, []),
                    allowed=allowed,
                )
            )

    return AssetSearchCriteria(
        freeword=FreewordQuery(
            text=st.session_state.get(_wk(state.SEARCH_ASSET_FREEWORD), ""),
            target_asset_name=st.session_state.get(_wk(state.SEARCH_ASSET_TARGET_ASSET_NAME), True),
            target_asset_desc=st.session_state.get(_wk(state.SEARCH_ASSET_TARGET_ASSET_DESC), True),
            target_column_name=st.session_state.get(_wk(state.SEARCH_ASSET_TARGET_COLUMN_NAME), True),
            target_column_desc=st.session_state.get(_wk(state.SEARCH_ASSET_TARGET_COLUMN_DESC), True),
        ),
        selected_databases=st.session_state.get(_wk(state.SEARCH_ASSET_DATABASES), []),
        selected_schemas=st.session_state.get(_wk(state.SEARCH_ASSET_SCHEMAS), []),
        selected_types=st.session_state.get(_wk(state.SEARCH_ASSET_TYPES), []),
        tag_selections=tag_selections,
        hierarchy_or=_op_is_or(_wk(state.SEARCH_ASSET_OP_HIERARCHY)),
        type_or=_op_is_or(_wk(state.SEARCH_ASSET_OP_TYPE)),
        tag_or=_op_is_or(_wk(state.SEARCH_ASSET_OP_TAG)),
    )


def render_table(assets: pd.DataFrame) -> int | None:
    """main pane：一覧（st.dataframe）。100 件単位ページング。選択中の TABLE_ID を返す。"""
    A = schema.Assets
    ordered = assets.sort_values(
        [A.DATABASE_NAME, A.SCHEMA_NAME, A.ASSET_NAME]
    ).reset_index(drop=True)

    total = len(ordered)
    st.caption(f"{total} 件")
    if total > PAGE_SIZE:
        page_count = (total - 1) // PAGE_SIZE + 1
        page = st.number_input("ページ", min_value=1, max_value=page_count, value=1, key="asset_page")
        start = (page - 1) * PAGE_SIZE
        page_df = ordered.iloc[start:start + PAGE_SIZE]
    else:
        page_df = ordered

    display = pd.DataFrame(
        {
            "データベース": page_df[A.DATABASE_NAME],
            "スキーマ": page_df[A.SCHEMA_NAME],
            "名前": page_df[A.ASSET_NAME],
            "種別": page_df[A.ASSET_TYPE],
            "説明": page_df[A.DESCRIPTION],
        }
    ).reset_index(drop=True)

    event = st.dataframe(
        display,
        column_config=_ASSET_COLUMN_CONFIG,
        hide_index=True,
        width="stretch",
        # セル本文クリックで行を特定する（cells = [(行位置, 列名)]）。左端チェック列は出さない。
        selection_mode="single-cell",
        on_select="rerun",
        key=_ASSET_TABLE_KEY,
    )

    cells = event.selection.cells
    if cells and cells[0][0] < len(page_df):
        return int(page_df.iloc[cells[0][0]][A.TABLE_ID])
    return None


def _close_detail() -> None:
    """詳細ペインを閉じる。行選択ウィジェットの選択状態も解除する。"""
    st.session_state[state.ASSET_SELECTED_TABLE_ID] = None
    st.session_state.pop(_ASSET_TABLE_KEY, None)


def render_detail(table_id: int, assets: pd.DataFrame, columns: pd.DataFrame,
                  visibility: pd.DataFrame) -> None:
    """右カラム：シングル：データ資産の詳細ペイン。"""
    A = schema.Assets
    match = assets[assets[A.TABLE_ID] == table_id]
    if match.empty:
        st.error("選択されたデータ資産が見つかりませんでした。")
        return
    asset = match.iloc[0]

    # --- 詳細ペイン上部 ---
    st.button("✕ 閉じる", on_click=_close_detail, key="asset_detail_close")
    st.subheader(asset[A.ASSET_NAME])
    st.write(asset[A.DESCRIPTION] or "")
    st.text(f"階層: {asset[A.DATABASE_NAME]}.{asset[A.SCHEMA_NAME]}")
    st.text(f"種別: {asset[A.ASSET_TYPE]}")
    st.text(f"タグ: {_fmt_tags(asset[A.TAGS])}")
    st.text(f"PUBLIC 参照可否: {'可' if asset[A.IS_PUBLIC_VISIBILITY] else '不可'}")

    # --- 詳細ペイン下部（タブ）---
    tab_cols, tab_contact, tab_stats, tab_users = st.tabs(["カラム", "連絡先", "統計情報", "ユーザー"])
    with tab_cols:
        _render_columns_tab(table_id, columns)
    with tab_contact:
        _render_contact_tab(asset)
    with tab_stats:
        _render_stats_tab(asset)
    with tab_users:
        _render_users_tab(table_id, visibility)


def _render_columns_tab(table_id: int, columns: pd.DataFrame) -> None:
    C = schema.Columns
    cols = columns[columns[C.TABLE_ID] == table_id].sort_values(C.ORDINAL_POSITION)
    if cols.empty:
        st.caption("カラム情報がありません。")
        return
    for _, c in cols.iterrows():
        badges = []
        if c[C.IS_PRIMARY_KEY]:
            badges.append("PK")
        if c[C.IS_UNIQUE_KEY]:
            badges.append("UK")
        if c[C.FOREIGN_KEYS]:
            badges.append("FK")
        if not c[C.IS_NULLABLE]:
            badges.append("NOT NULL")
        suffix = f"  [{', '.join(badges)}]" if badges else ""
        with st.expander(f"{c[C.COLUMN_NAME]}（{c[C.DATA_TYPE]}）{suffix}"):
            st.text(f"説明: {c[C.DESCRIPTION] or ''}")
            st.text(f"タグ: {_fmt_tags(c[C.TAGS])}")
            st.text(f"マスキングポリシー: {c[C.MASKING_POLICY_NAME] or ''}")


def _render_contact_tab(asset: pd.Series) -> None:
    A = schema.Assets
    st.text(f"スチュワード: {asset[A.CONTACT_STEWARD] or ''}")
    st.text(f"サポート: {asset[A.CONTACT_SUPPORT] or ''}")
    st.text(f"承認者: {asset[A.CONTACT_ACCESS_APPROVAL] or ''}")
    st.text(f"セキュリティとコンプライアンス: {asset[A.CONTACT_SECURITY_COMPLIANCE] or ''}")


def _render_stats_tab(asset: pd.Series) -> None:
    A = schema.Assets
    row_count = asset[A.ROW_COUNT]
    n_bytes = asset[A.BYTES]
    c1, c2 = st.columns(2)
    c1.metric("行数", f"{int(row_count):,}" if pd.notna(row_count) else "-")
    c2.metric("データサイズ (bytes)", f"{int(n_bytes):,}" if pd.notna(n_bytes) else "-")


def _render_users_tab(table_id: int, visibility: pd.DataFrame) -> None:
    V = schema.AssetVisibility
    vis = visibility[visibility[V.TABLE_ID] == table_id]
    if vis.empty:
        st.caption("閲覧可能なユーザーがいません。")
        return
    asset_roles = sorted({r for roles in vis[V.ASSET_ROLES] for r in roles})
    st.text(f"直接付与ロール: {', '.join(asset_roles)}")
    st.dataframe(
        vis[[V.USER_NAME, V.USER_ROLES]].rename(
            columns={V.USER_NAME: "ユーザー", V.USER_ROLES: "起点ロール"}
        ),
        hide_index=True,
        width="stretch",
    )
    st.button("ロール継承グラフを表示", disabled=True, help="Step 4 で実装します。")


def main() -> None:
    st.title("🗂️ データ資産")

    left, main_pane = st.columns([1, 3])

    try:
        session = get_session()
        assets = catalog.load_assets(session)
        columns = catalog.load_columns(session)
        tags = catalog.load_tags(session)
        visibility = catalog.load_asset_visibility(session)
    except Exception:  # traceback は出さず日本語メッセージのみ表示する
        with main_pane:
            st.error("データの取得に失敗しました。接続設定やカタログテーブルの生成状況をご確認ください。")
        return

    with left:
        criteria = render_search(assets, tags)

    with main_pane:
        if not has_search_condition(criteria):
            st.info("左の検索条件を指定すると、一覧が表示されます。")
            return

        filtered = search.filter_assets(assets, columns, criteria)
        prior = st.session_state.get(state.ASSET_SELECTED_TABLE_ID)
        if prior is None:
            selected_now = render_table(filtered)
        else:
            list_col, detail_col = st.columns([1, 2])
            with list_col:
                selected_now = render_table(filtered)
            with detail_col:
                render_detail(prior, assets, columns, visibility)

        # 選択の変化を 1 操作で反映する（行選択で即座に詳細を開閉する）。
        if selected_now != prior:
            if selected_now is None:
                st.session_state.pop(state.ASSET_SELECTED_TABLE_ID, None)
            else:
                st.session_state[state.ASSET_SELECTED_TABLE_ID] = selected_now
            st.rerun()


main()

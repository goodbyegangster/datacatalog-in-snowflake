"""page：データ資産。

design-view.md の「page：データ資産」に対応。left pane（検索）と main pane（一覧 / 詳細）を
1:3 で配置し、行選択で main を 1:2 に分割して詳細ペインを表示する。検索仕様は
design-search.md、検索ロジックは ``lib.search`` を参照。

初期状態は一覧を空欄表示とし、検索入力に応じてインタラクティブに結果を表示する。
ユーザータブでは、ロール列のセル選択でロール継承グラフを表示する。
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import catalog, graph, schema, search, state, ui, user_context
from lib.search import AssetSearchCriteria, FreewordQuery, TagSelection
from settings import IS_VISIBLE_ONLY_SELF_USER, SELECTABLE_TAG_KEYS

PAGE_SIZE = 100
ASSET_TYPE_BADGE_COLORS = {
    "BASE TABLE": "blue",
    "VIEW": "green",
    "MATERIALIZED VIEW": "violet",
    "DYNAMIC TABLE": "orange",
    "ICEBERG TABLE": "blue",
    "HYBRID TABLE": "yellow",
    "EXTERNAL TABLE": "gray",
    "EVENT TABLE": "red",
    "TEMPORARY TABLE": "gray",
}
TAG_BADGE_COLOR_PALETTE = ("blue", "green", "orange", "violet", "red", "gray")
ASSET_PAGE_CSS = """
<style>
.asset-result-count {
    position: fixed;
    top: 72px;
    right: 32px;
    z-index: 999;
    min-width: 120px;
    padding: 10px 12px;
    border: 1px solid rgba(49, 51, 63, 0.18);
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.96);
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
    text-align: right;
}
.asset-result-count__label {
    margin: 0;
    color: rgba(49, 51, 63, 0.68);
    font-size: 12px;
    line-height: 1.2;
}
.asset-result-count__value {
    margin: 2px 0 0;
    color: rgb(49, 51, 63);
    font-size: 18px;
    font-weight: 700;
    line-height: 1.2;
}
</style>
"""

# 一覧テーブルの行選択ウィジェットの key（閉じる際に選択状態も解除するため定数化）。
_ASSET_TABLE_KEY = "asset_table"
_ASSET_USERS_TABLE_KEY = "asset_users_table"
_ASSET_USER_GRAPH_COLUMNS = {"ユーザー付与ロール", "データ資産付与ロール"}
CURRENT_USER_UNAVAILABLE_MESSAGE = (
    "ログインユーザー名を取得できないため、ログインユーザーのみ表示を適用できません。"
)

# 一覧の列表示設定（列幅）。キーは表示用 DataFrame の列名と一致させる。
_ASSET_COLUMN_CONFIG = {
    "データベース": st.column_config.TextColumn(width="small"),
    "スキーマ": st.column_config.TextColumn(width="small"),
    "名前": st.column_config.TextColumn(width="medium"),
    "説明": st.column_config.TextColumn(width="large"),
}
_ASSET_COMPACT_COLUMN_CONFIG = {
    "名前": st.column_config.TextColumn(width="medium"),
}


def _search_defaults() -> dict[str, object]:
    """検索ウィジェットの初期値。"""
    return {
        state.SEARCH_ASSET_FREEWORD: "",
        state.SEARCH_ASSET_TARGET_ASSET_NAME: True,
        state.SEARCH_ASSET_TARGET_ASSET_DESC: True,
        state.SEARCH_ASSET_TARGET_COLUMN_NAME: True,
        state.SEARCH_ASSET_TARGET_COLUMN_DESC: True,
        state.SEARCH_ASSET_DATABASES: [],
        state.SEARCH_ASSET_SCHEMAS: [],
        state.SEARCH_ASSET_TYPES: [],
        state.SEARCH_ASSET_OP_HIERARCHY: "AND",
        state.SEARCH_ASSET_OP_TYPE: "AND",
        state.SEARCH_ASSET_OP_TAG: "AND",
    }


def _render_asset_page_css() -> None:
    """データ資産ページ用の CSS を適用する。"""
    ui.render_page_spacing_css()
    st.markdown(ASSET_PAGE_CSS, unsafe_allow_html=True)


def _fmt_tags(tags: list[dict]) -> str:
    """TAGS 列（object の list）を表示用の文字列へ整形する。"""
    if not isinstance(tags, list) or not tags:
        return ""
    return ", ".join(f"{t['TAG_NAME']}={t['TAG_VALUE']}" for t in tags)


def _fmt_roles(roles: object) -> str:
    """ロール配列を dataframe 表示向けに整形する。"""
    if not isinstance(roles, list) or not roles:
        return ""
    return ", ".join(str(role) for role in roles)


def _fmt_foreign_keys(foreign_keys: object) -> str:
    """FOREIGN_KEYS 列（object の list）を表示用の文字列へ整形する。"""
    if not isinstance(foreign_keys, list) or not foreign_keys:
        return ""
    return ", ".join(
        ".".join(
            [
                str(fk["REFERENCED_DATABASE"]),
                str(fk["REFERENCED_SCHEMA"]),
                str(fk["REFERENCED_TABLE"]),
                str(fk["REFERENCED_COLUMN"]),
            ]
        )
        for fk in foreign_keys
    )


def _asset_type_badge_color(asset_type: str) -> str:
    """ASSET_TYPE に応じた badge 色を返す。"""
    return ASSET_TYPE_BADGE_COLORS.get(asset_type, "gray")


def _tag_badge_color(tag_name: str) -> str:
    """タグキー名から安定した badge 色を返す。"""
    index = sum(ord(char) for char in tag_name) % len(TAG_BADGE_COLOR_PALETTE)
    return TAG_BADGE_COLOR_PALETTE[index]


def _tag_allowed_values(tags: pd.DataFrame, tag_key: dict) -> list[str]:
    """TAGS マスターから、指定タグの allowed_values を取得する。"""
    T = schema.Tags
    mask = (
        (tags[T.TAG_DATABASE] == tag_key["DATABASE_NAME"])
        & (tags[T.TAG_SCHEMA] == tag_key["SCHEMA_NAME"])
        & (tags[T.TAG_NAME] == tag_key["TAG_NAME"])
    )
    return sorted(tags.loc[mask, T.TAG_VALUE].tolist())


def _tag_widget_key(tag_key: dict) -> str:
    return state.search_asset_tag_key(
        tag_key["DATABASE_NAME"], tag_key["SCHEMA_NAME"], tag_key["TAG_NAME"]
    )


def _init_search_state() -> None:
    """検索ウィジェットの初期値を session_state に寄せる。"""
    for key, value in _search_defaults().items():
        st.session_state.setdefault(key, value)
    for tag_key in SELECTABLE_TAG_KEYS:
        st.session_state.setdefault(_tag_widget_key(tag_key), [])


def _on_database_change() -> None:
    """DB 選択変更時、（親に依存する）スキーマ選択を未選択へリセットする。"""
    st.session_state[state.SEARCH_ASSET_SCHEMAS] = []


def _clear_search() -> None:
    """検索入力を全クリアする。"""
    for key, value in _search_defaults().items():
        st.session_state[key] = value
    for tag_key in SELECTABLE_TAG_KEYS:
        st.session_state[_tag_widget_key(tag_key)] = []
    st.session_state.pop(state.ASSET_SELECTED_TABLE_ID, None)
    st.session_state.pop(state.ASSET_PAGE, None)
    st.session_state.pop(_ASSET_TABLE_KEY, None)


def _clear_selection() -> None:
    """検索条件と整合しなくなった一覧/詳細の選択状態を解除する。"""
    st.session_state.pop(state.ASSET_SELECTED_TABLE_ID, None)
    st.session_state.pop(_ASSET_TABLE_KEY, None)


def _render_combine_control(key: str) -> None:
    """カテゴリ間の結合（AND=必須 / OR=いずれか）を選ぶセグメントコントロール。"""
    st.segmented_control(
        "その他検索との結合条件",
        ["AND", "OR"],
        key=key,
    )


def _op_is_or(key: str) -> bool:
    return st.session_state.get(key) == "OR"


def has_search_condition(criteria: AssetSearchCriteria) -> bool:
    """いずれかの検索条件が入力/選択されているか（初期空欄判定に用いる）。"""
    return bool(
        criteria.freeword.text.strip()
        or criteria.selected_databases
        or criteria.selected_schemas
        or criteria.selected_types
        or any(t.selected for t in criteria.tag_selections)
    )


def _search_fingerprint(criteria: AssetSearchCriteria) -> tuple[object, ...]:
    """現在の検索条件を、変更検知しやすい不変値へ正規化する。"""
    tags = tuple(
        (
            tag.tag_database,
            tag.tag_schema,
            tag.tag_name,
            tuple(sorted(tag.selected)),
        )
        for tag in criteria.tag_selections
        if tag.selected
    )
    return (
        criteria.freeword.text.strip(),
        criteria.freeword.target_asset_name,
        criteria.freeword.target_asset_desc,
        criteria.freeword.target_column_name,
        criteria.freeword.target_column_desc,
        tuple(sorted(criteria.selected_databases)),
        tuple(sorted(criteria.selected_schemas)),
        tuple(sorted(criteria.selected_types)),
        tags,
        criteria.hierarchy_or,
        criteria.type_or,
        criteria.tag_or,
    )


def render_search(assets: pd.DataFrame, tags: pd.DataFrame) -> AssetSearchCriteria:
    """left pane：検索 UI。ウィジェットを描画し、現在の検索条件を返す。"""
    _init_search_state()
    st.button("入力をクリア", on_click=_clear_search, width="stretch")

    # カテゴリ1：フリーワード
    with st.container(border=True):
        st.markdown("**フリーワード**")
        st.text_input(
            "キーワード",
            key=state.SEARCH_ASSET_FREEWORD,
            placeholder="名前 / 説明 で検索",
            label_visibility="collapsed",
        )
        st.caption("単語間に ` OR ` / ` AND ` を入れると組み合わせ検索ができます")
        cols = st.columns(2)
        with cols[0]:
            st.checkbox("オブジェクトの名前", key=state.SEARCH_ASSET_TARGET_ASSET_NAME)
            st.checkbox("カラムの名前", key=state.SEARCH_ASSET_TARGET_COLUMN_NAME)
        with cols[1]:
            st.checkbox("オブジェクトの説明", key=state.SEARCH_ASSET_TARGET_ASSET_DESC)
            st.checkbox("カラムの説明", key=state.SEARCH_ASSET_TARGET_COLUMN_DESC)

    # カテゴリ2：階層（DB → スキーマ連動）
    dbs_now = st.session_state.get(state.SEARCH_ASSET_DATABASES, [])
    schemas_now = st.session_state.get(state.SEARCH_ASSET_SCHEMAS, [])
    with st.expander("データベース / スキーマ", expanded=bool(dbs_now or schemas_now)):
        _render_combine_control(state.SEARCH_ASSET_OP_HIERARCHY)
        db_options = search.scope_databases()
        st.multiselect(
            "データベース",
            db_options,
            key=state.SEARCH_ASSET_DATABASES,
            on_change=_on_database_change,
        )
        selected_dbs = st.session_state.get(state.SEARCH_ASSET_DATABASES, [])
        schema_options = search.scope_schemas(selected_dbs)
        st.multiselect(
            "スキーマ",
            schema_options,
            key=state.SEARCH_ASSET_SCHEMAS,
            help="データベースを選択すると候補が表示されます",
        )

    # カテゴリ3：オブジェクト種別
    types_now = st.session_state.get(state.SEARCH_ASSET_TYPES, [])
    with st.expander("オブジェクト種別", expanded=bool(types_now)):
        _render_combine_control(state.SEARCH_ASSET_OP_TYPE)
        type_options = sorted(assets[schema.Assets.ASSET_TYPE].dropna().unique().tolist())
        st.multiselect(
            "種別",
            type_options,
            key=state.SEARCH_ASSET_TYPES,
            label_visibility="collapsed",
        )

    # カテゴリ4：タグ
    tag_selections: list[TagSelection] = []
    tag_widget_keys = [_tag_widget_key(t) for t in SELECTABLE_TAG_KEYS]
    any_tag = any(st.session_state.get(k, []) for k in tag_widget_keys)
    with st.expander("タグ", expanded=any_tag):
        _render_combine_control(state.SEARCH_ASSET_OP_TAG)
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
            text=st.session_state.get(state.SEARCH_ASSET_FREEWORD, ""),
            target_asset_name=st.session_state.get(state.SEARCH_ASSET_TARGET_ASSET_NAME, True),
            target_asset_desc=st.session_state.get(state.SEARCH_ASSET_TARGET_ASSET_DESC, True),
            target_column_name=st.session_state.get(state.SEARCH_ASSET_TARGET_COLUMN_NAME, True),
            target_column_desc=st.session_state.get(state.SEARCH_ASSET_TARGET_COLUMN_DESC, True),
        ),
        selected_databases=st.session_state.get(state.SEARCH_ASSET_DATABASES, []),
        selected_schemas=st.session_state.get(state.SEARCH_ASSET_SCHEMAS, []),
        selected_types=st.session_state.get(state.SEARCH_ASSET_TYPES, []),
        tag_selections=tag_selections,
        hierarchy_or=_op_is_or(state.SEARCH_ASSET_OP_HIERARCHY),
        type_or=_op_is_or(state.SEARCH_ASSET_OP_TYPE),
        tag_or=_op_is_or(state.SEARCH_ASSET_OP_TAG),
    )


def render_table(assets: pd.DataFrame, *, compact: bool = False) -> int | None:
    """main pane：一覧（st.dataframe）。100 件単位ページング。選択中の TABLE_ID を返す。"""
    A = schema.Assets
    ordered = assets.sort_values([A.DATABASE_NAME, A.SCHEMA_NAME, A.ASSET_NAME]).reset_index(
        drop=True
    )

    total = len(ordered)
    table_slot = st.empty()
    if total > PAGE_SIZE:
        page_count = (total - 1) // PAGE_SIZE + 1
        current_page = st.session_state.get(state.ASSET_PAGE)
        if current_page is not None and not 1 <= current_page <= page_count:
            st.session_state.pop(state.ASSET_PAGE, None)
        page = st.pagination(
            num_pages=page_count,
            key=state.ASSET_PAGE,
            on_change=_clear_selection,
        )
        start = (page - 1) * PAGE_SIZE
        page_df = ordered.iloc[start : start + PAGE_SIZE]
    else:
        page_df = ordered

    if compact:
        display = pd.DataFrame({"名前": page_df[A.ASSET_NAME]}).reset_index(drop=True)
        column_config = _ASSET_COMPACT_COLUMN_CONFIG
    else:
        display = pd.DataFrame(
            {
                "データベース": page_df[A.DATABASE_NAME],
                "スキーマ": page_df[A.SCHEMA_NAME],
                "名前": page_df[A.ASSET_NAME],
                "説明": page_df[A.DESCRIPTION],
            }
        ).reset_index(drop=True)
        column_config = _ASSET_COLUMN_CONFIG

    event = table_slot.dataframe(
        display,
        column_config=column_config,
        hide_index=True,
        width="stretch",
        selection_mode="single-cell",
        on_select="rerun",
        key=_ASSET_TABLE_KEY,
    )

    cells = event.selection.cells
    if cells and cells[0][0] < len(page_df):
        return int(page_df.iloc[cells[0][0]][A.TABLE_ID])
    return None


def render_result_count(total: int | None = None) -> None:
    """スクロール中も見える検索結果件数のサマリー。"""
    value = "-" if total is None else f"{total} 件"
    st.markdown(
        f"""
        <div class="asset-result-count">
            <p class="asset-result-count__label">検索結果</p>
            <p class="asset-result-count__value">{value}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _close_detail() -> None:
    """詳細ペインを閉じる。行選択ウィジェットの選択状態も解除する。"""
    st.session_state.pop(state.ASSET_SELECTED_TABLE_ID, None)
    st.session_state.pop(_ASSET_TABLE_KEY, None)


def render_detail(
    table_id: int,
    assets: pd.DataFrame,
    columns: pd.DataFrame,
    visibility: pd.DataFrame,
    edges: pd.DataFrame,
) -> None:
    """右カラム：シングル：データ資産の詳細ペイン。"""
    A = schema.Assets
    match = assets[assets[A.TABLE_ID] == table_id]
    if match.empty:
        st.error("選択されたデータ資産が見つかりませんでした")
        return
    asset = match.iloc[0]

    with st.container(key="asset-summary"):
        title_col, close_col = st.columns([1, 0.12], vertical_alignment="center")
        with title_col:
            st.subheader(asset[A.ASSET_NAME], anchor=False)
        with close_col:
            st.button(
                "",
                icon=":material/close:",
                help="詳細を閉じる",
                on_click=_close_detail,
                key="asset_detail_close",
                type="primary",
            )

        if asset[A.DESCRIPTION]:
            st.markdown(f"**{asset[A.DESCRIPTION]}**")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.caption("データベース")
            st.markdown(f"**{asset[A.DATABASE_NAME]}**")
        with col2:
            st.caption("スキーマ")
            st.markdown(f"**{asset[A.SCHEMA_NAME]}**")
        with col3:
            st.caption("オブジェクト種別")
            st.badge(
                asset[A.ASSET_TYPE],
                color=_asset_type_badge_color(asset[A.ASSET_TYPE]),
            )
        with col4:
            is_public = bool(asset[A.IS_PUBLIC_VISIBILITY])
            st.caption("PUBLIC")
            st.badge(
                "参照可能" if is_public else "参照不可",
                color="primary" if is_public else "gray",
            )

        st.caption("タグ")
        tags = asset[A.TAGS]
        if isinstance(tags, list) and tags:
            tag_cols = st.columns(3)
            for index, tag in enumerate(tags):
                with tag_cols[index % len(tag_cols)]:
                    tag_name = str(tag["TAG_NAME"])
                    st.badge(
                        f"{tag_name}: {tag['TAG_VALUE']}",
                        icon=":material/sell:",
                        color=_tag_badge_color(tag_name),
                    )
        else:
            st.caption("タグはありません")

    # --- 詳細ペイン下部（タブ）---
    tab_cols, tab_contact, tab_stats, tab_users = st.tabs(
        ["カラム", "連絡先", "統計情報", "ユーザー"]
    )
    with tab_cols:
        _render_columns_tab(table_id, columns)
    with tab_contact:
        _render_contact_tab(asset)
    with tab_stats:
        _render_stats_tab(asset)
    with tab_users:
        _render_users_tab(asset, visibility, edges)


def _render_columns_tab(table_id: int, columns: pd.DataFrame) -> None:
    C = schema.Columns
    cols = columns[columns[C.TABLE_ID] == table_id].sort_values(C.ORDINAL_POSITION)
    if cols.empty:
        st.caption("カラム情報がありません")
        return
    st.caption("詳細な確認は Fullscreen モード（表選択時に右上出現）を利用してください")
    display = pd.DataFrame(
        {
            "位置": cols[C.ORDINAL_POSITION],
            "名前": cols[C.COLUMN_NAME],
            "説明": cols[C.DESCRIPTION].fillna(""),
            "型": cols[C.DATA_TYPE],
            "PKEY": cols[C.IS_PRIMARY_KEY],
            "NOT NULL": ~cols[C.IS_NULLABLE],
            "UNIQUE": cols[C.IS_UNIQUE_KEY],
            "外部 KEY": cols[C.FOREIGN_KEYS].map(_fmt_foreign_keys),
            "マスキングポリシー": cols[C.MASKING_POLICY_NAME].fillna("").astype(bool),
            "タグ": cols[C.TAGS].map(_fmt_tags),
        }
    )
    st.dataframe(
        display,
        hide_index=True,
        width="stretch",
        column_config={
            "位置": st.column_config.NumberColumn(width="small"),
            "名前": st.column_config.TextColumn(width="medium"),
            "説明": st.column_config.TextColumn(width="large"),
            "型": st.column_config.TextColumn(width="small"),
            "PKEY": st.column_config.CheckboxColumn(width="small"),
            "NOT NULL": st.column_config.CheckboxColumn(width="small"),
            "UNIQUE": st.column_config.CheckboxColumn(width="small"),
            "外部 KEY": st.column_config.TextColumn(width="large"),
            "マスキングポリシー": st.column_config.CheckboxColumn(width="small"),
            "タグ": st.column_config.TextColumn(width="medium"),
        },
    )


def _render_contact_tab(asset: pd.Series) -> None:
    A = schema.Assets
    display = pd.DataFrame(
        [
            {"項目": "スチュワード", "ロール": asset[A.CONTACT_STEWARD] or ""},
            {"項目": "サポート", "ロール": asset[A.CONTACT_SUPPORT] or ""},
            {"項目": "承認者", "ロール": asset[A.CONTACT_ACCESS_APPROVAL] or ""},
            {
                "項目": "セキュリティとコンプライアンス",
                "ロール": asset[A.CONTACT_SECURITY_COMPLIANCE] or "",
            },
        ]
    )
    st.dataframe(
        display,
        hide_index=True,
        width="stretch",
        column_config={
            "項目": st.column_config.TextColumn(width="medium"),
            "ロール": st.column_config.TextColumn(width="large"),
        },
    )


def _render_stats_tab(asset: pd.Series) -> None:
    A = schema.Assets
    row_count = asset[A.ROW_COUNT]
    n_bytes = asset[A.BYTES]
    display = pd.DataFrame(
        [
            {"項目": "行数", "値": f"{int(row_count):,}" if pd.notna(row_count) else "-"},
            {
                "項目": "データサイズ (bytes)",
                "値": f"{int(n_bytes):,}" if pd.notna(n_bytes) else "-",
            },
        ]
    )
    st.dataframe(
        display,
        hide_index=True,
        width="stretch",
        column_config={
            "項目": st.column_config.TextColumn(width="medium"),
            "値": st.column_config.TextColumn(width="medium"),
        },
    )


@st.dialog("ロール継承グラフ", width="large")
def _render_asset_user_graph_dialog(user_name: str, asset_fqn: str, edges: pd.DataFrame) -> None:
    """選択ユーザーから表示中資産までの graph を表示する。"""
    result = graph.build_user_asset_graph(edges, user_name=user_name, asset_fqn=asset_fqn)
    st.markdown(f"**{user_name}** から **{asset_fqn}** までのロール継承")
    if result.path_limit_exceeded:
        st.warning("経路が多すぎるため表示できません。")
        return
    if not result.paths:
        st.warning("ロール継承 graph の経路が見つかりませんでした。")
        return
    st.caption(f"{len(result.paths)} 経路")
    st.graphviz_chart(result.dot, width="stretch")


def _selected_user_graph_row(event: object, display: pd.DataFrame) -> int | None:
    """ユーザータブで graph 対象セルが選択された場合、行位置を返す。"""
    cells = event.selection.cells
    if not cells:
        return None

    cell = cells[0]
    if isinstance(cell, dict):
        row_index = cell["row"]
        column_ref = cell["column"]
    else:
        row_index = cell[0]
        column_ref = cell[1]

    if row_index >= len(display):
        return None

    if isinstance(column_ref, int):
        if column_ref >= len(display.columns):
            return None
        column_name = display.columns[column_ref]
    else:
        column_name = str(column_ref)

    if column_name not in _ASSET_USER_GRAPH_COLUMNS:
        return None
    return int(row_index)


def _render_users_tab(asset: pd.Series, visibility: pd.DataFrame, edges: pd.DataFrame) -> None:
    A = schema.Assets
    V = schema.AssetVisibility
    table_id = int(asset[A.TABLE_ID])
    vis = visibility[visibility[V.TABLE_ID] == table_id]
    if IS_VISIBLE_ONLY_SELF_USER:
        current_user_name = user_context.current_user_name()
        if current_user_name is None:
            st.warning(CURRENT_USER_UNAVAILABLE_MESSAGE)
            return
        vis = vis[vis[V.USER_NAME] == current_user_name]

    if vis.empty:
        st.caption("閲覧可能なユーザーがいません")
        return

    display = pd.DataFrame(
        {
            "ユーザー": vis[V.USER_NAME],
            "ユーザー付与ロール": vis[V.USER_ROLES].map(_fmt_roles),
            "データ資産付与ロール": vis[V.ASSET_ROLES].map(_fmt_roles),
        }
    ).reset_index(drop=True)
    st.caption("ユーザー付与ロール / データ資産付与ロール を選択すると「ロール継承グラフ」を表示します")
    event = st.dataframe(
        display,
        hide_index=True,
        width="stretch",
        selection_mode="single-cell",
        on_select="rerun",
        key=f"{_ASSET_USERS_TABLE_KEY}_{table_id}",
        column_config={
            "ユーザー": st.column_config.TextColumn(width="medium"),
            "ユーザー付与ロール": st.column_config.TextColumn(width="medium"),
            "データ資産付与ロール": st.column_config.TextColumn(width="medium"),
        },
    )

    selected_row = _selected_user_graph_row(event, display)
    if selected_row is not None:
        _render_asset_user_graph_dialog(
            user_name=str(display.iloc[selected_row]["ユーザー"]),
            asset_fqn=".".join(
                [
                    str(asset[A.DATABASE_NAME]),
                    str(asset[A.SCHEMA_NAME]),
                    str(asset[A.ASSET_NAME]),
                ]
            ),
            edges=edges,
        )


def main() -> None:
    st.title("🗂️ データ資産", anchor=False)
    _render_asset_page_css()
    result_count = st.empty()

    left, main_pane = st.columns([1, 3])

    try:
        assets = catalog.load_assets()
        columns = catalog.load_columns()
        tags = catalog.load_tags()
        visibility = catalog.load_asset_visibility()
        edges = catalog.load_access_edges()
    except Exception as exc:
        with main_pane:
            st.error(
                "データの取得に失敗しました。接続設定やカタログテーブルの生成状況をご確認ください。"
            )
            if catalog.data_mode() == "fake":
                st.exception(exc)
        return

    with left:
        criteria = render_search(assets, tags)

    with main_pane:
        if not has_search_condition(criteria):
            _clear_selection()
            st.session_state.pop(state.ASSET_SEARCH_FINGERPRINT, None)
            with result_count:
                render_result_count()
            st.info("左の検索条件を指定すると、一覧が表示されます。")
            return

        search_fingerprint = _search_fingerprint(criteria)
        if st.session_state.get(state.ASSET_SEARCH_FINGERPRINT) != search_fingerprint:
            _clear_selection()
            st.session_state.pop(state.ASSET_PAGE, None)
            st.session_state[state.ASSET_SEARCH_FINGERPRINT] = search_fingerprint

        filtered = search.filter_assets(assets, columns, criteria)
        with result_count:
            render_result_count(len(filtered))
        if filtered.empty:
            _clear_selection()
            st.info("該当するデータ資産がありません。検索条件を変更してください。")
            return

        prior = st.session_state.get(state.ASSET_SELECTED_TABLE_ID)
        if prior is None:
            selected_now = render_table(filtered)
        else:
            list_col, detail_col = st.columns([1, 2])
            with list_col:
                selected_now = render_table(filtered, compact=True)
            with detail_col:
                render_detail(prior, assets, columns, visibility, edges)

        # 選択の変化を 1 操作で反映する（行選択で即座に詳細を開閉する）。
        if selected_now != prior:
            if selected_now is None:
                st.session_state.pop(state.ASSET_SELECTED_TABLE_ID, None)
            else:
                st.session_state[state.ASSET_SELECTED_TABLE_ID] = selected_now
            st.rerun()


main()

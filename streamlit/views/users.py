"""page：ユーザー。

design-view.md の「page：ユーザー」に対応。left pane（検索）と main pane（一覧 / 詳細）を
1:3 で配置し、ユーザー検索・一覧・詳細ペインを表示する。初期は全ユーザー表示。

詳細ペインでは、選択ユーザーの基本情報と閲覧可能なデータ資産を表示する。
閲覧可能データ資産一覧では、行選択後のボタン操作でロール継承グラフを表示する。
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import catalog, graph, schema, search, state, ui, user_context
from lib.search import UserFreewordQuery
from settings import IS_VISIBLE_ONLY_SELF_USER

# 一覧テーブルの行選択ウィジェットの key（閉じる際に選択状態も解除するため定数化）。
_USER_TABLE_KEY = "user_table"
_USER_ASSETS_TABLE_KEY = "user_assets_table"

_USER_COLUMN_CONFIG = {
    "名前": st.column_config.TextColumn(width="medium"),
    "表示名": st.column_config.TextColumn(width="large"),
    "タイプ": st.column_config.TextColumn(width="small"),
    "ステータス": st.column_config.TextColumn(width="small"),
}
_USER_COMPACT_COLUMN_CONFIG = {
    "名前": st.column_config.TextColumn(width="medium"),
}
CURRENT_USER_UNAVAILABLE_MESSAGE = (
    "ログインユーザー名を取得できないため、ログインユーザーのみ表示を適用できません。"
)
USER_TYPE_BADGE_COLORS = {
    "PERSON": "blue",
    "SERVICE": "orange",
    "LEGACY_SERVICE": "gray",
}


def _fmt_roles(roles: object) -> str:
    """ロール配列を dataframe 表示向けに整形する。"""
    if not isinstance(roles, list) or not roles:
        return ""
    return ", ".join(str(role) for role in roles)


def _display_user_type(user_type: object) -> str:
    """Snowflake ユーザー種別を表示用に正規化する。"""
    if pd.isna(user_type) or user_type == "":
        return "PERSON"
    return str(user_type)


def _user_type_badge_color(user_type: str) -> str:
    """ユーザー種別に応じた badge 色を返す。"""
    return USER_TYPE_BADGE_COLORS.get(user_type, "gray")


def _search_defaults() -> dict[str, object]:
    """検索ウィジェットの初期値。"""
    return {
        state.SEARCH_USER_ONLY_SELF: IS_VISIBLE_ONLY_SELF_USER,
        state.SEARCH_USER_FREEWORD: "",
        state.SEARCH_USER_TARGET_USER_NAME: True,
        state.SEARCH_USER_TARGET_DISPLAY_NAME: True,
    }


def _init_search_state() -> None:
    """検索ウィジェットの初期値を session_state に寄せる。"""
    for key, value in _search_defaults().items():
        st.session_state.setdefault(key, value)
    if IS_VISIBLE_ONLY_SELF_USER:
        st.session_state[state.SEARCH_USER_ONLY_SELF] = True


def _clear_selection() -> None:
    """一覧/詳細の選択状態を解除する。"""
    st.session_state.pop(state.USER_SELECTED_NAME, None)
    st.session_state.pop(_USER_TABLE_KEY, None)


def _close_detail() -> None:
    """詳細ペインを閉じる。行選択ウィジェットの選択状態も解除する。"""
    _clear_selection()
    st.session_state.pop(state.NAV_TO_USER_NAME, None)


def _clear_search() -> None:
    """検索入力を全クリアする。"""
    for key, value in _search_defaults().items():
        st.session_state[key] = value
    if IS_VISIBLE_ONLY_SELF_USER:
        st.session_state[state.SEARCH_USER_ONLY_SELF] = True
    _clear_selection()


def _render_user_page_css() -> None:
    """ユーザーページ用の CSS を適用する。"""
    ui.render_page_spacing_css()


def _set_asset_page_navigation(table_id: int) -> None:
    """データ資産ページへ遷移するための状態を積む。"""
    st.session_state[state.NAV_TO_TABLE_ID] = int(table_id)
    st.session_state.pop(state.ASSET_SELECTED_TABLE_ID, None)


def _consume_nav_to_user_name(users: pd.DataFrame) -> str | None:
    """ページ間遷移で指定されたユーザー名を取り出し、存在する場合のみ返す。"""
    user_name = st.session_state.pop(state.NAV_TO_USER_NAME, None)
    if user_name is None:
        return None

    normalized = str(user_name).upper()
    U = schema.Users
    if normalized in set(users[U.USER_NAME].astype(str).str.upper().tolist()):
        st.session_state[state.USER_SELECTED_NAME] = normalized
        return normalized
    return None


def _user_search_fingerprint(
    freeword: UserFreewordQuery, only_user_name: str | None
) -> tuple[object, ...]:
    """現在の検索条件を、変更検知しやすい不変値へ正規化する。"""
    return (
        only_user_name,
        freeword.text.strip(),
        freeword.target_user_name,
        freeword.target_display_name,
    )


def render_search() -> tuple[UserFreewordQuery, str | None, bool]:
    """left pane：検索 UI。ウィジェットを描画し、現在の検索条件を返す。"""
    _init_search_state()
    st.button("入力をクリア", on_click=_clear_search, width="stretch")

    only_self = st.toggle(
        "ログインユーザーのみ表示",
        key=state.SEARCH_USER_ONLY_SELF,
        disabled=IS_VISIBLE_ONLY_SELF_USER,
        help="Streamlit App にログインしている Snowflake ユーザーのみ表示します",
    )
    if IS_VISIBLE_ONLY_SELF_USER:
        only_self = True
    only_user_name = user_context.current_user_name() if only_self else None

    with st.container(border=True):
        st.markdown("**フリーワード**")
        disabled = only_self
        st.text_input(
            "キーワード",
            key=state.SEARCH_USER_FREEWORD,
            placeholder="名前 / 表示名 で検索",
            label_visibility="collapsed",
            disabled=disabled,
        )
        st.caption("単語間に ` OR ` / ` AND ` を入れると組み合わせ検索ができます")
        cols = st.columns(2)
        with cols[0]:
            st.checkbox(
                "ユーザーの名前",
                key=state.SEARCH_USER_TARGET_USER_NAME,
                disabled=disabled,
            )
        with cols[1]:
            st.checkbox(
                "ユーザーの表示名",
                key=state.SEARCH_USER_TARGET_DISPLAY_NAME,
                disabled=disabled,
            )

    return (
        UserFreewordQuery(
            text="" if disabled else st.session_state.get(state.SEARCH_USER_FREEWORD, ""),
            target_user_name=st.session_state.get(state.SEARCH_USER_TARGET_USER_NAME, True),
            target_display_name=st.session_state.get(state.SEARCH_USER_TARGET_DISPLAY_NAME, True),
        ),
        only_user_name,
        only_self,
    )


def render_table(users: pd.DataFrame, *, compact: bool = False) -> str | None:
    """main pane：一覧（st.dataframe）。選択中の USER_NAME を返す。"""
    U = schema.Users
    ordered = users.sort_values(U.USER_NAME).reset_index(drop=True)

    if compact:
        display = pd.DataFrame({"名前": ordered[U.USER_NAME]}).reset_index(drop=True)
        column_config = _USER_COMPACT_COLUMN_CONFIG
    else:
        display = pd.DataFrame(
            {
                "名前": ordered[U.USER_NAME],
                "表示名": ordered[U.DISPLAY_NAME],
                "タイプ": ordered[U.USER_TYPE],
                "ステータス": ordered[U.DISABLED].map(lambda d: "無効" if d else "有効"),
            }
        ).reset_index(drop=True)
        column_config = _USER_COLUMN_CONFIG

    event = st.dataframe(
        display,
        column_config=column_config,
        hide_index=True,
        height="stretch",
        width="stretch",
        selection_mode="single-cell",
        on_select="rerun",
        key=_USER_TABLE_KEY,
    )

    cells = event.selection.cells
    if cells and cells[0][0] < len(ordered):
        return str(ordered.iloc[cells[0][0]][U.USER_NAME])
    return None


@st.dialog("ロール継承グラフ", width="large")
def _render_user_asset_graph_dialog(user_name: str, asset_fqn: str, edges: pd.DataFrame) -> None:
    """選択ユーザーから選択資産までの graph を表示する。"""
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


def _selected_asset_row(event: object, display: pd.DataFrame) -> int | None:
    """閲覧可能データ資産一覧で選択されたセルの行位置を返す。"""
    cells = event.selection.cells
    if not cells:
        return None

    cell = cells[0]
    row_index = cell["row"] if isinstance(cell, dict) else cell[0]
    if row_index >= len(display):
        return None
    return int(row_index)


def render_detail(
    user_name: str, users: pd.DataFrame, visibility: pd.DataFrame, edges: pd.DataFrame
) -> None:
    """右カラム：シングル：ユーザーの詳細ペイン。"""
    U = schema.Users
    match = users[users[U.USER_NAME] == user_name]
    if match.empty:
        st.error("選択されたユーザーが見つかりませんでした。")
        return
    user = match.iloc[0]

    title_col, close_col = st.columns([1, 0.12], vertical_alignment="center")
    with title_col:
        st.subheader(user[U.USER_NAME], anchor=False)
    with close_col:
        st.button(
            "",
            icon=":material/close:",
            help="詳細を閉じる",
            on_click=_close_detail,
            key="user_detail_close",
            type="primary",
        )

    display_name = user[U.DISPLAY_NAME]
    if pd.notna(display_name) and str(display_name) != "":
        st.markdown(f"**{display_name}**")

    user_type = _display_user_type(user[U.USER_TYPE])
    disabled = bool(user[U.DISABLED])
    col1, col2 = st.columns(2)
    with col1:
        st.caption("タイプ")
        st.badge(user_type, color=_user_type_badge_color(user_type))
    with col2:
        st.caption("ステータス")
        st.badge("無効" if disabled else "有効", color="red" if disabled else "green")

    # --- 詳細ペイン下部：閲覧可能なデータ資産 ---
    V = schema.AssetVisibility
    vis = visibility[visibility[V.USER_NAME] == user_name]
    st.markdown("**閲覧可能なデータ資産**")
    if vis.empty:
        st.caption("閲覧可能なデータ資産がありません。")
    else:
        vis_display_source = vis.sort_values(
            [V.DATABASE_NAME, V.SCHEMA_NAME, V.ASSET_NAME]
        ).reset_index(drop=True)
        display = pd.DataFrame(
            {
                "データベース": vis_display_source[V.DATABASE_NAME],
                "スキーマ": vis_display_source[V.SCHEMA_NAME],
                "名前": vis_display_source[V.ASSET_NAME],
                "ユーザー付与ロール": vis_display_source[V.USER_ROLES].map(_fmt_roles),
                "データ資産付与ロール": vis_display_source[V.ASSET_ROLES].map(_fmt_roles),
            }
        ).reset_index(drop=True)
        action_slot = st.container()
        event = st.dataframe(
            display,
            hide_index=True,
            height="stretch",
            width="stretch",
            selection_mode="single-cell",
            on_select="rerun",
            key=f"{_USER_ASSETS_TABLE_KEY}_{user_name}",
            column_config={
                "データベース": st.column_config.TextColumn(width="small"),
                "スキーマ": st.column_config.TextColumn(width="small"),
                "名前": st.column_config.TextColumn(width="medium"),
                "ユーザー付与ロール": st.column_config.TextColumn(width="medium"),
                "データ資産付与ロール": st.column_config.TextColumn(width="medium"),
            },
        )

        selected_asset_row = _selected_asset_row(event, display)
        selected_table_id = (
            None
            if selected_asset_row is None
            else int(vis_display_source.iloc[selected_asset_row][V.TABLE_ID])
        )
        with action_slot:
            open_col, graph_col = st.columns(2)
            with open_col:
                if st.button(
                    "選択データ資産を開く",
                    icon=":material/table_view:",
                    disabled=selected_table_id is None,
                    key=f"user_asset_open_button_{user_name}",
                    width="stretch",
                ):
                    _set_asset_page_navigation(selected_table_id or 0)
                    st.switch_page("views/assets.py")
            with graph_col:
                if st.button(
                    "ロール継承グラフを表示",
                    icon=":material/account_tree:",
                    disabled=selected_asset_row is None,
                    key=f"user_asset_graph_button_{user_name}",
                    width="stretch",
                ):
                    _render_user_asset_graph_dialog(
                        user_name=user_name,
                        asset_fqn=".".join(
                            [
                                str(display.iloc[selected_asset_row]["データベース"]),
                                str(display.iloc[selected_asset_row]["スキーマ"]),
                                str(display.iloc[selected_asset_row]["名前"]),
                            ]
                        ),
                        edges=edges,
                    )
            st.caption("行を選択してから、必要な操作ボタンを押してください")


def main() -> None:
    st.title("👤 ユーザー", anchor=False)
    _render_user_page_css()

    left, main_pane = st.columns([1, 3])
    with left:
        freeword, only_user_name, only_self = render_search()

    with main_pane:
        if only_self and only_user_name is None:
            _clear_selection()
            st.warning(CURRENT_USER_UNAVAILABLE_MESSAGE)
            return

        try:
            users = catalog.load_users()
            visibility = catalog.load_asset_visibility()
            edges = catalog.load_access_edges()
        except Exception as exc:
            st.error(
                "データの取得に失敗しました。接続設定やカタログテーブルの生成状況をご確認ください。"
            )
            if catalog.data_mode() == "fake":
                st.exception(exc)
            return

        search_fingerprint = _user_search_fingerprint(freeword, only_user_name)
        if st.session_state.get(state.USER_SEARCH_FINGERPRINT) != search_fingerprint:
            _clear_selection()
            st.session_state[state.USER_SEARCH_FINGERPRINT] = search_fingerprint

        _consume_nav_to_user_name(users)

        filtered = search.filter_users(users, freeword, only_user_name=only_user_name)
        if filtered.empty:
            _clear_selection()
            st.info("該当するユーザーがいません。検索条件を変更してください。")
            return

        prior = st.session_state.get(state.USER_SELECTED_NAME)
        U = schema.Users
        if prior is not None and prior not in set(filtered[U.USER_NAME].astype(str).tolist()):
            _clear_selection()
            prior = None

        if prior is None:
            selected_now = render_table(filtered)
        else:
            list_col, detail_col = st.columns([1, 3])
            with list_col:
                selected_now = render_table(filtered, compact=True)
            with detail_col:
                render_detail(prior, users, visibility, edges)

        # 選択セルがない rerun は、詳細ペイン内の操作でも発生するため既存詳細を維持する。
        if selected_now is not None and selected_now != prior:
            st.session_state[state.USER_SELECTED_NAME] = selected_now
            st.rerun()


main()

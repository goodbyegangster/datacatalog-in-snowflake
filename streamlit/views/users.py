"""page：ユーザー。

design-view.md の「page：ユーザー」に対応。left pane（検索）と main pane（一覧 / 詳細）を
1:3 で配置し、ユーザー検索・一覧・詳細ペインを表示する。初期は全ユーザー表示。

詳細ペインでは、選択ユーザーの基本情報と閲覧可能なデータ資産を表示する。
ロール継承グラフは Step 4 で実装する。
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import catalog, schema, search, state, ui, user_context
from lib.search import UserFreewordQuery
from settings import IS_VISIBLE_ONLY_SELF_USER

PAGE_SIZE = 100

# 一覧テーブルの行選択ウィジェットの key（閉じる際に選択状態も解除するため定数化）。
_USER_TABLE_KEY = "user_table"

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


def _clear_search() -> None:
    """検索入力を全クリアする。"""
    for key, value in _search_defaults().items():
        st.session_state[key] = value
    if IS_VISIBLE_ONLY_SELF_USER:
        st.session_state[state.SEARCH_USER_ONLY_SELF] = True
    _clear_selection()
    st.session_state.pop(state.USER_PAGE, None)


def _render_user_page_css() -> None:
    """ユーザーページ用の CSS を適用する。"""
    ui.render_page_spacing_css()


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
    """main pane：一覧（st.dataframe）。100 件単位ページング。選択中の USER_NAME を返す。"""
    U = schema.Users
    ordered = users.sort_values(U.USER_NAME).reset_index(drop=True)

    total = len(ordered)
    table_slot = st.empty()
    if total > PAGE_SIZE:
        page_count = (total - 1) // PAGE_SIZE + 1
        current_page = st.session_state.get(state.USER_PAGE)
        if current_page is not None and not 1 <= current_page <= page_count:
            st.session_state.pop(state.USER_PAGE, None)
        page = st.pagination(
            num_pages=page_count,
            key=state.USER_PAGE,
            on_change=_clear_selection,
        )
        start = (page - 1) * PAGE_SIZE
        page_df = ordered.iloc[start : start + PAGE_SIZE]
    else:
        page_df = ordered

    if compact:
        display = pd.DataFrame({"名前": page_df[U.USER_NAME]}).reset_index(drop=True)
        column_config = _USER_COMPACT_COLUMN_CONFIG
    else:
        display = pd.DataFrame(
            {
                "名前": page_df[U.USER_NAME],
                "表示名": page_df[U.DISPLAY_NAME],
                "タイプ": page_df[U.USER_TYPE],
                "ステータス": page_df[U.DISABLED].map(lambda d: "無効" if d else "有効"),
            }
        ).reset_index(drop=True)
        column_config = _USER_COLUMN_CONFIG

    event = table_slot.dataframe(
        display,
        column_config=column_config,
        hide_index=True,
        width="stretch",
        selection_mode="single-cell",
        on_select="rerun",
        key=_USER_TABLE_KEY,
    )

    cells = event.selection.cells
    if cells and cells[0][0] < len(page_df):
        return str(page_df.iloc[cells[0][0]][U.USER_NAME])
    return None


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
            pd.DataFrame(
                {
                    "データベース": vis[V.DATABASE_NAME],
                    "スキーマ": vis[V.SCHEMA_NAME],
                    "名前": vis[V.ASSET_NAME],
                    "起点ロール": vis[V.USER_ROLES].map(_fmt_roles),
                }
            ),
            hide_index=True,
            width="stretch",
        )
    st.button("ロール継承グラフを表示", disabled=True, help="Step 4 で実装します。")


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
            st.session_state.pop(state.USER_PAGE, None)
            st.session_state[state.USER_SEARCH_FINGERPRINT] = search_fingerprint

        filtered = search.filter_users(users, freeword, only_user_name=only_user_name)
        if filtered.empty:
            _clear_selection()
            st.info("該当するユーザーがいません。検索条件を変更してください。")
            return

        prior = st.session_state.get(state.USER_SELECTED_NAME)
        if prior is None:
            selected_now = render_table(filtered)
        else:
            list_col, detail_col = st.columns([1, 2])
            with list_col:
                selected_now = render_table(filtered, compact=True)
            with detail_col:
                render_detail(prior, users, visibility, edges)

        # 選択の変化を 1 操作で反映する（行選択で即座に詳細を開閉する）。
        if selected_now != prior:
            if selected_now is None:
                st.session_state.pop(state.USER_SELECTED_NAME, None)
            else:
                st.session_state[state.USER_SELECTED_NAME] = selected_now
            st.rerun()


main()

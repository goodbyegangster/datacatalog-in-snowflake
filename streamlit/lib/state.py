"""``st.session_state`` のキー定数。

Streamlit は再実行のたびにスクリプトを再評価するため、選択状態や検索条件は
session_state に永続させる。キーは接頭辞で名前空間を分ける（design-view.md 参照）。

- ``asset_`` : データ資産ページの状態
- ``user_``  : ユーザーページの状態
- ``search_``: 検索ウィジェットの選択値（Step 3 で追加）
"""

from __future__ import annotations

# --- ページ内で選択中の行 ID ---
ASSET_SELECTED_TABLE_ID = "asset_selected_table_id"
ASSET_SEARCH_FINGERPRINT = "asset_search_fingerprint"
USER_SELECTED_NAME = "user_selected_name"
USER_SEARCH_FINGERPRINT = "user_search_fingerprint"

# --- 検索ウィジェットの選択値（データ資産ページ） ---
SEARCH_ASSET_FREEWORD = "search_asset_freeword"
SEARCH_ASSET_TARGET_ASSET_NAME = "search_asset_target_asset_name"
SEARCH_ASSET_TARGET_ASSET_DESC = "search_asset_target_asset_desc"
SEARCH_ASSET_TARGET_COLUMN_NAME = "search_asset_target_column_name"
SEARCH_ASSET_TARGET_COLUMN_DESC = "search_asset_target_column_desc"
SEARCH_ASSET_DATABASES = "search_asset_databases"
SEARCH_ASSET_SCHEMAS = "search_asset_schemas"
SEARCH_ASSET_TYPES = "search_asset_types"
# カテゴリ間結合（バケット方式）の AND / OR 指定。値は "AND" / "OR"。
SEARCH_ASSET_OP_HIERARCHY = "search_asset_op_hierarchy"
SEARCH_ASSET_OP_TYPE = "search_asset_op_type"
SEARCH_ASSET_OP_TAG = "search_asset_op_tag"
# タグの選択値は tag key ごとに動的なキーを用いる（下記ヘルパで生成）。

# --- 検索ウィジェットの選択値（ユーザーページ） ---
SEARCH_USER_ONLY_SELF = "search_user_only_self"
SEARCH_USER_FREEWORD = "search_user_freeword"
SEARCH_USER_TARGET_USER_NAME = "search_user_target_user_name"
SEARCH_USER_TARGET_DISPLAY_NAME = "search_user_target_display_name"


def search_asset_tag_key(tag_database: str, tag_schema: str, tag_name: str) -> str:
    """タグ絞り込み multiselect 用の session_state キーを生成する。"""
    return f"search_asset_tag__{tag_database}__{tag_schema}__{tag_name}"


# --- ページ間遷移で「遷移先に選択させたい ID」を積むキー ---
# データ資産ページのユーザー一覧から遷移する際に対象ユーザー名を積む。
NAV_TO_USER_NAME = "nav_to_user_name"
# ユーザーページの閲覧可能資産一覧から遷移する際に対象 TABLE_ID を積む。
NAV_TO_TABLE_ID = "nav_to_table_id"
# ロール継承グラフページへ遷移する際に対象ユーザー名・資産 ID / FQN を積む。
NAV_GRAPH_USER_NAME = "nav_graph_user_name"
NAV_GRAPH_TABLE_ID = "nav_graph_table_id"
NAV_GRAPH_ASSET_FQN = "nav_graph_asset_fqn"

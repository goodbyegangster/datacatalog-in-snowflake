"""``st.session_state`` に保存するキー名の契約。

Streamlit は rerun のたびに script を再評価するため、ページをまたいで維持する状態は
名前付き key で扱う。ここには値そのものではなく、各 module が共有する key 名だけを置く。
"""

from __future__ import annotations

# --- ページ内の選択状態 -----------------------------------------------------
#
# 一覧と詳細ペインの両方で参照する、現在選択中の行を保持する。
ASSET_SELECTED_TABLE_ID = "asset_selected_table_id"
USER_SELECTED_NAME = "user_selected_name"

# 検索条件が変わったタイミングを検知し、既存選択を解除するための正規化済み値を保持する。
ASSET_SEARCH_FINGERPRINT = "asset_search_fingerprint"
USER_SEARCH_FINGERPRINT = "user_search_fingerprint"


# --- データ資産検索 widget --------------------------------------------------
#
# 以降はデータ資産検索 UI の widget key。key を固定することで rerun 後も入力値を維持する。


# --- データ資産検索 widget：フリーワード -------------------------------------
SEARCH_ASSET_FREEWORD = "search_asset_freeword"
SEARCH_ASSET_TARGET_ASSET_NAME = "search_asset_target_asset_name"
SEARCH_ASSET_TARGET_ASSET_DESC = "search_asset_target_asset_desc"
SEARCH_ASSET_TARGET_COLUMN_NAME = "search_asset_target_column_name"
SEARCH_ASSET_TARGET_COLUMN_DESC = "search_asset_target_column_desc"


# --- データ資産検索 widget：データベース / スキーマ --------------------------
SEARCH_ASSET_DATABASES = "search_asset_databases"
SEARCH_ASSET_SCHEMAS = "search_asset_schemas"


# --- データ資産検索 widget：オブジェクト種別 --------------------------------
SEARCH_ASSET_TYPES = "search_asset_types"


# --- データ資産検索 widget：タグ --------------------------------------------
# タグ値 widget は settings.SELECTABLE_TAG_KEYS のタグキーごとに key を生成する。
def search_asset_tag_key(tag_database: str, tag_schema: str, tag_name: str) -> str:
    """タグキー 3 要素から、タグ値 multiselect 用の session_state キーを生成する。"""
    return f"search_asset_tag__{tag_database}__{tag_schema}__{tag_name}"


# --- データ資産検索 widget：検索条件グループの結合方法 -----------------------
#
# フリーワード以外の検索条件グループを、他グループと AND / OR のどちらで結合するかを保持する。
SEARCH_ASSET_OP_HIERARCHY = "search_asset_op_hierarchy"
SEARCH_ASSET_OP_TYPE = "search_asset_op_type"
SEARCH_ASSET_OP_TAG = "search_asset_op_tag"


# --- ユーザー検索 widget -----------------------------------------------------
#
# SEARCH_USER_ONLY_SELF は設定値と現在ユーザーに依存するため、ページ遷移時の保持対象から外す。
SEARCH_USER_ONLY_SELF = "search_user_only_self"
SEARCH_USER_FREEWORD = "search_user_freeword"
SEARCH_USER_TARGET_USER_NAME = "search_user_target_user_name"
SEARCH_USER_TARGET_DISPLAY_NAME = "search_user_target_display_name"


# --- ページ間遷移 -----------------------------------------------------------
#
# runtime.navigation が遷移直前に積み、遷移先 page が取り出して選択状態へ反映する。
NAV_TO_USER_NAME = "nav_to_user_name"
NAV_TO_TABLE_ID = "nav_to_table_id"

# graph page はユーザーと資産の組を表示するため、片方だけでなく FQN と戻り先も保持する。
NAV_GRAPH_USER_NAME = "nav_graph_user_name"
NAV_GRAPH_TABLE_ID = "nav_graph_table_id"
NAV_GRAPH_ASSET_FQN = "nav_graph_asset_fqn"
NAV_GRAPH_RETURN_PAGE = "nav_graph_return_page"

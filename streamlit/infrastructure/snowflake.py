"""Snowflake セッション取得を集約するモジュール。

- SiS 実行時: ``snowflake.snowpark.context.get_active_session()``
- ローカル開発時: ``.streamlit/secrets.toml`` の ``[connections.snowflake]``

技術規約（technical-guidelines.md）に従い、UI 層（pages / components）からは接続処理を
直接書かず、必ず本モジュール経由でセッションを取得する。テスト容易性のため、セッションは
呼び出し側へ注入できる形（引数で受け渡す）を前提とする。
"""

from __future__ import annotations

import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.context import get_active_session


@st.cache_resource
def get_session() -> Session:
    """アクティブな Snowflake セッションを返す。

    SiS 上では実行中セッションを、ローカルでは secrets.toml の接続定義を利用する。
    セッションはプロセス内で再利用したいため ``st.cache_resource`` で保持する。
    """
    try:
        return get_active_session()
    except Exception:
        return st.connection("snowflake").session()

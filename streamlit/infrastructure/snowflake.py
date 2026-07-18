"""Snowflake セッション取得を集約する。"""

from __future__ import annotations

import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.context import get_active_session


@st.cache_resource
def get_session() -> Session:
    """Snowflake 接続に利用する Snowpark Session を返す。

    Streamlit in Snowflake 上では実行中の active session を使い、ローカル開発時は
    ``.streamlit/secrets.toml`` の ``[connections.snowflake]`` から接続する。
    """
    try:
        return get_active_session()
    except Exception:
        return st.connection("snowflake").session()

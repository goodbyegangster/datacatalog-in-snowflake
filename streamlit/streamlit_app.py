"""データカタログ アプリのエントリポイント。

``st.navigation`` + ``st.Page`` でマルチページを構成する。ページ本体は ``views/``（ASCII
名）に置き、ナビゲーションの表示名（日本語）はここで与える。``st.set_page_config`` は
セッションで一度だけ、本エントリで呼ぶ（各ページでは呼ばない）。
"""

import streamlit as st

from runtime import widget_state

st.set_page_config(page_title="データカタログ", page_icon="📚", layout="wide")

pages = [
    st.Page("views/assets.py", title="データ資産", icon="🗂️", default=True),
    st.Page("views/users.py", title="ユーザー", icon="👤"),
    st.Page("views/graph.py", title="ロール継承グラフ", icon="🌐", visibility="hidden"),
]

widget_state.preserve_widget_state(widget_state.search_widget_keys())
st.navigation(pages, position="top").run()

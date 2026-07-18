"""データカタログ アプリのエントリポイント。"""

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

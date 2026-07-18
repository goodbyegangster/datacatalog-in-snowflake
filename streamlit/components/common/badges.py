"""Streamlit badge の共通型を定義する。"""

from __future__ import annotations

from typing import Literal

StreamlitBadgeColor = Literal[
    "red",
    "orange",
    "yellow",
    "blue",
    "green",
    "violet",
    "gray",
    "grey",
    "primary",
]
"""st.badge の color に指定する色名。"""

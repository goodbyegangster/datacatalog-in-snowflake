"""データ資産詳細の連絡先 tab component。"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from catalog import schema


def render(asset: pd.Series) -> None:
    """連絡先 tab を表示する。"""
    assets_schema = schema.Assets
    display = pd.DataFrame(
        [
            {"担当": "スチュワード", "連絡先": asset[assets_schema.CONTACT_STEWARD] or ""},
            {"担当": "サポート", "連絡先": asset[assets_schema.CONTACT_SUPPORT] or ""},
            {"担当": "承認者", "連絡先": asset[assets_schema.CONTACT_ACCESS_APPROVAL] or ""},
            {
                "担当": "セキュリティとコンプライアンス",
                "連絡先": asset[assets_schema.CONTACT_SECURITY_COMPLIANCE] or "",
            },
        ]
    )
    st.dataframe(
        display,
        hide_index=True,
        width="stretch",
        column_config={
            "担当": st.column_config.TextColumn(width="medium"),
            "連絡先": st.column_config.TextColumn(width="large"),
        },
    )

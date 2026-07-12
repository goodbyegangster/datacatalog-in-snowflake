"""データ資産詳細の連絡先 tab component。"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from catalog import schema


def render(asset: pd.Series) -> None:
    """連絡先 tab を表示する。"""
    A = schema.Assets
    display = pd.DataFrame(
        [
            {"項目": "スチュワード", "ロール": asset[A.CONTACT_STEWARD] or ""},
            {"項目": "サポート", "ロール": asset[A.CONTACT_SUPPORT] or ""},
            {"項目": "承認者", "ロール": asset[A.CONTACT_ACCESS_APPROVAL] or ""},
            {
                "項目": "セキュリティとコンプライアンス",
                "ロール": asset[A.CONTACT_SECURITY_COMPLIANCE] or "",
            },
        ]
    )
    st.dataframe(
        display,
        hide_index=True,
        width="stretch",
        column_config={
            "項目": st.column_config.TextColumn(width="medium"),
            "ロール": st.column_config.TextColumn(width="large"),
        },
    )

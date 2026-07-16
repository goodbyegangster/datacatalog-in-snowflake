"""データ資産詳細のカラム tab component。"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from catalog import schema


def _fmt_tags(tags: list[dict]) -> str:
    """TAGS 列（object の list）を表示用の文字列へ整形する。"""
    if not isinstance(tags, list) or not tags:
        return ""
    return ", ".join(f"{t['TAG_NAME']}={t['TAG_VALUE']}" for t in tags)


def _fmt_foreign_keys(foreign_keys: object) -> str:
    """FOREIGN_KEYS 列（object の list）を表示用の文字列へ整形する。"""
    if not isinstance(foreign_keys, list) or not foreign_keys:
        return ""
    return ", ".join(
        ".".join(
            [
                str(fk["REFERENCED_DATABASE"]),
                str(fk["REFERENCED_SCHEMA"]),
                str(fk["REFERENCED_TABLE"]),
                str(fk["REFERENCED_COLUMN"]),
            ]
        )
        for fk in foreign_keys
    )


def render(table_id: int, columns: pd.DataFrame) -> None:
    """カラム tab を表示する。"""
    columns_schema = schema.Columns
    cols = columns[columns[columns_schema.TABLE_ID] == table_id].sort_values(
        columns_schema.ORDINAL_POSITION
    )
    if cols.empty:
        st.caption("カラム情報がありません")
        return

    st.caption("詳細な確認は Fullscreen モード（表選択時に右上出現）を利用してください")
    display = pd.DataFrame(
        {
            "位置": cols[columns_schema.ORDINAL_POSITION],
            "名前": cols[columns_schema.COLUMN_NAME],
            "説明": cols[columns_schema.DESCRIPTION].fillna(""),
            "型": cols[columns_schema.DATA_TYPE],
            "PKEY": cols[columns_schema.IS_PRIMARY_KEY],
            "NOT NULL": cols[columns_schema.IS_NULLABLE],
            "UNIQUE": cols[columns_schema.IS_UNIQUE_KEY],
            "外部 KEY": cols[columns_schema.FOREIGN_KEYS].map(_fmt_foreign_keys),
            "masking policy": cols[columns_schema.MASKING_POLICY_NAME].fillna("").astype(bool),
            "タグ": cols[columns_schema.TAGS].map(_fmt_tags),
        }
    )
    st.dataframe(
        display,
        hide_index=True,
        height="auto",
        width="stretch",
        column_config={
            "位置": st.column_config.NumberColumn(width="small"),
            "名前": st.column_config.TextColumn(width="medium"),
            "説明": st.column_config.TextColumn(width="large"),
            "型": st.column_config.TextColumn(width="small"),
            "PKEY": st.column_config.CheckboxColumn(width="small"),
            "NOT NULL": st.column_config.CheckboxColumn(width="small"),
            "UNIQUE": st.column_config.CheckboxColumn(width="small"),
            "外部 KEY": st.column_config.TextColumn(width="large"),
            "masking policy": st.column_config.CheckboxColumn(width="small"),
            "タグ": st.column_config.TextColumn(width="medium"),
        },
    )

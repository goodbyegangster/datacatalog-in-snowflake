# ruff: noqa: S101

from __future__ import annotations

import pandas as pd

from catalog import frame, schema


def test_filter_rows_by_display_scopes_keeps_matching_database_and_schema() -> None:
    """DISPLAY_SCOPES に含まれる DB / スキーマの行だけを返す。"""
    assets_schema = schema.Assets
    df = pd.DataFrame(
        [
            {
                assets_schema.DATABASE_NAME: "DB1",
                assets_schema.SCHEMA_NAME: "PUBLIC",
                assets_schema.ASSET_NAME: "VISIBLE_TABLE",
            },
            {
                assets_schema.DATABASE_NAME: "DB1",
                assets_schema.SCHEMA_NAME: "PRIVATE",
                assets_schema.ASSET_NAME: "HIDDEN_SCHEMA_TABLE",
            },
            {
                assets_schema.DATABASE_NAME: "DB2",
                assets_schema.SCHEMA_NAME: "PUBLIC",
                assets_schema.ASSET_NAME: "HIDDEN_DATABASE_TABLE",
            },
        ],
        index=[10, 20, 30],
    )

    result = frame.filter_rows_by_display_scopes(
        df,
        db_col=assets_schema.DATABASE_NAME,
        schema_col=assets_schema.SCHEMA_NAME,
        display_scopes=[{"DATABASE_NAME": "DB1", "SCHEMA_NAME": "PUBLIC"}],
    )

    assert result[assets_schema.ASSET_NAME].tolist() == ["VISIBLE_TABLE"]
    assert result.index.tolist() == [10]

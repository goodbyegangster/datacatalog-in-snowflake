# ruff: noqa: S101

from __future__ import annotations

from runtime import state, widget_state


def test_search_widget_keys_include_asset_user_and_tag_keys() -> None:
    keys = widget_state.search_widget_keys(
        [
            {
                "DATABASE_NAME": "DB",
                "SCHEMA_NAME": "SCHEMA",
                "TAG_NAME": "DOMAIN",
            }
        ]
    )

    assert state.SEARCH_ASSET_FREEWORD in keys
    assert state.SEARCH_ASSET_DATABASES in keys
    assert state.SEARCH_ASSET_OP_TAG in keys
    assert state.search_asset_tag_key("DB", "SCHEMA", "DOMAIN") in keys
    assert state.SEARCH_USER_ONLY_SELF not in keys
    assert state.SEARCH_USER_FREEWORD in keys

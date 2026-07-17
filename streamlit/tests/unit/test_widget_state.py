# ruff: noqa: S101

from __future__ import annotations

import pytest

from components.assets import search as asset_search
from runtime import state, widget_state


def test_search_widget_keys_include_asset_user_and_tag_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """検索ウィジェットの維持対象 key を返す。"""
    monkeypatch.setattr(
        asset_search,
        "SELECTABLE_TAG_KEYS",
        [
            {
                "DATABASE_NAME": "DB",
                "SCHEMA_NAME": "SCHEMA",
                "TAG_NAME": "DOMAIN",
            }
        ],
    )

    keys = widget_state.search_widget_keys()

    assert state.SEARCH_ASSET_FREEWORD in keys
    assert state.SEARCH_ASSET_DATABASES in keys
    assert state.SEARCH_ASSET_OP_TAG in keys
    assert state.search_asset_tag_key("DB", "SCHEMA", "DOMAIN") in keys
    assert state.SEARCH_USER_ONLY_SELF not in keys
    assert state.SEARCH_USER_FREEWORD in keys

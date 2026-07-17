# ruff: noqa: S101

from __future__ import annotations

import pytest

from views.common import error_handling


def test_render_catalog_load_error_hides_exception_outside_fake_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """fake mode 以外では traceback を表示しない。"""
    messages: list[str] = []
    exceptions: list[Exception] = []
    exc = RuntimeError("load failed")

    monkeypatch.setattr(error_handling.catalog, "data_mode", lambda: "snowflake")
    monkeypatch.setattr(error_handling.st, "error", messages.append)
    monkeypatch.setattr(error_handling.st, "exception", exceptions.append)

    error_handling.render_catalog_load_error(exc)

    assert messages == [error_handling.CATALOG_LOAD_ERROR_MESSAGE]
    assert exceptions == []


def test_render_catalog_load_error_shows_exception_in_fake_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """fake mode では traceback を表示する。"""
    messages: list[str] = []
    exceptions: list[Exception] = []
    exc = RuntimeError("load failed")

    monkeypatch.setattr(error_handling.catalog, "data_mode", lambda: "fake")
    monkeypatch.setattr(error_handling.st, "error", messages.append)
    monkeypatch.setattr(error_handling.st, "exception", exceptions.append)

    error_handling.render_catalog_load_error(exc)

    assert messages == [error_handling.CATALOG_LOAD_ERROR_MESSAGE]
    assert exceptions == [exc]

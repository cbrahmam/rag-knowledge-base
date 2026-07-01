"""Shared test fixtures.

Redirects the JSON-backed stores to a temporary directory so tests never
touch (or depend on) real local data.
"""
import pytest

from services import analytics, conversations, feedback


@pytest.fixture(autouse=True)
def isolate_stores(tmp_path, monkeypatch):
    monkeypatch.setattr(analytics, "ANALYTICS_STORE", tmp_path / "analytics.json")
    monkeypatch.setattr(feedback, "FEEDBACK_STORE", tmp_path / "feedback.json")
    monkeypatch.setattr(conversations, "CONVERSATIONS_STORE", tmp_path / "conversations.json")
    yield

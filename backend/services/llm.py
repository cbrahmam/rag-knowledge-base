"""Shared Anthropic client factory.

Centralizes API-key validation and client construction so the RAG and
summarization services don't each reimplement it.
"""
from __future__ import annotations

import os

import anthropic


def get_client() -> anthropic.Anthropic:
    """Return an Anthropic client, raising a clear error if the key is missing."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
    return anthropic.Anthropic(api_key=api_key)

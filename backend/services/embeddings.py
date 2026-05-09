from __future__ import annotations

import logging
from typing import List

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None
MODEL_NAME = "all-MiniLM-L6-v2"


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info("Loading embedding model %s (first load may download ~90MB)...", MODEL_NAME)
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Embedding model loaded successfully")
    return _model


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []

    model = _get_model()
    filtered = [t if t.strip() else " " for t in texts]
    embeddings = model.encode(filtered, show_progress_bar=False)
    return embeddings.tolist()

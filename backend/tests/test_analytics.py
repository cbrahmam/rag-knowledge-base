from models.schemas import RAGResponse, SourceCitation
from services import analytics


def _resp(confidence="high", ms=1200, sources=1):
    return RAGResponse(
        answer="a",
        sources=[
            SourceCitation(document=f"d{i}.md", page=None, chunk_text="t", relevance_score=0.8)
            for i in range(sources)
        ],
        confidence=confidence,
        chunks_searched=5,
        processing_time_ms=ms,
    )


def test_empty_summary():
    s = analytics.get_summary()
    assert s.total_queries == 0
    assert s.avg_processing_time_ms == 0
    assert s.confidence_distribution == {"high": 0, "medium": 0, "low": 0}


def test_log_and_aggregate():
    analytics.log_query("q1", _resp("high", 1000, 2))
    analytics.log_query("q2", _resp("low", 2000, 0))
    s = analytics.get_summary()
    assert s.total_queries == 2
    assert s.avg_processing_time_ms == 1500
    assert s.confidence_distribution["high"] == 1
    assert s.confidence_distribution["low"] == 1
    assert s.recent[0].question == "q2"  # most recent first


def test_history_and_clear():
    analytics.log_query("q", _resp())
    assert len(analytics.get_history()) == 1
    assert analytics.clear_history() == 1
    assert analytics.get_history() == []


def test_log_query_never_raises_on_bad_input():
    # Best-effort logging must not propagate errors into the query path.
    analytics.log_query("q", object())  # type: ignore[arg-type]

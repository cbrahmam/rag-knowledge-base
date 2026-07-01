from models.schemas import FeedbackRequest
from services import feedback


def _fb(rating):
    return FeedbackRequest(question="q", answer="a", rating=rating, confidence="high")


def test_empty_summary():
    s = feedback.get_summary()
    assert s.total == 0
    assert s.up == 0 and s.down == 0
    assert s.satisfaction_rate == 0.0


def test_log_and_summarize():
    feedback.log_feedback(_fb("up"))
    feedback.log_feedback(_fb("up"))
    feedback.log_feedback(_fb("down"))
    s = feedback.get_summary()
    assert s.total == 3
    assert s.up == 2 and s.down == 1
    assert s.satisfaction_rate == round(2 / 3 * 100, 1)


def test_clear():
    feedback.log_feedback(_fb("up"))
    assert feedback.clear_feedback() == 1
    assert feedback.get_summary().total == 0

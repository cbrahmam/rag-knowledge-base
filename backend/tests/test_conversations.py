from models.schemas import ConversationCreate
from services import conversations


def _create(messages=None, title=None):
    messages = messages or [{"role": "user", "content": "What is the policy?"}]
    return conversations.save_conversation(ConversationCreate(title=title, messages=messages))


def test_save_derives_title_from_first_user_message():
    conv = _create()
    assert conv.title == "What is the policy?"
    assert conv.id


def test_explicit_title_wins():
    conv = _create(title="My chat")
    assert conv.title == "My chat"


def test_list_get_and_delete():
    a = _create([{"role": "user", "content": "first"}])
    b = _create([{"role": "user", "content": "second"}])

    items = conversations.list_conversations()
    assert {i.id for i in items} == {a.id, b.id}

    got = conversations.get_conversation(a.id)
    assert got is not None and got.messages[0]["content"] == "first"

    assert conversations.delete_conversation(a.id) is True
    assert conversations.get_conversation(a.id) is None
    assert conversations.delete_conversation("missing") is False


def test_update_replaces_messages():
    conv = _create()
    updated = conversations.update_conversation(
        conv.id, ConversationCreate(messages=[{"role": "user", "content": "changed"}])
    )
    assert updated is not None
    assert updated.messages[0]["content"] == "changed"

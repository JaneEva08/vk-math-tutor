from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from models.user_data import UserData, ChatMessage
from services.ai_service import AIError
from services.openai_provider import OpenAIProvider
from services.tutor_service import prepare_topic, study_context
from tests.test_core import FakeMessage, env


def test_grade_and_topic_survive_history_reset():
    user = UserData.new(8)
    assert prepare_topic(user, "привет") is not None
    assert prepare_topic(user, "7 класс, дроби") is None
    user = UserData.from_dict(user.to_dict())
    assert user.settings["grade"] == 7
    assert user.active_dialog.study["topic"] == "дроби"
    assert "дроби" in study_context(user)


@pytest.mark.parametrize("grade", ["0", "12", "99"])
def test_invalid_grade_is_not_saved(grade):
    user = UserData.new(8)
    assert prepare_topic(user, grade)
    assert "grade" not in user.settings


async def test_tutor_onboarding_and_new_topic(env):
    h = env.handlers
    await h.on_message(FakeMessage("7"))
    assert not env.provider.calls
    await h.on_message(FakeMessage("дроби"))
    assert "класс=7" in env.provider.calls[0][0]
    assert "дроби" in env.provider.calls[0][0]
    user = await env.storage.load(1)
    assert user.active_dialog.study["exchanges"] == 1
    await h.on_message(FakeMessage(payload={"cmd": "topic"}))
    user = await env.storage.load(1)
    assert user.settings["grade"] == 7
    assert user.active_dialog.study == {} and user.active_dialog.messages == []
    await h.on_message(FakeMessage("проценты"))
    assert env.provider.calls[-1][1] == []
    assert "проценты" in env.provider.calls[-1][0]


async def test_provider_roles_usage_and_empty_response():
    reply = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Объяснение"))],
                            usage=SimpleNamespace(prompt_tokens=4, completion_tokens=2, total_tokens=6))
    create = AsyncMock(return_value=reply)
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    provider = OpenAIProvider("test", "test", "https://example.test", client=client)
    assert await provider.generate("правила", [ChatMessage("assistant", "раньше")], "вопрос") == "Объяснение"
    assert [m["role"] for m in create.call_args.kwargs["messages"]] == ["system", "assistant", "user"]
    assert provider.last_usage["total_tokens"] == 6
    reply.choices[0].message.content = " "
    with pytest.raises(AIError):
        await provider.generate("правила", [], "вопрос")


async def test_failed_first_reply_preserves_study_facts(env):
    env.provider.fail = True
    await env.handlers.on_message(FakeMessage("7 класс, дроби"))
    user = await env.storage.load(1)
    assert user.settings["grade"] == 7
    assert user.active_dialog.study["topic"] == "дроби"
    assert user.active_dialog.messages == []

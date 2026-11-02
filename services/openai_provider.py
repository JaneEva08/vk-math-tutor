"""OpenAI-совместимый API с ограничением времени и безопасными ошибками."""
from openai import AsyncOpenAI, OpenAIError


class OpenAIProvider:
    def __init__(self, api_key, model, base_url, client=None):
        self.model = model
        self._client = client or AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=60.0, max_retries=1)
        self.last_usage = {}

    async def generate(self, system_prompt, history, user_message):
        from services.ai_service import AIError
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend({"role": m.role, "content": m.content} for m in history)
        messages.append({"role": "user", "content": user_message})
        try:
            response = await self._client.chat.completions.create(
                model=self.model, messages=messages, max_completion_tokens=1800,
            )
            text = (response.choices[0].message.content or "").strip()
        except (OpenAIError, IndexError, AttributeError) as exc:
            raise AIError(type(exc).__name__) from None
        if not text:
            raise AIError("EmptyResponse")
        u = response.usage
        self.last_usage = {"prompt_tokens": u.prompt_tokens, "completion_tokens": u.completion_tokens,
                           "total_tokens": u.total_tokens} if u else {}
        return text

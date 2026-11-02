"""Проверка подключения без отправки сообщений в VK и без сохранения ключей в отчёт."""
import asyncio
import json
import sys

from config.settings import get_settings
from config.prompts import get_mode
from services.openai_provider import OpenAIProvider


async def main():
    s = get_settings()
    s.validate()
    if "--ai" in sys.argv:
        p = OpenAIProvider(s.openai_api_key, s.openai_model, s.openai_base_url)
        try:
            answer = await p.generate(get_mode("math").system_prompt,
                                      [], "Я в 7 классе. Объясни линейные уравнения: один небольшой шаг и один вопрос.")
            print(json.dumps({"model": s.openai_model, "answer": answer, "usage": p.last_usage}, ensure_ascii=False))
        except Exception as e:
            print("AI_PROBE_FAILED", type(e).__name__)
            raise SystemExit(1) from None
        finally:
            await p._client.close()
    if "--vk" in sys.argv:
        from vkbottle import API
        api = API(token=s.vk_token)
        try:
            permissions = await api.groups.get_token_permissions()
            lp = await api.groups.get_long_poll_settings(group_id=s.vk_group_id)
            print("VK_OK", "permissions_mask=", permissions.mask,
                  "long_poll=", lp.is_enabled, "message_new=", lp.events.message_new)
        except Exception as e:
            print("VK_PROBE_FAILED", type(e).__name__)
            raise SystemExit(1) from None
        finally:
            await api.http_client.close()


if __name__ == "__main__":
    asyncio.run(main())

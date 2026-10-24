"""Прямой запрос к Gemini через ProxyAPI (Google GenAI SDK).

Запуск из корня проекта: python examples/gemini_proxyapi_example.py
"""

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(
    api_key=os.environ["PROXY_API_KEY"],
    http_options=types.HttpOptions(base_url=os.getenv("GEMINI_BASE_URL", "https://api.proxyapi.ru/google")),
)
response = client.models.generate_content(
    model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
    contents="Привет!",
)
print(response.text)
print(response.usage_metadata)  # токены запроса/ответа — для отчёта по ДЗ

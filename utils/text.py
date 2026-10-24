"""Работа с текстом сообщений: очистка Markdown и разбиение по длине."""

import re


def strip_markdown(text: str) -> str:
    """ВКонтакте не рендерит Markdown — убираем разметку."""
    text = re.sub(r"```[a-zA-Z0-9]*\n?", "", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"(?<!\*)\*(?!\s)([^*\n]+?)\*(?!\*)", r"\1", text)
    text = re.sub(r"^\s*[*+]\s+", "- ", text, flags=re.MULTILINE)
    return text.replace("`", "").strip()


def split_message(text: str, limit: int) -> list[str]:
    """Делит длинный ответ на части <= limit, стараясь резать по переносам строк."""
    chunks: list[str] = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = text.rfind(" ", 0, limit)
        if cut < limit // 2:
            cut = limit
        chunks.append(text[:cut].rstrip())
        text = text[cut:].lstrip()
    if text:
        chunks.append(text)
    return chunks

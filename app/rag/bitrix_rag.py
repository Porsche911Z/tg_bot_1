

from pathlib import Path
import re
from typing import List, Tuple

DOCS_PATH = Path("data/bitrix_docs")
MAX_CONTEXT_CHARS = 3000


def load_documents() -> List[Tuple[str, str]]:
  
    documents = []
    if not DOCS_PATH.exists():
        return documents

    for file in DOCS_PATH.glob("*.txt"):
        text = file.read_text(encoding="utf-8")
        documents.append((file.name, text))

    return documents


def score_document(question: str, text: str) -> int:
   
    words = re.findall(r"[a-zA-Zа-яА-Я\.]+", question.lower())
    score = 0
    text_lower = text.lower()

    for w in words:
        if len(w) > 3:
            score += text_lower.count(w)

    return score


def retrieve_context(question: str, top_k: int = 3) -> str:
   
    documents = load_documents()

    if not documents:
        return ""

    scored = []
    for name, text in documents:
        score = score_document(question, text)
        if score > 0:
            scored.append((score, name, text))

    # если ничего не найдено — берём первые документы
    if not scored:
        scored = [(1, name, text) for name, text in documents]

    scored.sort(reverse=True, key=lambda x: x[0])

    context_parts = []
    current_length = 0

    for _, name, text in scored[:top_k]:
        header = f"\n\n### Документ: {name}\n"
        part = header + text
        if current_length + len(part) > MAX_CONTEXT_CHARS:
            break
        context_parts.append(part)
        current_length += len(part)

    return "".join(context_parts)


if __name__ == "__main__":
    # простой тест
    q = "Как создать сделку в Bitrix24 через API?"
    print(retrieve_context(q))
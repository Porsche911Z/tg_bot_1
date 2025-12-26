
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from yandex_cloud_ml_sdk import YCloudML, AssistantTextSearchIndex, File


load_dotenv()

FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")          
AUTH_TOKEN = os.getenv("YANDEX_API_KEY")           

DOCS_DIR = Path("data/bitrix_docs")
MAX_CONTEXT_CHARS = 8000   

sdk = YCloudML(
    folder_id=FOLDER_ID,
    auth=AUTH_TOKEN,           
)


def ensure_search_index(index_name: str = "bitrix24-api-docs") -> AssistantTextSearchIndex:
    """
    Создаёт (или находит существующий) текстовый поисковый индекс
    """

    for idx in sdk.assistants.search_indexes():
        if idx.name == index_name:
            return idx

    print(f"Создаём новый поисковый индекс: {index_name}")
    index = sdk.assistants.create_search_index(
        name=index_name,
        description="База знаний по API Bitrix24",
    )
    return index


def upload_and_index_documents(index: AssistantTextSearchIndex):
    """
    Загружает все .txt / .md файлы из папки и добавляет их в индекс
    """
    if not DOCS_DIR.exists():
        print("Папка с документами не найдена:", DOCS_DIR)
        return

    uploaded_count = 0

    for file_path in DOCS_DIR.glob("*.*"):
        if file_path.suffix.lower() not in (".txt", ".md", ".pdf"):
            continue

        print(f"Загружаем {file_path.name} ...")

        yc_file: File = sdk.files.upload(str(file_path))

        index.add_file(yc_file)

        uploaded_count += 1

    if uploaded_count > 0:
        print(f"Успешно добавлено {uploaded_count} документов в индекс")
    else:
        print("Не найдено подходящих документов для индексации")


def get_rag_context(question: str, top_k: int = 5) -> str:
    """
    Основная функция: получает релевантный контекст через Yandex AI Assistant Search Index
    """
    index = ensure_search_index()


    results = index.search(
        query=question,
        limit=top_k,
    )

    if not results:
        return ""

    context_parts = []

    for item in results:
        header = f"\n\n### Документ: {item.metadata.get('file_name', 'без имени')}\n"
        context_parts.append(header + item.text)

    context = "".join(context_parts)
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS] + "\n... (контекст обрезан)"

    return context


def ask_question_with_rag(question: str) -> str:
    """
    Пример: как можно использовать полученный контекст + YandexGPT
    """
    context = get_rag_context(question, top_k=4)

    if not context:
        return "К сожалению, в базе знаний ничего не нашлось по этому вопросу."

    prompt = f"""Ты — эксперт по API Bitrix24.
Отвечай только на основе предоставленной ниже информации из документации.
Если в документах нет ответа — скажи об этом честно.

Контекст из базы знаний:
{context}

Вопрос пользователя: {question}

Ответ:"""


    model = sdk.models.completions("yandexgpt")  
    model = model.configure(temperature=0.3, max_tokens=1500)

    result = model.run(prompt)

    return result[0].text   


if __name__ == "__main__":

    question = "Как создать сделку в Bitrix24 через REST API?"
    print("Вопрос:", question)
    print("-" * 60)
    answer = ask_question_with_rag(question)
    print(answer)
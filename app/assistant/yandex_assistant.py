import os
import requests
from app.rag.bitrix_rag import retrieve_context

YANDEX_GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"


def ask_yandex_assistant(question: str) -> str:

    YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
    YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

    if not YANDEX_API_KEY or not YANDEX_FOLDER_ID:
        return "❌ Yandex Assistant не настроен. Проверьте переменные окружения."

    context = retrieve_context(question)

    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0.2,
            "maxTokens": 500
        },
        "messages": [
            {
                "role": "system",
                "text": (
                    "Ты технический ассистент по API Bitrix24. "
                    "Отвечай ТОЛЬКО используя документацию ниже.\n\n"
                    f"{context}"
                )
            },
            {
                "role": "user",
                "text": question
            }
        ]
    }

    response = requests.post(
        YANDEX_GPT_URL,
        headers=headers,
        json=payload,
        timeout=30
    )

    if response.status_code != 200:
        return f"❌ Ошибка Yandex Assistant: {response.text}"

    result = response.json()
    return result["result"]["alternatives"][0]["message"]["text"]
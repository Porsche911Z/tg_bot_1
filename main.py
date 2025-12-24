import logging
import os
from pathlib import Path
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from app.assistant.yandex_assistant import ask_yandex_assistant
from app.database.db import engine, Base, SessionLocal
from app.database.models import User
from app.database.crud import get_or_create_user, save_message

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

BOT_TOKEN = os.getenv("BOT_TOKEN")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

print("ENV LOADED FROM:", ENV_PATH)
print("BOT_TOKEN:", BOT_TOKEN)
print("YANDEX_API_KEY:", YANDEX_API_KEY)
print("YANDEX_FOLDER_ID:", YANDEX_FOLDER_ID)

Base.metadata.create_all(bind=engine)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Я чат-бот для помощи разработчикам Bitrix24.\n"
        "Задайте вопрос по API Bitrix24, и я отвечу, используя документацию Bitrix24."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    try:
        tg_user = update.message.from_user
        user = get_or_create_user(
            db,
            telegram_id=str(tg_user.id),
            username=tg_user.username
        )

        question = update.message.text
        logger.info(f"Вопрос пользователя {tg_user.id}: {question}")

        await update.message.reply_text(" Думаю над ответом...")

        answer = ask_yandex_assistant(question)

        save_message(db, user, question, answer)

        await update.message.reply_text(answer)
    finally:
        db.close()

def main():
    if not BOT_TOKEN:
        raise RuntimeError("Не найден BOT_TOKEN в .env файле")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
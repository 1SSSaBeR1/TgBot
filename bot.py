from sqlalchemy import engine, create_engine
from sqlalchemy.orm import sessionmaker
import logging
import sqlite3

from telegram.ext import Application, MessageHandler, filters, ConversationHandler, Updater
from telegram.ext import CommandHandler
from telegram import ReplyKeyboardMarkup
from telegram import ReplyKeyboardRemove
from data.links import Link

sqlite_database = "sqlite:///links.db"
engine = create_engine(sqlite_database, echo=True)
Session = sessionmaker(bind=engine)
session = Session()
reply_keyboard = [['/start', '/help', 'close']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)

async def link(update, context):
    await update.message.reply_text(
        "Напишите сюда свою ссылку")
    return 1

def handle_link(update, context):
   link = Link(url=update.message.text, description="todo")
   session.add(link)
   session.commit()
   context.bot.send_message(chat_id=update.effective_chat.id, text=f"Получил ссылку: {link}, сохранил её, чтобы посмотреть её нажмите /see")


async def first_response(update, context):
    context.user_data['save_link'] = update.message.text
    await update.message.reply_text(
        f"вот ваша ссылка {context.user_data['save_link']}")
    return 2


async def second_response(update, context):
    weather = update.message.text
    logger.info(weather)
    await update.message.reply_text(
        f"Спасибо за участие в опросе! Привет, {context.user_data['locality']}!")
    context.user_data.clear()


async def stop(update, context):
    await update.message.reply_text("Всего доброго!")
    return ConversationHandler.END

async def help_command(update, context):
    """Отправляет сообщение когда получена команда /help"""
    await update.message.reply_text("Я пока не умею помогать... Я только ваше эхо.",
                                    reply_markup=markup
                                    )
async def close_keyboard(update, context):
    await update.message.reply_text(
        "Ok",
        reply_markup=ReplyKeyboardRemove())

async def start(update, context):
    await update.message.reply_text(
        "Дабро пожадовать в рекомендательный бот\n"
        "Вы можете сюросить разговор нажав/stop.\n"
        "Чтобы сохранить сылку нажмите /link и отправьте ссылку"
        "")
    return 1
def see(update, context):
    link = session.query(Link).filter_by(url="link").first()
    print(link.description)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)

def main():
    application = Application.builder().token("6363585289:AAGB2GZRVKahUXlU7SAe5A2AUJt4X1UWMEc").build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, first_response)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, second_response)]
        },

        fallbacks=[CommandHandler('stop', stop)]
    )

    conv_handler1 = ConversationHandler(
        entry_points=[CommandHandler('link', link)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    application.add_handler(conv_handler1)
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("close", close_keyboard))

if __name__ == '__main__':
    main()



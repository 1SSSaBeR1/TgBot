import logging
from sqlalchemy import engine, create_engine, select, update as sql_update
from sqlalchemy.orm import sessionmaker
import sqlite3

from sqlalchemy.sql.expression import func
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Update,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
)
from telegram import ReplyKeyboardRemove
from data.links import Link

sqlite_database = "sqlite:///db//links.db"
engine = create_engine(sqlite_database, echo=True)
Session = sessionmaker(bind=engine)
session = Session()
reply_keyboard = [["/link", "/see", "1"]]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text="Напишите сюда свою ссылку",
        reply_markup=markup
    )
    return 1


def get_tags_from_db():
    return ["Познавательно", "Развличения", "Другое"]


def generate_tags_battons(list_tags):
    res = [
        [InlineKeyboardButton(text="- " + tag, callback_data=f"tag_choice:{tag}")]
        for tag in list_tags
    ]
    return res


async def handle_link(update: Update, context):
    link = Link(
        url=update.message.text, user_id=update.message.from_user.id, description="todo"
    )
    session.add(link)
    session.commit()
    # тут нужно добавить в базу данных url и получить id записи
    tag_list = get_tags_from_db()
    buttons = generate_tags_battons(tag_list)
    buttons.append(
        [
            InlineKeyboardButton(
                text="Добавить выбранные теги", callback_data=f"added_tags:{link.id}"
            )
        ]
    )
    keyboard = InlineKeyboardMarkup(buttons)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Добавьте теги для ссылки: {update.message.text}",
        reply_markup=keyboard,
    )

    return 2


async def first_response(update, context):
    context.user_data["save_link"] = update.message.text
    await update.message.reply_text(f"вот ваша ссылка {context.user_data['save_link']}")
    return 2


async def second_response(update, context):
    weather = update.message.text
    await update.message.reply_text(
        f"Спасибо за участие в опросе! Привет, {context.user_data['locality']}!"
    )
    context.user_data.clear()
    return ConversationHandler.END


async def stop(update, context):
    await update.message.reply_text("Всего доброго!")
    return ConversationHandler.END


async def help_command(update, context):
    """Отправляет сообщение когда получена команда /help"""
    await update.message.reply_text(
        "Я пока не умею помогать... Я только ваше эхо."
    )


async def close_keyboard(update, context):
    await update.message.reply_text("Ok", reply_markup=ReplyKeyboardRemove())


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text="Дабро пожадовать в рекомендательный бот\n"
        "Вы можете сюросить разговор нажав/stop.\n"
        "Чтобы сохранить сылку нажмите /link и отправьте ссылку \n"
             "Чтобы посмотреть видео, воспользуйтесь /see"
    )


async def see(update, context):
    stmt = (
        select(Link)
        .where(Link.is_complited == False, Link.user_id == update.message.from_user.id)
        .order_by(func.random())
        .limit(1)
    )
    link = session.execute(stmt).scalar()
    if link:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "заверишть", callback_data=f"complite_url:{link.id}"
                    ), InlineKeyboardButton(
                    "не посмотрел", callback_data=f"not_complite_url: {link.url}")
                ]
            ]
        )
        context.user_data['current_question'] = link.id
        await update.message.reply_text(link.url, reply_markup=keyboard)

        return 4
    await update.message.reply_text("ссылок нет")
    return ConversationHandler.END
    # await update.message.reply_text(
    #     "вы можете выбрать тэг, по которому вы хотите посмотреть видео",
    #     reply_markup=markup,
    # )


async def url(update, context):
    await update.message.reply_text(text=
                                'и не забудьте завершить ссылку')
    question_id = context.user_data.get("current_question")

    await update.message.reply_text(f'создан комментарий для ссылки с id {question_id}')
    return 4


async def update_tag_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _, tag = update.callback_query.data.split(":")
    keyboard = []
    for button in update.callback_query.message.reply_markup.inline_keyboard:
        if button[0].callback_data.endswith(tag):
            text_prefix, *text = button[0].text.split()
            if text_prefix == "-":
                text = "+ " + " ".join(text)
            else:
                text = "- " + " ".join(text)
        else:
            text = button[0].text
        keyboard.append(
            [InlineKeyboardButton(text, callback_data=button[0].callback_data)]
        )
    await update.callback_query.edit_message_text(
        text=update.callback_query.message.text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return 2


async def added_tags_for_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = []
    for button in update.callback_query.message.reply_markup.inline_keyboard:
        if button[0].callback_data.startswith("tag_choice:"):
            symbol, *tag = button[0].text.split()
            if symbol == "+":
                res.append(" ".join(tag))

    # удаляем работу с тегами
    await update.callback_query.delete_message()
    await update.callback_query.message.reply_text(
        "Теги были добавленны:\n" + "\n".join(res)
    )
    return ConversationHandler.END


async def complite_url_hendler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    *_, link_id = update.callback_query.data.split(":")
    stmt = sql_update(Link).where(Link.id == int(link_id)).values(is_complited=True)
    session.execute(stmt)
    session.commit()
    await update.callback_query.delete_message()
    await update.callback_query.message.reply_text(
        "Поздравляю с просмотром!"
    )
    return ConversationHandler.END

async def not_complite_url(update: Update, cotext: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text(text="завершаем процесс")
    await update.callback_query.delete_message()
    await update.callback_query.message.reply_text(
        "Ссылка продолжает функционировать"
    )
    return ConversationHandler.END



def main():
    application = (
        Application.builder()
        .token("6363585289:AAGB2GZRVKahUXlU7SAe5A2AUJt4X1UWMEc")
        .build()
    )
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("link", link), CommandHandler("see", see)],
        states={
            # ждем текстового сообщения с сылкой, потом отправляем интерфейс управления тегами и переходим в режим изменения тегов
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link)],
            # режим работы с тегами
            2: [
                # в режиме изменения тегов фиксируем изменения и обновляем кнопки
                CallbackQueryHandler(update_tag_choice, pattern="^" + "tag_choice:"),
                # в режиме изменения тегов нажимам кнопку принять (выводим соощения успех) завершаем сценарий
                CallbackQueryHandler(added_tags_for_url, pattern="^" + "added_tags:"),
                # в режиме изменения тегов нажимаем кнопку добавить новый тег, выводим сообщение о необходимости ввевсти называние нового тега, переключаем в режим нового тега
                # CallbackQueryHandler(adding_self, pattern="^" + str(ADDING_SELF) + "$"),
                # в режиме изменения тегов нажимаем кнопку оставить без тега
                # CallbackQueryHandler(end, pattern="^" + str(END) + "$"),
            ],
            # режим добавления тегов
            3: [
                # в режиме добавления тегов вводим текст
                # MessageHandler(filters.TEXT & ~filters.COMMAND, second_response),
                # в режимe добавления тегов нажимаем назад
                # CallbackQueryHandler(show_data, pattern="^" + str(SHOWING) + "$"),
            ],
            4: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, url),
                CallbackQueryHandler(
                    complite_url_hendler, pattern="^" + "complite_url:"
                ), CallbackQueryHandler(not_complite_url, pattern="^" + "not_complite_url:"),
            ],
            5: [CallbackQueryHandler(update_tag_choice, pattern="^" + "tag_choice:")],
        },
        fallbacks=[
            CommandHandler("stop", stop),
            # любой ввод текст не по плану приводит к завершению сценария
            MessageHandler(filters.TEXT, stop),
        ],
    )

    # в случае команды старт не запускаем сценарий, а просто выводим подсказки
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    # application.add_handler(conv_handler1)
    # application.add_handler(CommandHandler("help", help_command))
    # application.add_handler(CommandHandler("close", close_keyboard))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()



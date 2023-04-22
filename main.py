import sqlite3
from telegram.ext import Application, MessageHandler, filters
from telegram.ext import CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)

con = sqlite3.connect("database.db")
cur = con.cursor()
body = 0
reply_keyboard = [['/login'],
                  ['/signup']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
idk = None


async def start(update, context):
    if body == 0:
        await update.message.reply_text(
            "Здравствуйте. Для начала войдите в свой аккаунт или создайте новый!",
            reply_markup=markup)
    else:
        await update.message.reply_text(
            "Вы уже вошли в свой аккаунт")


async def loginner(update, context):
    await update.message.reply_text("Пожалуйста, отправьте ваш Яндекс_ID:")
    return 3


async def signupper(update, context):
    await update.message.reply_text("Пожалуйста, отправьте ваш Яндекс_ID:")
    return 4


async def login(update):
    user_id = update.message.from_user.id
    update.message.reply_text(f'Пожалуйста, отправьте ваш Яндекс_ID:', reply_markup=ReplyKeyboardRemove())
    res = cur.execute(f"SELECT first_name, last_name FROM accounts"
                      f"WHERE yandex_id == {user_id}").fetchall()
    if len(res) == 0:
        await update.message.reply_text(f'Простите, но аккаунта с таким id не существует.')
    else:
        await update.message.reply_text(f'С возвращением, {res[0], res[1]}')
        update.message.delete(update.message.text)
        body = 1


async def signup(update, context):
    user_id = update.message.text
    res = cur.execute(f'SELECT account_id FROM teachers WHERE account_id == {user_id}').fetchall()
    if len(res) != 0:
        await update.message.reply_text(f'Простите, но аккаунт с таким id уже существует.')
    else:
        await update.message.reply_text(f'Добро пожаловать в наш школьный мир!')


async def exitor(update, context):
    await update.message.reply_text("Вы вышли из своего аккаунта. До свидания!")
    body = 0
    return ConversationHandler.END


async def send(update, context):
    await update.message.reply_text(
        "Введите имя и фамилию отправителя, первая буква имени и первая буква фамилии ЗАГЛАВНАЯ,"
        "все остальные символы - строчные буквы, иных символов быть не должно")
    return 1


async def idir(update, context):
    global idk
    first_name, last_name = update.message.text.split()
    res = cur.execute(f"SELECT yandex_id FROM accounts WHERE first_name = {first_name} AND"
                      f" last_name = {last_name}").fetchall()
    if len(res) == 0:
        await update.message.reply_text('Вы отправили не тот id')
        return 1
    else:
        idk = update.message.text
        await update.message.reply_text('Введите ваше сообщение:')
        return 2


async def is_sent(update, context):
    text = f'Сообщение от{update.from_user.first_name, update.from_user.last_name}: {update.message.text}'
    await update.message.text(text, id=idk)
    await update.message.reply_text("Все отправлено!")


def main():
    application = Application.builder().token('6232251709:AAFyEC6d0nKHHnW9ICwmUXJcLRqPocyeffo').build()
    conv_handler = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /start. Она задаёт первый вопрос.
        entry_points=[CommandHandler('start', start)],

        # Состояние внутри диалога.
        # Вариант с двумя обработчиками, фильтрующими текстовые сообщения.
        states={
            # Функция читает ответ на первый вопрос и задаёт второй.
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, login)],
            # Функция читает ответ на второй вопрос и завершает диалог.
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, signup)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, loginner)],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, signupper)]
        },

        fallbacks=[CommandHandler('exit', exitor)]
    )
    sender = ConversationHandler(
        entry_points=[CommandHandler('send', send)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, idir)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, is_sent)]
        },
        fallbacks=[CommandHandler('exit', is_sent)]
    )
    application.add_handler(conv_handler)
    application.add_handler(sender)
    application.add_handler(CommandHandler("login", loginner))
    application.add_handler(CommandHandler("signup", signupper))

    application.run_polling()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()

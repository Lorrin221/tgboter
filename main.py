import sqlite3
from telegram.ext import Application, MessageHandler, filters
from telegram.ext import CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import requests

TOKEN = '6232251709:AAFyEC6d0nKHHnW9ICwmUXJcLRqPocyeffo'  # Токен бота
signin = []  # Здесь хранятся данные для регистрации
con = sqlite3.connect("database.db")  # Подключение к БД, где хранится информация обо всех пользователях
cur = con.cursor()
body = None  # Если вход выполнен, body=(имя_пользователя, фамилия_пользователя), иначе body=None
reply_keyboard = [['/login'],
                  ['/signup'],
                  ['/help']]  # Простая клавиатура старта
markup = ReplyKeyboardMarkup(reply_keyboard,
                             one_time_keyboard=False)  # Когда бот начинает работу, просит пользователя зарегистрироваться или войти
keyb = [['/friends'],
        ['/send_friend'],
        ['/send'],
        ['/anonym_send'],
        ['/exit']]  # Основная клавиатура
mrkup = ReplyKeyboardMarkup(keyb, one_time_keyboard=False)



def password_level(word):  # Для проверки пароля
    if len(word) < 6:
        return 'Недопустимый пароль'
    else:
        dig = '0123456789'
        lit = 'abcdefghijklmnopqrstuvwxyzабвгдеёжзийклмнопрстуфхцчшщъыьэяю'
        big = lit.upper()
        d_c = 0
        l_c = 0
        b_c = 0
        for x in word:
            if x in dig and d_c == 0:
                d_c += 1
            elif x in big and b_c == 0:
                b_c += 1
            elif x in lit and l_c == 0:
                l_c += 1
        if d_c + l_c + b_c == 3:
            return 'Надежный пароль'
        elif d_c + l_c + b_c == 2:
            return 'Слабый пароль'
        else:
            return 'Ненадежный пароль'


async def helper(update, context):  # Для изучения интерфейса
    text = ['Команды для работы с ботом:',
            '"/login" - вход в аккаунт',
            '"/signup" - регистрация в аккаунте',
            '"/friends" - показывает всех ваших друзей',
            '"/send_friend" - отправляет запрос на дружбу другому пользователю',
            '"/send" - отправляет сообщение вашему контакту(другу)',
            '"/anonym_send" - отправляет анонимное сообщение вашему контакту(другу)'
            '"/cancel" - отменяет начатое действие',
            '"/exit" - выход из аккаунта']
    await update.message.reply_text("\n".join(text))


async def start(update, context):
    if not (body):
        await update.message.reply_text(
            "Здравствуйте. Для начала войдите в свой аккаунт или создайте новый!\n"
            "Хотите изучить интерфейс? нажмите на кнопку help или вбейте /help!",
            reply_markup=markup)
    else:
        await update.message.reply_text(
            "Вы уже вошли в свой аккаунт")


async def signupper(update,
                    context):  # 1 шаг: Начало созания аккаунта, введение имени пользователя(Вход после регистрации выполнятся не будет)
    global signin
    signin = []
    if len(cur.execute(
            f'SELECT * FROM accounts WHERE id = {update.message.from_user.id}').fetchall()) > 0:  # Если id уже есть в БД, регистрация невозможна
        await update.message.reply_text("Извините, но вы уже зарегистрированы")
        return ConversationHandler.END
    await update.message.reply_text("Введите свое имя:")
    return 1  # переход на шаг sig_1


async def sig_1(update, context):  # 2 шаг: введение фамилии пользователя
    global signin
    signin.append(update.message.text.capitalize())  # Добавляем введенное имя
    await update.message.reply_text("Введите свою фамилию:")
    return 2  # переход на шаг sig_2


async def sig_2(update, context):  # шаг 3: вводим пароль
    global signin
    signin.append(update.message.text.capitalize())  # Добавляем введенную фамилию
    await update.message.reply_text("Придумайте пароль (длина более 5 символов, должны быть цифры и"
                                    " буквы разных регистров, иных символов быть не должно, "
                                    "после введения ваше сообщение с паролем удалится, поэтому запомните его сейчас):")
    return 3  # переход на шаг sig_3


async def sig_3(update, context):
    global signin
    if password_level(update.message.text) == 'Надежный пароль':  # Если пароль прошел проверку
        await update.message.delete()
        signin.insert(0, update.message.text)  # Добавляем пароль
        cur.execute(f'CREATE TABLE IF NOT EXISTS accounts '
                    f'(id INTEGER PRIMARY KEY UNIQUE, '
                    f'password TEXT, '
                    f'first_name TEXT,'
                    f'last_name TEXT,'
                    f'chat_id INTEGER);')  # Создаем таблицу accounts, если она не существует
        cur.execute(f"INSERT INTO accounts(id,password,first_name,last_name,chat_id) VALUES(?,?,?,?,?)",
                    (update.message.from_user.id,
                     *signin, update.message.chat_id))  # Создаем в таблице accounts запись об пользователе
        cur.execute(f'CREATE TABLE IF NOT EXISTS {signin[1].capitalize()}_{signin[2].capitalize()} '
                    f'(id INTEGER UNIQUE, first_name TEXT, last_name TEXT);')  # Таблица для контактов - друзей пользователя
        con.commit()
        await update.message.reply_text("Поздравляем с регистрацией!")
        return ConversationHandler.END
    else:
        await update.message.reply_text(f'{password_level(update.message.text)} Введите новый пароль')
        return 3


async def loginner(update, context):  # Вход в аккаунт, стартовая точка
    global body
    if not(body):
        res = cur.execute(f'SELECT * FROM accounts WHERE id = {update.message.from_user.id}').fetchall()
        if len(res) == 0:
            await update.message.reply_text("Вы еще не зарегистрированы! Пожалуйста, зарегистрируйтесь!")
            return -1
        await update.message.reply_text("Пожалуйста, введите ваш пароль:",
                                        reply_markup=ReplyKeyboardRemove())  # Просьба ввести пароль,
        # удаляем клавиатуру
        return 1  # переход на шаг login
    else:
        await update.message.reply_text('Вход уже выполнен!')
        return ConversationHandler.END


async def login(update, context):  # Сам процесс входа
    global body
    res = cur.execute(f"SELECT first_name, last_name FROM accounts "
                      f"WHERE password='{update.message.text}'").fetchall()  # Проверяем введенный пароль
    if len(res) == 0:
        await update.message.reply_text(f'Неверный пароль! Поменяйте его или введите заново')
        return 1
    else:
        await update.message.reply_text(f'С возвращением, {res[0][0]} {res[0][1]}', reply_markup=mrkup)
        await update.message.delete()  # Удаляем сообщение с правильным паролем
        body = (res[0][0], res[0][1])  # Вход выполнен
        return ConversationHandler.END


async def cancel(update, context):  # Отменим действие
    await update.message.reply_text("Действие отменено!", reply_markup=mrkup)
    return ConversationHandler.END  # Если был диалог, он завершается


async def friender(update, context):  # Отправим контакту запрос на дружбу
    global body
    if not (body):
        await update.message.reply_text("Для начала войдите в аккаунт!")
        return ConversationHandler.END
    await update.message.reply_text('Отправьте имя и фамилию пользователя, с кем хотите дружить (через пробел)',
                                    reply_markup=ReplyKeyboardMarkup([['/cancel'], ['/exit']], one_time_keyboard=False))
    return 1


async def friend_1(update, context):
    global body
    text = list(update.message.text.split())
    res = cur.execute('SELECT chat_id FROM accounts WHERE first_name=? and last_name=?', (text[0], text[1])).fetchall()#Проверим существование аккаунта
    if len(res) == 0:
        await update.message.reply_text('Такого пользователя нет! Попробуйте еще раз!')
        return 1
    else:
        otp = cur.execute(f'SELECT id, first_name, last_name FROM accounts '
                          f'WHERE chat_id = {res[0][0]}').fetchall()
        params = {
            'chat_id': res[0][0],
            'text': f"Вам отправлен запрос на дружбу от {body[0]} {body[1]}"
        }
        cur.execute(f'INSERT INTO {body[0]}_{body[1]}(id, first_name, last_name) VALUES(?,?,?);',
                    *otp)# В таблицу отправителя добавляется получатель
        cur.execute(f'INSERT INTO {otp[0][1]}_{otp[0][2]}(id, first_name, last_name) VALUES(?,?,?);',
                    (update.message.from_user.id, *body)) # В таблицу получателя добавляется отправитель
        con.commit()
        response = requests.get(f'https://api.telegram.org/bot{TOKEN}/sendMessage', params=params) #Отправим сообщение получателю
        await update.message.reply_text('Запрос отправлен!')
        return ConversationHandler.END


async def send(update, context):  # Отправим сообщение своему контакту
    global body
    if not(not(body)):
        res = cur.execute(f'SELECT first_name, last_name FROM {body[0]}_{body[1]}').fetchall() #Получаем список контактов
        if len(res) > 0: #Есть ли вообще контакты
            buttons = [[' '.join(x)] for x in res]
            buttons.append(['/cancel'])
            buttons.append(['/exit'])
            contacts = ReplyKeyboardMarkup(buttons, one_time_keyboard=True)
            await update.message.reply_text(
                "Выберите пользователя, которому хотите отправить сообщение:", reply_markup=contacts)
            return 1
        else: #Если нет, завершаем диалог
            await update.message.reply_text('У вас нет друзей!')
            return ConversationHandler.END
    else:
        await update.message.reply_text(
            "Для начала войдите в аккаунт!")
        return ConversationHandler.END


async def idir(update, context): #Проверка корректности аккаунта и ввод сообщения
    global idk # Сюда запишем id чата бота и получателя
    first_name, last_name = update.message.text.split()
    res = cur.execute(f'SELECT chat_id FROM accounts '
                      f'WHERE first_name=? AND last_name=?', (first_name, last_name)).fetchall()#Нужно будет для сообщения
    if len(res) == 0: # Нет такого пользователя
        await update.message.reply_text('Такого пользователя нет! Попробуйте еще раз')
        return 1
    else:
        idk = res[0][0]
        await update.message.reply_text('Введите ваше сообщение:',
                                        reply_markup=ReplyKeyboardMarkup([['/cancel'], ['/exit']], one_time_keyboard=False))
        return 2


async def is_sent(update, context): # Отправляем сообщение
    global idk
    text = f'Вам сообщение от {body[0]} {body[1]}:\n{update.message.text}'
    params = {
        'chat_id': idk,
        'text': text
    }
    response = requests.get(f'https://api.telegram.org/bot{TOKEN}/sendMessage', params=params)
    await update.message.reply_text("Все отправлено!", reply_markup=mrkup)

# Следующие 3 команды работают аналогично 3 предыдущим, но для анонимного чата
async def anonym_send(update, context):  # Отправим сообщение своему контакту
    global body
    if not(not(body)):
        res = cur.execute(f'SELECT first_name, last_name FROM {body[0]}_{body[1]}').fetchall()
        if len(res) > 0:
            buttons = [[' '.join(x)] for x in res]
            buttons.append(['/cancel'])
            buttons.append(['/exit'])
            contacts = ReplyKeyboardMarkup(buttons, one_time_keyboard=True)
            await update.message.reply_text(
                "Выберите пользователя, которому хотите отправить сообщение:", reply_markup=contacts)
            return 1
        else:
            await update.message.reply_text('У вас нет друзей!')
            return ConversationHandler.END
    else:
        await update.message.reply_text(
            "Для начала войдите в аккаунт!")
        return ConversationHandler.END


async def anonym_idir(update, context):
    global idk
    first_name, last_name = update.message.text.split()
    res = cur.execute(f'SELECT chat_id FROM accounts '
                      f'WHERE first_name=? AND last_name=?', (first_name, last_name)).fetchall()
    if len(res) == 0:
        await update.message.reply_text('Такого пользователя нет! Попробуйте еще раз')
        return 1
    else:
        idk = res[0][0]
        await update.message.reply_text('Введите ваше сообщение:',
                                        reply_markup=ReplyKeyboardMarkup([['/cancel'], ['/exit']],
                                                                         one_time_keyboard=False))
        return 2


async def anonym_is_sent(update, context):
    global idk
    text = f'Вам сообщение от анонимуса:\n"{update.message.text}"'
    params = {
        'chat_id': idk,
        'text': text
    }
    response = requests.get(f'https://api.telegram.org/bot{TOKEN}/sendMessage', params=params)
    await update.message.reply_text("Все отправлено!", reply_markup=mrkup)


async def show_friends(update, context):  # Показать список друзей
    global body
    if not (body):  # Если вход не выполнен
        await update.message.reply_text('Для начала войдите в аккаунт!')
        return 0
    res = cur.execute(f"SELECT first_name, last_name FROM {body[0]}_{body[1]}").fetchall()
    if len(res) > 0:
        text = '\n'.join(list(' '.join(res)))
        await update.message.reply_text(f'Ваш список друзей:\n{text}')
    else:
        await update.message.reply_text('У вас нет друзей!')


async def exitor(update, context):  # Выполнить выход
    global body
    body = 0  # Выход выполнен
    await update.message.reply_text('Выход выполнен. До свидания!',
                                    reply_markup=ReplyKeyboardMarkup([['/start'], ['/help']], one_time_keyboard=False))
    return ConversationHandler.END  # Если был активен диалог, он завершается


def main():
    application = Application.builder().token(TOKEN).build()
    # Строим тг-бота
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            1: [CommandHandler('signup', signupper)],
            2: [CommandHandler('login', loginner)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    # Начальный диалог для регистрации/входа в аккаунт
    log = ConversationHandler(
        entry_points=[CommandHandler('login', loginner)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, login)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    # Диалог для входа в аккаунт
    sig = ConversationHandler(entry_points=[CommandHandler('signup', signupper)],
                              states={
                                  1: [MessageHandler(filters.TEXT & ~filters.COMMAND, sig_1)],
                                  2: [MessageHandler(filters.TEXT & ~filters.COMMAND, sig_2)],
                                  3: [MessageHandler(filters.TEXT & ~filters.COMMAND, sig_3)]
                              },
                              fallbacks=[CommandHandler('cancel', cancel)])
    # Диалог для регистрации аккаунта
    friends = ConversationHandler(
        entry_points=[CommandHandler('send_friend', friender)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, friend_1)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    # Диалог для отправки запроса в друзья
    sender = ConversationHandler(
        entry_points=[CommandHandler('send', send)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, idir)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, is_sent)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    # Диалог для отправления сообщения контакту
    anonym_sender = ConversationHandler(
        entry_points=[CommandHandler('anonym_send', anonym_send)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, anonym_idir)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, anonym_is_sent)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    # Анонимный диалог
    # Добавляем диалоги
    application.add_handler(conv_handler)
    application.add_handler(log)
    application.add_handler(sig)
    application.add_handler(sender)
    application.add_handler(friends)
    application.add_handler(anonym_sender)
    # Добавляем стартовые точки/точки стопа
    application.add_handler(CommandHandler('login', loginner))
    application.add_handler(CommandHandler('signup', signupper))
    application.add_handler(CommandHandler('exit', exitor))
    application.add_handler(CommandHandler('friends', show_friends))
    application.add_handler(CommandHandler('help', helper))
    application.run_polling()


if __name__ == '__main__':
    main()

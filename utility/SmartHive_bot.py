import logging
import sqlite3

import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

from config import BOTKEY
from utility.util import verify_pass

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

USERNAME, PASSWORD, CHECK = range(3)

updater = None


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text("Hi and welcome to SmartHive bot!")
    update.message.reply_text("Please tell me the username that you used to register in our website.")
    return USERNAME


def help_command(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


user_data = {}


def username(update, context):
    print("username")
    conn = sqlite3.connect("sqlite:////../database/db.sqlite3")
    cur = conn.cursor()
    text = update.message.text
    user_data['username'] = text
    username_check = cur.execute('''SELECT id FROM User WHERE username = (?)''', (user_data['username'],)).fetchall()
    if len(username_check) > 0:
        update.message.reply_text(
            'Are you {}? '.format(text.lower()))
        conn.commit()
        conn.close()
        update.message.reply_text('Please write your password now...')
        return PASSWORD
    update.message.reply_text("I'm sorry! Wrong username, please try again.")
    conn.commit()
    conn.close()
    return start(update, context)


def password(update, context):
    print("password")
    conn = sqlite3.connect("sqlite:////../database/db.sqlite3")
    cur = conn.cursor()

    text = update.message.text
    user_data['password'] = text
    user_password = \
        cur.execute('''SELECT password FROM User WHERE username = (?)''', ((user_data['username']),)).fetchone()[0]
    if verify_pass(user_data['password'], user_password):
        conn.commit()
        conn.close()
        return check(update, user_data)
    update.message.reply_text("I'm sorry! Wrong password, please try again.")
    conn.commit()
    conn.close()
    return start(update, context)


def check(update, user_data):
    print("check")
    conn = sqlite3.connect("sqlite:////../database/db.sqlite3")
    cur = conn.cursor()
    idTelegram_stored = \
        cur.execute('''SELECT idTelegram FROM User WHERE username = (?)''', ((user_data['username']),)).fetchone()[0]
    if idTelegram_stored == update.message.from_user.id:
        update.message.reply_text("Welcome again. Now you can receive the notifications fromey our hives!")
    else:
        cur.execute('''UPDATE User SET idTelegram = (?) WHERE username=(?)''',
                    ((update.message.from_user.id), (user_data['username']),))
        update.message.reply_text("Welcome! Now you can receive the notifications from your hives!")

    user_data = {}
    conn.commit()
    conn.close()

    return ConversationHandler.END


def cancel(update, user_data):
    print("cancel")
    user_data.clear()
    return ConversationHandler.END


def echo(update, context):
    """Echo the user message."""

    chatid = update.effective_chat.id
    receivedmessage = update.message.text
    sendmessage = ' I received: ' + receivedmessage
    update.bot.send_message(chat_id=chatid, text=sendmessage)
    print(chatid)
    # sample2: update.message.reply_text(update.message.text)


def sendMessage(msg, chatID):
    url = 'https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}'.format(BOTKEY, chatID, msg)
    requests.get(url)


def botStart():
    global updater
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True
    updater = Updater(BOTKEY, use_context=True)

    # Get the dispatcher to register handlers  (callbacks)
    dp = updater.dispatcher

    # add an handler for each command
    # start and help are usually defined
    # dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start, pass_user_data=True)],

        states={
            USERNAME: [MessageHandler(Filters.text, username, pass_user_data=True), ],
            PASSWORD: [MessageHandler(Filters.text, password, pass_user_data=True), ],
            CHECK: [MessageHandler(Filters.text, check, pass_user_data=True), ],
        },

        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(conv_handler)

    # add an handler for messages
    # dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the Bot (polling of messages)
    # this call is non-blocking
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    botStart()

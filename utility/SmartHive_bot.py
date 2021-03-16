import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import Chat, bot
from config import BOTKEY, chatID
from threading import Timer,Thread,Event

from random import uniform


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)



# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    bot1: bot.Bot = context.bot
    bot1.send_message(chat_id=update.effective_chat.id,
                     text="You have just entered start command")


def help_command(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def startBot():
    global updater
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True
    updater = Updater(BOTKEY, use_context=True)

    # Get the dispatcher to register handlers  (callbacks)
    dp = updater.dispatcher

    # add an handler for each command
    # start and help are usually defined
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))

    # Start the Bot (polling of messages)
    # this call is non-blocking
    updater.start_polling()

    return updater




# call a function each t seconds
class perpetualTimer():

    def __init__(self, t, hFunction, param):
        self.t = t
        self.hFunction = hFunction
        self.param = param
        self.thread = Timer(self.t, self.handle_function)

    def handle_function(self):
        self.hFunction(self.param)
        self.thread = Timer(self.t, self.handle_function)
        self.thread.start()

    def start(self):
        self.thread.start()

    def cancel(self):
        self.thread.cancel()


def sendBotRandomVal():
    val = int(uniform(0, 255))
    updater.bot.send_message(chat_id=chatID, text='New value detected: ' + str(val))

def swarmDetection_bot(hive,hives):
    msg = "The hive with id "+ str(hive.hive_id) +" is swarming!"
    telegram_bot_sendtext(updater,msg)

def telegram_bot_sendtext(updater,msg):

    updater.bot.send_message(chat_id=chatID, text=msg)



if __name__ == '__main__':
    # start bot
    updater = startBot()
    # start thread
    # randomizer = perpetualTimer(10,sendBotRandomVal,updater)
    # randomizer.start()

    # idle (blocking)
    updater.idle()

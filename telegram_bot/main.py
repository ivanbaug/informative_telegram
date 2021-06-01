import logging
from datetime import time
from pytz import timezone
from telegram import Update
from telegram.ext import Updater, CommandHandler,  CallbackContext
from my_keys import  *
from my_apis import  *

tz = timezone("America/Lima")
t_morning = time(6,1,tzinfo=tz)
t_noon = time(13,1,tzinfo=tz)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

def start(update: Update, _: CallbackContext) -> None:
    """Sends explanation on how to use the bot."""
    update.message.reply_text('Hi! Use /set <seconds> to set a timer')


def alarm(context: CallbackContext) -> None:
    """Send the alarm message."""
    job = context.job
    my_text = get_weather()
    context.bot.send_message(job.context, text=my_text)


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def set_daily_weather(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds
        # due = int(context.args[0])
        # if due < 0:
        #     update.message.reply_text('Sorry we can not go back to future!')
        #     return
        job_morning = str(chat_id)+"morning"
        job_noon = str(chat_id)+"noon"
        job_removed = remove_job_if_exists(job_morning, context)
        job_removed = remove_job_if_exists(job_noon, context)
        context.job_queue.run_daily(alarm, time= t_morning , context=chat_id, name=job_morning)
        context.job_queue.run_daily(alarm, time= t_noon , context=chat_id, name=job_noon)

        text = 'Timer successfully set!'
        if job_removed:
            text += ' Old one was removed.'
        update.message.reply_text(text)

    except (IndexError, ValueError):
        update.message.reply_text('Usage: /set <seconds>')


def unset(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id

    job_morning = str(chat_id)+"morning"
    job_noon = str(chat_id)+"noon"
    job_removed = remove_job_if_exists(job_morning, context)
    job_removed = remove_job_if_exists(job_noon, context)
    text = 'Timer successfully cancelled!' if job_removed else 'You have no active timer.'
    update.message.reply_text(text)

# dispatcher.add_handler(start_price_watch)
# dispatcher.add_handler(start_weather_watch)

# updater.start_polling()
# updater.idle()
def main():
  """Run bot"""
  # Create the Updater and pass it your bot's token.
  updater = Updater(TELEGRAM_TOKEN)

  # Get the dispatcher to register handlers
  dispatcher = updater.dispatcher

  # on different commands - answer in Telegram
  dispatcher.add_handler(CommandHandler("start", start))
  dispatcher.add_handler(CommandHandler("help", start))
  dispatcher.add_handler(CommandHandler("set", set_daily_weather))
  dispatcher.add_handler(CommandHandler("unset", unset))

  # Start the Bot
  updater.start_polling()

  # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
  # SIGABRT. This should be used most of the time, since start_polling() is
  # non-blocking and will stop the bot gracefully.
  updater.idle()

if __name__ == '__main__':
  main()
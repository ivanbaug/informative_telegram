import logging
from datetime import time
from pytz import timezone
from telegram import Update
from telegram.ext import Updater, CommandHandler,  CallbackContext, Filters, MessageHandler
from my_keys import *
from my_apis import *


tz = timezone("America/Lima")
t_morning = time(6, 1, tzinfo=tz)
t_noon = time(13, 1, tzinfo=tz)
t_night = time(18, 30, tzinfo=tz)


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def options(update: Update, _: CallbackContext) -> None:
    """Sends explanation on how to use the bot."""
    long_msg = "Use /setw to receive updates on the weather in the morning and at noon\n" \
        "Use /unsetw to cancel the weather updates\n" \
        "Use /setblog to watch if there are new posts in the evening\n" \
        "Use /unsetblog to cancel the blog watch\n" \
        "bye :)"
    update.message.reply_text(long_msg)


def blog_update(context: CallbackContext) -> None:
    """Check if there is an update on the feed and notifies it."""
    job = context.job
    new_posts, my_text = get_rss_feed()
    if new_posts:
        context.bot.send_message(job.context, text=my_text)


def weather_update(context: CallbackContext) -> None:
    """Send the weather update message."""
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


def set_blog_watch_job(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    try:
        job_blog = str(chat_id)+"blog"
        job_removed = remove_job_if_exists(job_blog, context)
        context.job_queue.run_daily(
            blog_update, time=t_night, context=chat_id, name=job_blog)
        text = 'Blog watch successfully set!'
        if job_removed:
            text += ' Old one was removed.'
        update.message.reply_text(text)

    except (IndexError, ValueError):
        # TODO: Better error handling sequence
        update.message.reply_text('Usage: /set <seconds>')


def set_daily_weather_job(update: Update, context: CallbackContext) -> None:
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
        context.job_queue.run_daily(
            weather_update, time=t_morning, context=chat_id, name=job_morning)
        context.job_queue.run_daily(
            weather_update, time=t_noon, context=chat_id, name=job_noon)

        text = 'Weather updates successfully set!'
        if job_removed:
            text += ' Old one was removed.'
        update.message.reply_text(text)

    except (IndexError, ValueError):
        update.message.reply_text('Usage: /set <seconds>')


def unset_weather_job(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id

    job_morning = str(chat_id)+"morning"
    job_noon = str(chat_id)+"noon"
    job_removed = remove_job_if_exists(job_morning, context)
    job_removed = remove_job_if_exists(job_noon, context)
    text = 'Weather updates successfully cancelled!' if job_removed else 'You have no active timer.'
    update.message.reply_text(text)


def unset_blog_watch_job(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_blog = str(chat_id)+"blog"
    job_removed = remove_job_if_exists(job_blog, context)
    text = 'Blog watch successfully cancelled!' if job_removed else 'You have no active timer.'
    update.message.reply_text(text)


def simple_reply(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    # msg = update.message.text
    update.message.reply_text("Hi! To view the options type /options ")


def main():
    """Run bot"""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TELEGRAM_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("options", options))
    dispatcher.add_handler(CommandHandler("setw", set_daily_weather_job))
    dispatcher.add_handler(CommandHandler("unsetw", unset_weather_job))
    dispatcher.add_handler(CommandHandler("setblog", set_blog_watch_job))
    dispatcher.add_handler(CommandHandler("unsetblog", unset_blog_watch_job))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command, simple_reply))

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()

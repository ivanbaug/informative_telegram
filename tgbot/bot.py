import datetime
import logging
from datetime import time
import db.db_funcs as dbf


from pytz import timezone
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Application, ContextTypes, filters

from tgbot.my_apis import get_rss_feed, get_weather
from tgbot.models import TChat, TService
from settings.config import TELEGRAM_TOKEN, db_file, ServiceType,IsActive

tz = timezone("America/Lima")
TIME_MORNING = time(21, 59, tzinfo=tz)
# TIME_MORNING = time(6, 1, tzinfo=tz)
TIME_NOON = time(13, 1, tzinfo=tz)
# TIME_NIGHT = time(18, 30, tzinfo=tz)
TIME_NIGHT = time(22, 4, tzinfo=tz)

MORNING = "MORNING"
NOON = "NOON"
NIGHT = "NIGHT"

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)





# region Weather
async def get_my_weather(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Checks for weather update and returns it immediately"""
    my_text = get_weather()
    await update.message.reply_text(my_text)


async def weather_update(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the weather update message."""
    job = context.job
    my_text = get_weather()
    await context.bot.send_message(job.chat_id, text=my_text)


async def set_daily_weather_job(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a job to the queue."""
    chat_id = update.effective_message.chat_id
    try:
        job_removed = set_weather_job(context, chat_id)

        text = 'Weather updates successfully set!'
        if job_removed:
            text += ' Old one was removed.'

        # Persist
        dbf.add_or_upd_service(db_file, str(chat_id), ServiceType.WEATHER.value, IsActive.YES)

        await update.effective_message.reply_text(text)

    except (IndexError, ValueError):
        await update.effective_message.reply_text('Failed to set a weather update job')


def set_weather_job(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> bool:
    job_morning = get_job_name(chat_id, MORNING)
    job_noon = get_job_name(chat_id, NOON)
    job_removed = remove_job_if_exists(job_morning, context)
    job_removed = remove_job_if_exists(job_noon, context)
    context.job_queue.run_daily(weather_update, time=TIME_MORNING, chat_id=chat_id, name=job_morning)
    context.job_queue.run_daily(weather_update, time=TIME_NOON, chat_id=chat_id, name=job_noon)

    return job_removed


async def unset_weather_job(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id

    job_morning = get_job_name(chat_id, MORNING)
    job_noon = get_job_name(chat_id, NOON)
    job_removed = remove_job_if_exists(job_morning, context)
    job_removed = remove_job_if_exists(job_noon, context)
    text = 'Weather updates successfully cancelled!' if job_removed else 'You have no active timer.'

    # Persist
    dbf.add_or_upd_service(db_file, str(chat_id), ServiceType.WEATHER.value, IsActive.NO)

    await update.message.reply_text(text)


# endregion

# region Blog
async def get_blog(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Checks for blog update and returns it immediately"""
    new_posts, my_text = get_rss_feed(update.effective_message.chat_id)
    if new_posts:
        await update.message.reply_text(my_text)
    return


async def blog_update(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check if there is an update on the feed and notifies it."""
    job = context.job
    new_posts, my_text = get_rss_feed(job.chat_id)
    if new_posts:
        await context.bot.send_message(job.chat_id, text=my_text)
    return


async def set_blog_watch_job(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a job to the queue."""
    chat_id = update.effective_message.chat_id
    try:
        job_blog = get_job_name(chat_id, ServiceType.BLOG.name)
        job_removed = remove_job_if_exists(job_blog, context)
        context.job_queue.run_daily(blog_update, time=TIME_NIGHT, chat_id=chat_id, name=job_blog)
        # context.job_queue.run_once(blog_update, when=delta, context=chat_id, name=job_blog)
        text = 'Blog watch successfully set!'
        if job_removed:
            text += ' Old one was removed.'

        # Persist, first persist with a fixed date
        dbf.add_or_upd_service(db_file, str(chat_id), ServiceType.BLOG.value, IsActive.YES,
                               last_updated=datetime.datetime(2000, 1, 1, 0, 0, 0))

        await update.message.reply_text(text)

    except (IndexError, ValueError):
        await update.message.reply_text('Failed to set a blog watch job')


async def unset_blog_watch_job(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_blog = get_job_name(chat_id, ServiceType.BLOG.name)
    job_removed = remove_job_if_exists(job_blog, context)
    text = 'Blog watch successfully cancelled!' if job_removed else 'You have no active timer.'

    # Persist
    dbf.add_or_upd_service(db_file, str(chat_id), ServiceType.BLOG.value, IsActive.NO)

    await update.message.reply_text(text)
# endregion


async def options(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends explanation on how to use the bot."""
    long_msg = "Use /setw to receive updates on the weather in the morning and at noon\n" \
               "Use /unsetw to cancel the weather updates\n" \
               "Use /setblog to watch if there are new posts in the evening\n" \
               "Use /unsetblog to cancel the blog watch\n" \
               "Use /getblog to check for blog updates\n" \
               "Use /getw to get weather update\n" \
               "Use /forgetme deactivate current chat and its services\n" \
               "Have fun :)"
    await update.message.reply_text(long_msg)

async def deactivate_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Marks chat and its services as inactive."""
    chat_id = update.message.chat_id

    # Persist
    rows = dbf.get_active_services_from_chat(db_file, str(chat_id))
    tservices = [TService(row) for row in rows]

    for service in tservices:
        if service.id_type == ServiceType.WEATHER.value:
            await unset_weather_job(update, context)
        if service.id_type == ServiceType.BLOG.value:
            await unset_blog_watch_job(update, context)

        dbf.add_or_upd_service(db_file, str(chat_id), service.id_type, IsActive.NO,
                               optional_url=service.optional_url, last_updated=service.last_updated)

    dbf.add_or_upd_chat(db_file, str(chat_id), IsActive.NO)

    await update.message.reply_text("Your you have successfully deactivated the chat and it's associated services.")


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def simple_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Basic reply"""
    # Save chat id and set it to active
    chat_id = update.effective_message.chat_id
    dbf.add_or_upd_chat(db_file, str(chat_id), IsActive.YES)

    await update.message.reply_text("Hi! To view the options type /options ")


def get_job_name(chat_id: int, job_type: str) -> str:
    return str(chat_id) + job_type


def load_saved_jobs(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Read info from db and load saved jobs for the chat"""

    tchat = []
    rows = dbf.get_active_chat_list(db_file)
    for row in rows:
        tchat.append(TChat(row))

    tservices = []
    for chat in tchat:
        rows = dbf.get_active_services_from_chat(db_file, chat.id)
        for row in rows:
            tservices.append(TService(row))

    for service in tservices:
        chat_id = service.id_chat
        stype = ServiceType(service.id_type).value
        if stype == ServiceType.BLOG.value:
            try:
                job_blog = get_job_name(chat_id, ServiceType.BLOG.name)
                job_removed = remove_job_if_exists(job_blog, context)
                context.job_queue.run_daily(blog_update, time=TIME_NIGHT, chat_id=chat_id, name=job_blog)
            except (IndexError, ValueError):
                logger.error("Failed to set a blog watch job")
        elif stype == ServiceType.WEATHER.value:
            try:
                job_removed = set_weather_job(context, chat_id)
            except (IndexError, ValueError):
                logger.error("Failed to set a weather job")
        elif stype == ServiceType.DEX.value:
            pass


def main():
    """Start the bot."""

    # Create the Application, use your bot's token.
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("options", options))
    application.add_handler(CommandHandler("setw", set_daily_weather_job))
    application.add_handler(CommandHandler("unsetw", unset_weather_job))
    application.add_handler(CommandHandler("setblog", set_blog_watch_job))
    application.add_handler(CommandHandler("unsetblog", unset_blog_watch_job))
    application.add_handler(CommandHandler("getw", get_my_weather))
    application.add_handler(CommandHandler("getblog", get_blog))
    application.add_handler(CommandHandler("forgetme", deactivate_chat))

    # On non command i.e. message - return list of command options
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, simple_reply))

    # Load saved jobs
    load_saved_jobs(CallbackContext(application))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

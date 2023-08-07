import httpx
import feedparser
from datetime import datetime, timedelta
from settings.config import WEATHER_KEY, FEED_URL, ServiceType, db_file, IsActive
from tgbot.models import TService
import db.db_funcs as dbf


def get_weather():
    owm_endpoint = "https://api.openweathermap.org/data/2.5/onecall"
    weather_params = {
        "lat": 4.62,
        "lon": -74.06,
        "appid": WEATHER_KEY,
        "exclude": "current,minutely,daily",
        "units": "metric",
    }
    response = httpx.get(owm_endpoint, params=weather_params)
    response.raise_for_status()
    # get the next 8 hours of forecast to notify myself if it will rain
    response_json = response.json()
    tz_offset = int(response_json['timezone_offset'])
    forecasts = response_json['hourly'][:8]

    forecast_str = ""
    for f in forecasts:
        unixtime = int(f['dt']) + tz_offset  # timezone offset
        # dt = datetime.utcfromtimestamp(unixtime).strftime('%Y-%m-%d %H:%M:%S')
        time = datetime.utcfromtimestamp(unixtime).strftime('%I%p')
        forecast = f['weather'][0]
        forecast_id = int(forecast['id'])
        main_fc = forecast['main']
        description_fc = forecast['description']
        comment = ""
        if forecast_id < 700:
            comment = " ☔"
        forecast_str += f"{time} | {description_fc}{comment}\n"
    return forecast_str


def entryd_to_date(date_str: str) -> datetime:
    # Works only with the format of this feed
    # Clean date string
    date_str = date_str[5:-6]
    # Convert to datetime obj
    return datetime.strptime(date_str, '%d %b %Y %H:%M:%S')


def get_rss_feed(chat_id: int) -> tuple[bool, str]:
    news_feed = feedparser.parse(FEED_URL)

    # Get the latest date of an entry recorded by this script
    row = dbf.get_service_by_chatid(db_file, str(chat_id), ServiceType.BLOG.value)
    if not row:
        raise ValueError(f"Blog service not found in database.")

    tservice = TService(row)

    # Take the top 10 entries and check whether they are new
    new_entry_count = 0
    msg_text = ""
    last_date = tservice.last_updated
    new_date = last_date

    for e in news_feed.entries[:10]:
        entry_date = entryd_to_date(e['published'])
        if entry_date > last_date:
            new_entry_count += 1
            line = f"{entry_date} # {e['title']}\n"
            msg_text += line
            # Record the most recent date to log it in a file at the end of
            # the process
            if entry_date > new_date:
                new_date = entry_date

    if new_entry_count:
        msg = f'There are {new_entry_count} new entries!\n{msg_text}'
    else:
        msg = 'There are no new entries.'

    if new_entry_count:
        dbf.add_or_upd_service(db_file, str(tservice.id_chat), tservice.id_type, IsActive.YES, last_updated=new_date)

    return new_entry_count > 0, msg


# Dex
def get_mangadex(manga_id: str, last_updated: datetime, chat_id: int):
    # Api documentation: https://api.mangadex.org/docs/

    base_url = "https://api.mangadex.org"
    options = "?limit=5&includeFuturePublishAt=0&order[publishAt]=desc"
    languages = ["en", "es", "es-la"]
    str_languages = "&translatedLanguage[]=" + "&translatedLanguage[]=".join(languages)
    publish_since = "&publishAtSince=" + last_updated.strftime("%Y-%m-%dT%H:%M:%S")
    options += str_languages + publish_since
    r = httpx.get(f"{base_url}/manga/{manga_id}/feed{options}")
    r.raise_for_status()

    rdata = r.json()
    if rdata["result"].lower() != "ok":
        msg = f"{manga_id} error: \n"
        msg += get_dex_error_msg(rdata)
        return msg

    if rdata["total"] == 0:
        return ""

    new_date: datetime = last_updated

    result_str = f"New chapters for {manga_id}:\n"
    for chapter in rdata["data"]:
        publish_at = datetime.strptime(chapter["attributes"]["publishAt"][0:19], "%Y-%m-%dT%H:%M:%S")
        if publish_at > new_date:
            new_date = publish_at
        result_str += f"Ch:{chapter['attributes']['chapter']} - Title:{chapter['attributes']['title']}\n"
        result_str += (f"Language:{chapter['attributes']['translatedLanguage']} "
                       f"Date:{chapter['attributes']['publishAt'][0:19]}\n")
        result_str += f"Link: https://mangadex.org/chapter/{chapter['id']}\n\n"

    # Update service
    lu = new_date + timedelta(seconds=1)  # Add 1 second to avoid repeating the last chapter in query
    dbf.add_or_upd_service(db_file, str(chat_id), ServiceType.DEX.value,
                           IsActive.YES, last_updated=lu, optional_url=manga_id)

    return result_str


async def check_manga_exists(manga_id: str):
    base_url = "https://api.mangadex.org"
    r = httpx.get(f"{base_url}/manga/{manga_id}")
    rdata = r.json()
    if 'result' not in rdata:
        return False, "Unexpected response from server"

    if rdata["result"].lower() != "ok":
        return False, get_dex_error_msg(rdata)

    title = list(rdata["data"]["attributes"]["title"].values())[0]
    return True, f"Manga {title} found!"


def get_dex_error_msg(rdata: dict):
    msg = "Request not ok \n"
    if rdata["result"].lower() == "error":
        msg += f"Error code: {rdata['errors'][0]['status']}\n"
        msg += f"Error message: {rdata['errors'][0]['detail']}\n"
        return msg

    return msg + f"Result: {rdata['result']}\n"

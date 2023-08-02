import httpx
import feedparser
from datetime import datetime
from settings.config import WEATHER_KEY, FEED_URL, ServiceType, db_file, IsActive
from tgbot.models import TChat, TService
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
        id = int(forecast['id'])
        main_fc = forecast['main']
        description_fc = forecast['description']
        comment = ""
        if id < 700:
            comment = " ☔"
        forecast_str += f"{time} | {description_fc}{comment}\n"
    return forecast_str


def entryd_to_date(date_str: str) -> datetime:
    # Works only with the format of this feed
    # Clean date string
    date_str = date_str[5:-6]
    # Convert to datetime obj
    return datetime.strptime(date_str, '%d %b %Y %H:%M:%S')


def get_rss_feed(chat_id:int) -> tuple[bool, str]:
    NewsFeed = feedparser.parse(FEED_URL)

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

    for e in NewsFeed.entries[:10]:
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

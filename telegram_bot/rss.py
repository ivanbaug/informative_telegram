import feedparser
from datetime import datetime as dt
from my_keys import FEED_URL

NewsFeed = feedparser.parse(FEED_URL)
entry = NewsFeed.entries[1]

# print(entry.keys())


def format_date(date_str):
    # works only with the format of this feed
    # Clean date string
    date_str = date_str[5:-6]
    # Convert to datetime obj
    return dt.strptime(date_str, '%d %b %Y %H:%M:%S')


for e in NewsFeed.entries:
    date = format_date(e['published'])
    print(f"{date} # {e['title']}")

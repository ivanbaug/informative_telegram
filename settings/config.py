import os
from enum import Enum,IntEnum

from dotenv import load_dotenv

load_dotenv()  # get environment variables from .env

PRODUCTION = os.getenv('PRODUCTION') == 'True'
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
WEATHER_KEY = os.getenv('WEATHER_KEY')
FEED_URL = os.getenv('FEED_URL')



if PRODUCTION:
    VOLUME_PATH = os.getenv('VOLUME_PATH')
else:
    VOLUME_PATH = ''

logging_file = VOLUME_PATH + 'app.log'
db_file = VOLUME_PATH + 'db.sqlite3'

# Nice guide to logging config with dictionary
# https://coderzcolumn.com/tutorials/python/logging-config-simple-guide-to-configure-loggers-from-dictionary-and-config-files-in-python
logging_level = 'INFO'
log_config = {
    "version": 1,
    "root": {
        "handlers": ["console", "file"],
        "level": logging_level
    },
    "handlers": {
        "console": {
            "formatter": "simplefmt",
            "class": "logging.StreamHandler",
            "level": logging_level
        },
        "file": {
            "formatter": "simplefmt",
            "class": "logging.FileHandler",
            "level": logging_level,
            "filename": logging_file
        }
    },
    "formatters": {
        "simplefmt": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s",
        }
    },
}

class ServiceType(Enum):
    WEATHER = 1
    BLOG = 2
    DEX = 3

    def __int__(self):
        return self.value

    def __str__(self):
        return self.name


class IsActive(IntEnum):
    YES = 1
    NO = 0

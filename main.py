import logging
from tgbot.bot import main
from logging import config as logging_config
from settings.config import log_config, PRODUCTION, db_file
from db.db_funcs import initialize_db, add_or_upd_chat

logging_config.dictConfig(log_config)
logger = logging.getLogger()

if __name__ == '__main__':
    if not PRODUCTION:
        logger.info('Running in development mode.')

    initialize_db(db_file)

    main()

import datetime
import sqlite3
from contextlib import contextmanager
from settings.config import log_config, ServiceType, IsActive
import logging
from logging import config as logging_config

logging_config.dictConfig(log_config)
logger = logging.getLogger()


@contextmanager
def db_ops(db_filepath):
    try:
        conn = sqlite3.connect(db_filepath, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception as _:
        logger.error('Exception while performing db operation', exc_info=True)
        raise
    finally:
        cursor.close()
        conn.close()


def initialize_db(db_filepath) -> None:
    """
    Creates a connection to the database and creates the tables if they don't exist.
    """

    with db_ops(db_filepath) as cursor:
        cursor.execute('CREATE TABLE IF NOT EXISTS chat (id TEXT PRIMARY KEY, active INTEGER DEFAULT 0, '
                       'last_updated timestamp)')
        cursor.execute('CREATE TABLE IF NOT EXISTS service_type (id INTEGER PRIMARY KEY, name TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS service (id INTEGER PRIMARY KEY,id_chat TEXT, id_type INTEGER, ' 
                       'active INTEGER DEFAULT 0,last_updated timestamp, optional_url TEXT, '
                       'FOREIGN KEY (id_chat) REFERENCES chat (id), FOREIGN KEY (id_type) REFERENCES service_type(id), ' 
                       'UNIQUE(id_chat, id_type, optional_url) ON CONFLICT IGNORE)')
    for member in ServiceType:
        add_or_upd_service_type(db_filepath, member.value, member.name)


def add_or_upd_chat(db_filepath: str, id_chat: str, active: int) -> int:
    """
    Create a new chat
    :param db_filepath:
    :param id_chat:
    :param active:
    :return: chat id
    """
    sql = '''INSERT OR IGNORE INTO chat(id,active,last_updated) VALUES(?,?,CURRENT_TIMESTAMP)'''
    with db_ops(db_filepath) as cursor:
        cursor.execute(sql, (id_chat, active))
        if cursor.lastrowid == 0:
            cursor.execute("UPDATE chat SET active=?, last_updated=CURRENT_TIMESTAMP WHERE id=?", (active, id_chat))
        lastrowid = cursor.lastrowid
    return lastrowid


def add_or_upd_service_type(db_filepath: str, id_servicetype: int, name: str) -> int:
    """
    Create a new service_type
    :param db_filepath:
    :param id_servicetype:
    :param name:
    :return: service_type id
    """
    sql = '''INSERT OR IGNORE INTO service_type(id,name) VALUES(?,?)'''
    with db_ops(db_filepath) as cursor:
        cursor.execute(sql, (id_servicetype, name))
        if cursor.lastrowid == 0:
            cursor.execute("UPDATE service_type SET name=? WHERE id=?", (name, id_servicetype))
        lastrowid = cursor.lastrowid
    return lastrowid


def add_or_upd_service(db_filepath: str, id_chat: str, id_type: int, active: int, optional_url='',
                       last_updated: datetime.datetime = datetime.datetime.now()) -> int:
    """
    Create a new service
    :param db_filepath:
    :param id_chat:
    :param id_type:
    :param active:
    :param optional_url:
    :param last_updated:
    :return: service id
    """
    sql = '''INSERT OR IGNORE INTO service(id_chat,id_type,active,last_updated,optional_url) 
    VALUES(?,?,?,?,?)'''
    with db_ops(db_filepath) as cursor:
        cursor.execute(sql, (id_chat, id_type, active, last_updated, optional_url))
        if cursor.lastrowid == 0:
            cursor.execute("SELECT * FROM service WHERE id_chat=? AND id_type=? AND optional_url=?",
                           (id_chat, id_type, optional_url))
            first_row = cursor.fetchall()[0]
            upd_id = first_row[0] # this is a tuple and the id is the first element
            cursor.execute("UPDATE service SET id_chat=?, id_type=?, active=?, last_updated=?, "
                           "optional_url=? WHERE id=?", (id_chat, id_type, active, last_updated, optional_url, upd_id))
        lastrowid = cursor.lastrowid
    return lastrowid


def get_active_chat_list(db_filepath: str) -> list:
    """
    Query all rows in the chat table that are labeled as active
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute("SELECT * FROM chat WHERE active=1")
        rows = cursor.fetchall()
    return rows


def get_active_services_from_chat(db_filepath: str, id_chat:str) -> list:
    """
    Query all rows in the service table that are labeled as active for a specific chat
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute("SELECT * FROM service WHERE active=1 AND id_chat=?", (id_chat,))
        rows = cursor.fetchall()
    return rows


def get_service_by_chatid(db_filepath: str, id_chat: str, id_type: int) -> tuple:
    """
    Query all rows in the service table that are labeled as active for a specific chat
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute("SELECT * FROM service WHERE active=1 AND id_chat=? AND id_type=?", (id_chat, id_type))
        rows = cursor.fetchall()
    if len(rows) > 0:
        return rows[0]
    return None

def get_pages(db_filepath: str) -> list:
    """
    Query all rows in the pages table
    :return: list of pages
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute("SELECT * FROM sigma_pages")
        rows = cursor.fetchall()
    return rows


def get_products(db_filepath: str) -> list:
    """
    Query all rows in the products table
    :return: list of products
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute("SELECT * FROM sigma_products")
        rows = cursor.fetchall()
    return rows


def get_pages_last_updated(db_filepath: str) -> datetime.datetime | None:
    """
    Query all rows in the pages table
    :return: NAIVE datetime of last updated page
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute("SELECT last_updated FROM sigma_pages ORDER BY last_updated DESC LIMIT 1")
        rows = cursor.fetchall()
    if rows:
        return rows[0][0]
    return None


def get_products_last_updated(db_filepath: str) -> datetime.datetime | None:
    """
    Query all rows in the products table
    :return: datetime of last updated product
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute("SELECT last_updated FROM sigma_products ORDER BY last_updated DESC LIMIT 1")
        rows = cursor.fetchall()
    if rows:
        return rows[0][0]
    return None


def delete_product(db_filepath: str, url: str) -> None:
    """
    Delete a product by url
    :param db_filepath:
    :param url:
    :return:
    """
    with db_ops(db_filepath) as cursor:
        cursor.execute("DELETE FROM sigma_products WHERE url=?", (url,))

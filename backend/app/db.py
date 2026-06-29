from contextlib import contextmanager

import psycopg
from pymongo import MongoClient

from app.config import settings

mongo_client = MongoClient(settings.mongo_uri)
mongo_db = mongo_client[settings.mongo_db]


@contextmanager
def postgres_conn():
    with psycopg.connect(settings.postgres_dsn) as conn:
        yield conn

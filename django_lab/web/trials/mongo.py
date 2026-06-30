from django.conf import settings
from pymongo import MongoClient


client = MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB]


def studies_collection():
    return db.studies

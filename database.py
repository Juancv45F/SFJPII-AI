from pymongo import MongoClient
from config import settings


client = MongoClient(settings.mongodb_uri)

db = client[settings.mongodb_database]


def verificar_conexion():
    client.admin.command("ping")
    return True
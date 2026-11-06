from pymongo import MongoClient
from config import settings


# Cliente a nivel de módulo: las invocaciones de una misma instancia comparten
# el pool. Conecta de forma diferida, así que importar no toca la red.
client = MongoClient(
    settings.mongodb_uri,
    appname="sfjpii-ai",
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=20000,
    maxPoolSize=10,
    maxIdleTimeMS=60000
)

db = client[settings.mongodb_database]


def verificar_conexion():
    client.admin.command("ping")
    return True
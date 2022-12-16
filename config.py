import os

PROXY = os.environ.get("HTTP_PROXY", None)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DATABASE = "./db/dk.db"
POOL_JSON = "./db/pool.json"

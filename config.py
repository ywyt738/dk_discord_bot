import os

PROXY = os.environ.get("HTTP_PROXY", None)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
# INIT_POOL = "与共同迎" * 375 + "K年" * 100
# POOL = "与共同迎" * 375 + "K年" * 100 + "D虎" * 20
DATABASE = "./db/dk.db"
POOL_JSON = "./db/pool.json"
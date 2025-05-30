# config.py
import os

GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_CHANNEL = os.getenv("DISCORD_CHANNEL", "")
PROJECT_ID = os.getenv("PROJECT_ID", "gtm-mcv3pd5-ytbin")
TOPIC_ID = os.getenv("TOPIC_ID", "apexlegends")

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

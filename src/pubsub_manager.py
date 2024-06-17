# pubsub_manager.py
import os
from google.cloud import pubsub_v1
import logging
import config

# Set the environment variable for Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.path.dirname(__file__), "service_account.json")

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(config.PROJECT_ID, config.TOPIC_ID)

logger = logging.getLogger('websocket_server')

def publish_message(message):
    data = message.encode("utf-8")
    future = publisher.publish(topic_path, data=data)
    logger.info(f"Message published with ID {future.result()}")

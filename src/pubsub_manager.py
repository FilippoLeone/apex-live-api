# pubsub_manager.py
import os
from google.cloud import pubsub_v1
import logging
import config
import time
from datetime import datetime

# Set the environment variable for Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.path.dirname(__file__), "service_account.json")

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(config.PROJECT_ID, config.TOPIC_ID)

logger = logging.getLogger('websocket_server')

# Tracking variables for pubsub status
_last_publish_time = None
_total_messages_published = 0
_publish_errors = 0

def publish_message(message):
    global _last_publish_time, _total_messages_published, _publish_errors
    
    try:
        data = message.encode("utf-8")
        future = publisher.publish(topic_path, data=data)
        message_id = future.result()
        
        _last_publish_time = time.time()
        _total_messages_published += 1
        
        logger.info(f"Message published with ID {message_id}")
        return True
    except Exception as e:
        _publish_errors += 1
        logger.error(f"Failed to publish message: {e}")
        return False

def get_pubsub_status():
    """Get current pubsub streaming status"""
    now = time.time()
    is_streaming = False
    
    if _last_publish_time:
        # Consider streaming active if we published within last 30 seconds
        time_since_last = now - _last_publish_time
        is_streaming = time_since_last < 30
        
        return {
            "streaming": is_streaming,
            "last_publish": datetime.fromtimestamp(_last_publish_time).isoformat(),
            "seconds_since_last": int(time_since_last),
            "total_messages": _total_messages_published,
            "errors": _publish_errors
        }
    else:
        return {
            "streaming": False,
            "last_publish": None,
            "seconds_since_last": None,
            "total_messages": _total_messages_published,
            "errors": _publish_errors
        }

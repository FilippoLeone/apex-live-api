# data_store.py
import asyncio
import json
import redis.asyncio as redis # Use redis.asyncio for async operations
import logging
import config # Changed from relative to absolute import

logger = logging.getLogger(__name__)

# Global Redis connection pool
redis_pool = None

# data_updated_event will be initialized in main.py with the correct event loop
data_updated_event = None

async def init_data_store_event(loop):
    """Initializes the data_updated_event with the correct loop."""
    global data_updated_event
    data_updated_event = asyncio.Event(loop=loop)
    logger.info("data_updated_event initialized with the provided event loop.")

async def init_redis_pool():
    """Initializes the Redis connection pool."""
    global redis_pool
    try:
        redis_pool = redis.ConnectionPool(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)
        logger.info(f"Successfully connected to Redis at {config.REDIS_HOST}:{config.REDIS_PORT}")
    except Exception as e:
        logger.error(f"Could not connect to Redis: {e}")
        redis_pool = None # Ensure pool is None if connection fails

async def get_redis_connection():
    """Gets a Redis connection from the pool."""
    if not redis_pool:
        await init_redis_pool() # Attempt to initialize if not already
        if not redis_pool: # If still None after attempt, raise error
            raise ConnectionError("Redis connection pool is not available.")
    return redis.Redis(connection_pool=redis_pool)

async def update_data_store(result_type, data):
    """Updates data in Redis and sets the event."""
    try:
        r = await get_redis_connection()
        # Store data as JSON string
        await r.set(result_type, json.dumps(data))
        await r.close()
        if data_updated_event:
            data_updated_event.set()
        else:
            logger.warning("data_updated_event not initialized, cannot set event.")
        logger.debug(f"Data for {result_type} updated in Redis.")
    except Exception as e:
        logger.error(f"Error updating data in Redis for {result_type}: {e}")

async def get_data_store():
    """Retrieves all keys from Redis (use with caution in production)."""
    try:
        r = await get_redis_connection()
        keys = await r.keys('*')
        all_data = {}
        for key_bytes in keys:
            key = key_bytes.decode('utf-8')
            value_bytes = await r.get(key)
            if value_bytes:
                all_data[key] = json.loads(value_bytes.decode('utf-8'))
        await r.close()
        return all_data
    except Exception as e:
        logger.error(f"Error retrieving all data from Redis: {e}")
        return {}

async def get_data_by_type(result_type):
    """Retrieves specific data by type (key) from Redis."""
    try:
        r = await get_redis_connection()
        value_bytes = await r.get(result_type)
        await r.close()
        if value_bytes:
            return json.loads(value_bytes.decode('utf-8'))
        return {}
    except Exception as e:
        logger.error(f"Error retrieving data from Redis for {result_type}: {e}")
        return {}

async def wait_for_data_update(timeout=5):
    """
    Waits for the local data_updated_event.
    """
    if not data_updated_event:
        logger.warning("data_updated_event not initialized. Cannot wait.")
        return False # Or raise an error, depending on desired behavior
    try:
        data_updated_event.clear()
        await asyncio.wait_for(data_updated_event.wait(), timeout)
    except asyncio.TimeoutError:
        logger.debug("Timeout waiting for data update event.")
        return False
    return True

# It might be useful to add functions for more specific Redis operations
# e.g., incrementing counters, managing lists, sets, or hashes directly
# if the application logic can benefit from Redis's native data structures.
# For example:
# async def increment_event_counter(event_type: str):
#     try:
#         r = await get_redis_connection()
#         await r.incr(f"event_counter:{event_type}")
#         await r.close()
#     except Exception as e:
#         logger.error(f"Error incrementing event counter for {event_type}: {e}")

# async def add_player_to_lobby(lobby_id: str, player_info: dict):
#     try:
#         r = await get_redis_connection()
#         await r.hset(f"lobby:{lobby_id}:players", player_info['playerId'], json.dumps(player_info))
#         await r.close()
#     except Exception as e:
#         logger.error(f"Error adding player to lobby {lobby_id}: {e}")

# Ensure Redis pool is initialized when the application starts.
# This can be done in main.py

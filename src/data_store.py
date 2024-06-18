# data_store.py
import asyncio

data_store = {}
data_updated_event = asyncio.Event()

def update_data_store(result_type, data):
    data_store[result_type] = data
    data_updated_event.set()

def get_data_store():
    return data_store

def get_data_by_type(result_type):
    return data_store.get(result_type, {})

async def wait_for_data_update(timeout=5):
    try:
        data_updated_event.clear()
        await asyncio.wait_for(data_updated_event.wait(), timeout)
    except asyncio.TimeoutError:
        return False
    return True

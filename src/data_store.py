data_store = {}

def update_data_store(result_type, data):
    data_store[result_type] = data

def get_data_store():
    return data_store

def get_data_by_type(result_type):
    return data_store.get(result_type, {})

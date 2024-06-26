# websocket_server.py
import asyncio
import websockets
from websockets.server import WebSocketServerProtocol
from google.protobuf import symbol_database
import logging
import json
from google.protobuf.json_format import MessageToDict
from pubsub_manager import publish_message
import os, sys

# Respect the original file structure for path
current_script_directory = os.path.dirname(os.path.abspath(__file__))
parent_directory = os.path.abspath(os.path.join(current_script_directory, os.pardir, os.pardir))
sys.path.append(parent_directory)
import events_pb2
from data_store import update_data_store

connected_websockets = set()

logger = logging.getLogger('websocket_server')

async def ws_handler(websocket: WebSocketServerProtocol, path: str):
    connected_websockets.add(websocket)
    logger.info("New client connected.")
    
    try:
        async for message in websocket:
            pblist = events_pb2.LiveAPIEvent()
            pblist.ParseFromString(message)
            result_type = pblist.gameMessage.TypeName()
            logger.info(f"Result type: {result_type}")
            msg_result = symbol_database.Default().GetSymbol(result_type)()
            pblist.gameMessage.Unpack(msg_result)
            logger.info(f"Received message from client: {msg_result}")
            
            msg_dict = MessageToDict(msg_result)
            if msg_dict:
                jsonreq = json.dumps(msg_dict)
                publish_message(jsonreq)
                await websocket.send(jsonreq)
                update_data_store(result_type, jsonreq)
                logger.info(f"Writing {result_type} to data store")

    except websockets.exceptions.ConnectionClosedError:
        logger.info("Client disconnected.")
    except Exception as e:
        logger.error(f"Error handling client connection: {e}")
        await websocket.close()
    finally:
        connected_websockets.remove(websocket)

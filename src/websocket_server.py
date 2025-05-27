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

async def ws_handler(websocket, path="/"):
    """
    Handle WebSocket connections.
    
    Args:
        websocket: The WebSocket connection object
        path: The request path, defaulting to "/" if not provided
    """
    connected_websockets.add(websocket)
    logger.info(f"New client connected. Path: {path}")
    
    try:
        async for message in websocket:
            try:
                logger.debug(f"Received raw message of length: {len(message)}")
                pblist = events_pb2.LiveAPIEvent()
                pblist.ParseFromString(message)
                result_type = pblist.gameMessage.TypeName()
                logger.info(f"Result type: {result_type}")
                
                try:
                    msg_result = symbol_database.Default().GetSymbol(result_type)()
                    pblist.gameMessage.Unpack(msg_result)
                    logger.info(f"Received message from client: {msg_result}")
                    
                    # Convert to dict for data store and pubsub
                    msg_dict = MessageToDict(msg_result)
                    if msg_dict:
                        # Pass the dictionary directly, not the JSON string
                        publish_message(json.dumps(msg_dict)) # pubsub might still expect a string
                        await update_data_store(result_type, msg_dict) # Pass the dict
                        logger.info(f"Writing {result_type} to data store")
                        
                        # Handle Response messages specifically
                        if result_type == "rtech.liveapi.Response":
                            await handle_response_message(msg_result)
                            
                except Exception as symbol_error:
                    logger.error(f"Error processing message: \"{symbol_error}\"")
                    # Enhanced error handling - try alternative message processing
                    try:
                        # Try to handle known message types without symbol lookup
                        if "CustomMatch_LobbyPlayers" in result_type:
                            # Handle lobby players data
                            try:
                                msg_result = events_pb2.CustomMatch_LobbyPlayers()
                                pblist.gameMessage.Unpack(msg_result)
                                msg_dict = MessageToDict(msg_result)
                                if msg_dict:
                                    # Pass the dictionary directly
                                    publish_message(json.dumps(msg_dict)) # pubsub might still expect a string
                                    await update_data_store(result_type, msg_dict) # Pass the dict
                                    logger.info(f"Successfully processed {result_type} via fallback")
                            except Exception as fallback_error:
                                logger.error(f"Fallback processing failed for {result_type}: {fallback_error}")
                        
                        elif "CustomMatch_LegendBanStatus" in result_type:
                            # Handle legend ban status data
                            try:
                                msg_result = events_pb2.CustomMatch_LegendBanStatus()
                                pblist.gameMessage.Unpack(msg_result)
                                msg_dict = MessageToDict(msg_result)
                                if msg_dict:
                                    # Pass the dictionary directly
                                    publish_message(json.dumps(msg_dict)) # pubsub might still expect a string
                                    await update_data_store(result_type, msg_dict) # Pass the dict
                                    logger.info(f"Successfully processed {result_type} via fallback")
                            except Exception as fallback_error:
                                logger.error(f"Fallback processing failed for {result_type}: {fallback_error}")
                        
                        elif "Response" in result_type:
                            # Handle Response messages
                            try:
                                msg_result = events_pb2.Response()
                                pblist.gameMessage.Unpack(msg_result)
                                msg_dict = MessageToDict(msg_result)
                                if msg_dict:
                                    # Pass the dictionary directly
                                    publish_message(json.dumps(msg_dict)) # pubsub might still expect a string
                                    await update_data_store(result_type, msg_dict) # Pass the dict
                                    await handle_response_message(msg_result) # Assuming this expects the protobuf message
                                    logger.info(f"Successfully processed {result_type} via fallback")
                            except Exception as fallback_error:
                                logger.error(f"Fallback processing failed for {result_type}: {fallback_error}")
                        
                        else:
                            # Store raw data for unknown types
                            raw_msg = pblist.gameMessage.value
                            logger.info(f"Storing raw message data for {result_type}, length: {len(raw_msg)} bytes")
                            await update_data_store(result_type, { # Pass a dict for raw data as well
                                "raw_data": raw_msg.hex(), 
                                "type": result_type,
                                "timestamp": logger._created if hasattr(logger, '_created') else 0
                            })
                    except Exception as processing_error:
                        logger.error(f"Complete message processing failed: {processing_error}")
                        # Continue processing other messages
                        
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                # Continue processing other messages even if one fails

    except websockets.exceptions.ConnectionClosedError:
        logger.info("Client disconnected.")
    except Exception as e:
        logger.error(f"Error handling client connection: {e}")
        await websocket.close()
    finally:
        connected_websockets.remove(websocket)

async def handle_response_message(response_msg):
    """
    Handle Response messages from the game.
    
    Args:
        response_msg: The Response protobuf message
    """
    if response_msg.success:
        logger.info("Request acknowledged successfully by the game")
        if response_msg.result:
            # Unpack and handle the result if present
            try:
                result_type = response_msg.result.TypeName()
                logger.info(f"Response contains result of type: {result_type}")
                
                # Try to unpack the result and store it separately
                try:
                    result_msg = symbol_database.Default().GetSymbol(result_type)()
                    response_msg.result.Unpack(result_msg)
                    logger.info(f"Response result: {result_msg}")
                    
                    # Store the unpacked result in the data store under its specific type
                    result_dict = MessageToDict(result_msg)
                    if result_dict:
                        # Pass the dictionary directly
                        await update_data_store(result_type, result_dict) # Pass the dict
                        logger.info(f"Stored response result under type: {result_type}")
                        
                except Exception as unpack_error:
                    logger.warning(f"Could not unpack result of type {result_type}: {unpack_error}")
                    # Try fallback unpacking for known types
                    try:
                        if "CustomMatch_SetSettings" in result_type:
                            result_msg = events_pb2.CustomMatch_SetSettings()
                            response_msg.result.Unpack(result_msg)
                            result_dict = MessageToDict(result_msg)
                            if result_dict:
                                # Pass the dictionary directly
                                await update_data_store(result_type, result_dict) # Pass the dict
                                logger.info(f"Successfully unpacked {result_type} via fallback")
                        elif "CustomMatch_LegendBanStatus" in result_type:
                            result_msg = events_pb2.CustomMatch_LegendBanStatus()
                            response_msg.result.Unpack(result_msg)
                            result_dict = MessageToDict(result_msg)
                            if result_dict:
                                # Pass the dictionary directly
                                await update_data_store(result_type, result_dict) # Pass the dict
                                logger.info(f"Successfully unpacked {result_type} via fallback")
                    except Exception as fallback_error:
                        logger.error(f"Fallback unpacking also failed for {result_type}: {fallback_error}")
                        
            except Exception as result_error:
                logger.error(f"Error processing response result: {result_error}")
    else:
        logger.warning("Request was not successful")
        if hasattr(response_msg, 'error_message'):
            logger.warning(f"Error message: {response_msg.error_message}")
        
async def send_request_to_game(request_msg):
    """
    Send a Request message to all connected Apex Legends clients.
    
    Args:
        request_msg: The Request protobuf message to send
    """
    if not connected_websockets:
        logger.warning("No connected websockets to send request to")
        return False
        
    serialized_request = request_msg.SerializeToString()
    disconnected_sockets = set()
    
    for ws in connected_websockets:
        try:
            await ws.send(serialized_request)
            logger.debug("Request sent to websocket client")
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed while sending request")
            disconnected_sockets.add(ws)
        except Exception as e:
            logger.error(f"Error sending request to websocket: {e}")
            disconnected_sockets.add(ws)
    
    # Clean up disconnected sockets
    connected_websockets.difference_update(disconnected_sockets)
    
    return len(connected_websockets) > 0

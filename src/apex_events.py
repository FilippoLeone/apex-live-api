# apex_events.py
import asyncio
import logging
import json
import os
import sys
from google.protobuf.json_format import MessageToJson
from data_store import update_data_store, get_data_store, get_data_by_type, wait_for_data_update

# Respect the original file structure for path
current_script_directory = os.path.dirname(os.path.abspath(__file__))
parent_directory = os.path.abspath(os.path.join(current_script_directory, os.pardir, os.pardir)) # Pardir two times cuz 2 dir above
sys.path.append(parent_directory)
import events_pb2

logger = logging.getLogger('websocket_server')

def create_lobby():
    request = events_pb2.Request()
    request.customMatch_CreateLobby.CopyFrom(events_pb2.CustomMatch_CreateLobby())
    request.withAck = True

    logger.info("Sent request to create a custom match lobby.")

    # Send to all connected websockets
    from websocket_server import connected_websockets
    for ws in connected_websockets:
        asyncio.create_task(ws.send(request.SerializeToString()))

    return request

def get_lobby_players():
    request = events_pb2.Request()
    request.customMatch_GetLobbyPlayers.CopyFrom(events_pb2.CustomMatch_GetLobbyPlayers())
    request.withAck = True

    logger.info(f"Pulling player info. {request}")

    # Send to all connected websockets
    from websocket_server import connected_websockets
    for ws in connected_websockets:
        asyncio.create_task(ws.send(request.SerializeToString()))

    return request

async def fetch_lobby_players(timeout=5):
    get_lobby_players()
    success = await wait_for_data_update(timeout)
    if not success:
        logger.error("Fetching lobby players timed out.")
        return {}
    return get_data_by_type('rtech.liveapi.CustomMatch_LobbyPlayers')

def message_to_json(message):
    return MessageToJson(message)

def message_to_dict(message):
    return json.loads(MessageToJson(message))

# Add new request functions
def change_camera(poi=None, name=None):
    request = events_pb2.Request()
    if poi:
        request.changeCam.poi = poi
    if name:
        request.changeCam.name = name
    request.withAck = True

    logger.info("Sent request to change camera.")

    from websocket_server import connected_websockets
    for ws in connected_websockets:
        asyncio.create_task(ws.send(request.SerializeToString()))

    return request

def pause_toggle(pre_timer):
    request = events_pb2.Request()
    request.pauseToggle.preTimer = pre_timer
    request.withAck = True

    logger.info("Sent request to toggle pause.")

    from websocket_server import connected_websockets
    for ws in connected_websockets:
        asyncio.create_task(ws.send(request.SerializeToString()))

    return request

def set_ready(is_ready):
    request = events_pb2.Request()
    request.customMatch_SetReady.isReady = is_ready
    request.withAck = True

    logger.info("Sent request to set ready state.")

    from websocket_server import connected_websockets
    for ws in connected_websockets:
        asyncio.create_task(ws.send(request.SerializeToString()))

    return request

def set_matchmaking(enabled):
    request = events_pb2.Request()
    request.customMatch_SetMatchmaking.enabled = enabled
    request.withAck = True

    logger.info("Sent request to set matchmaking state.")

    from websocket_server import connected_websockets
    for ws in connected_websockets:
        asyncio.create_task(ws.send(request.SerializeToString()))

    return request

def set_team(team_id, target_hardware_name, target_nucleus_hash):
    request = events_pb2.Request()
    request.customMatch_SetTeam.teamId = team_id
    request.customMatch_SetTeam.targetHardwareName = target_hardware_name
    request.customMatch_SetTeam.targetNucleusHash = target_nucleus_hash
    request.withAck = True

    logger.info("Sent request to set team.")

    from websocket_server import connected_websockets
    for ws in connected_websockets:
        asyncio.create_task(ws.send(request.SerializeToString()))

    return request

def kick_player(target_hardware_name, target_nucleus_hash):
    request = events_pb2.Request()
    request.customMatch_KickPlayer.targetHardwareName = target_hardware_name
    request.customMatch_KickPlayer.targetNucleusHash = target_nucleus_hash
    request.withAck = True

    logger.info("Sent request to kick player.")

    from websocket_server import connected_websockets
    for ws in connected_websockets:
        asyncio.create_task(ws.send(request.SerializeToString()))

    return request

def set_settings(settings):
    request = events_pb2.Request()
    for key, value in settings.items():
        setattr(request.customMatch_SetSettings, key, value)
    request.withAck = True

    logger.info("Sent request to set settings.")

    from websocket_server import connected_websockets
    for ws in connected_websockets:
        asyncio.create_task(ws.send(request.SerializeToString()))

    return request

def send_chat(text):
    request = events_pb2.Request()
    request.customMatch_SendChat.text = text
    request.withAck = True

    logger.info("Sent request to send chat.")

    from websocket_server import connected_websockets
    for ws in connected_websockets:
        asyncio.create_task(ws.send(request.SerializeToString()))

    return request

async def get_lobby_token():
    request = get_lobby_players()
    # Assuming get_lobby_players will somehow obtain a lobby token
    return data_store.get('rtech.liveapi.CustomMatch_LobbyPlayers', {})

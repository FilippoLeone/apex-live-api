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

    # Send to all connected websockets using proper async mechanism
    asyncio.create_task(send_request_to_connected_clients(request))

    return request

def get_lobby_players():
    request = events_pb2.Request()
    request.customMatch_GetLobbyPlayers.CopyFrom(events_pb2.CustomMatch_GetLobbyPlayers())
    request.withAck = True

    logger.info(f"Pulling player info. {request}")

    # Send to all connected websockets using proper async mechanism
    asyncio.create_task(send_request_to_connected_clients(request))

    return request

async def send_request_to_connected_clients(request):
    """
    Send a request to all connected websocket clients.
    
    Args:
        request: The protobuf Request message to send
    """
    from websocket_server import send_request_to_game
    await send_request_to_game(request)

async def fetch_lobby_players(timeout=5):
    get_lobby_players()
    success = await wait_for_data_update(timeout)
    if not success:
        logger.error("Fetching lobby players timed out.")
        return {}
    return await get_data_by_type('rtech.liveapi.CustomMatch_LobbyPlayers')

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

    asyncio.create_task(send_request_to_connected_clients(request))

    return request

def pause_toggle(pre_timer):
    request = events_pb2.Request()
    request.pauseToggle.preTimer = pre_timer
    request.withAck = True

    logger.info("Sent request to toggle pause.")

    asyncio.create_task(send_request_to_connected_clients(request))

    return request

def set_ready(is_ready):
    request = events_pb2.Request()
    request.customMatch_SetReady.isReady = is_ready
    request.withAck = True

    logger.info("Sent request to set ready state.")

    asyncio.create_task(send_request_to_connected_clients(request))

    return request

def set_matchmaking(enabled):
    request = events_pb2.Request()
    request.customMatch_SetMatchmaking.enabled = enabled
    request.withAck = True

    logger.info("Sent request to set matchmaking state.")

    asyncio.create_task(send_request_to_connected_clients(request))

    return request

def set_team(team_id, target_hardware_name, target_nucleus_hash):
    request = events_pb2.Request()
    request.customMatch_SetTeam.teamId = team_id
    request.customMatch_SetTeam.targetHardwareName = target_hardware_name
    request.customMatch_SetTeam.targetNucleusHash = target_nucleus_hash
    request.withAck = True

    logger.info("Sent request to set team.")

    asyncio.create_task(send_request_to_connected_clients(request))

    return request

def kick_player(target_hardware_name, target_nucleus_hash):
    request = events_pb2.Request()
    request.customMatch_KickPlayer.targetHardwareName = target_hardware_name
    request.customMatch_KickPlayer.targetNucleusHash = target_nucleus_hash
    request.withAck = True

    logger.info("Sent request to kick player.")

    asyncio.create_task(send_request_to_connected_clients(request))

    return request

def set_settings(settings_data: dict): # Type hint for clarity
    request = events_pb2.Request()
    
    # These are the fields defined in the CustomMatch_SetSettings message in your events.proto
    defined_fields = request.customMatch_SetSettings.DESCRIPTOR.fields_by_name.keys()

    for key, value in settings_data.items():
        if key in defined_fields:
            try:
                setattr(request.customMatch_SetSettings, key, value)
            except TypeError as e:
                logger.error(f"Type error setting attribute '{key}' to value '{value}' of type {type(value)} on CustomMatch_SetSettings: {e}")
            except Exception as e:
                logger.error(f"Unexpected error setting attribute '{key}' on CustomMatch_SetSettings: {e}")
        else:
            # This field is not part of CustomMatch_SetSettings.
            # It could be a top-level field on the Request object, or simply an unknown/extra field.
            # For now, we log a warning if it's not specifically for CustomMatch_SetSettings.
            # If fields like targetPlayerName are meant for the top-level Request,
            # that would require different handling (e.g., request.targetPlayerName = value).
            logger.warning(f"Field '{key}' with value '{value}' is not a recognized field of CustomMatch_SetSettings. Ignoring for this sub-message.")

    request.withAck = True
    # logger.info(f"Prepared set_settings request: {request}") # Uncomment for deep debugging if needed
    asyncio.create_task(send_request_to_connected_clients(request))
    return request

def send_chat(text):
    request = events_pb2.Request()
    request.customMatch_SendChat.text = text
    request.withAck = True

    logger.info("Sent request to send chat.")

    asyncio.create_task(send_request_to_connected_clients(request))

    return request

# Additional missing request functions
def get_settings():
    """Get current custom match settings."""
    request = events_pb2.Request()
    request.customMatch_GetSettings.CopyFrom(events_pb2.CustomMatch_GetSettings())
    request.withAck = True

    logger.info("Sent request to get settings.")

    asyncio.create_task(send_request_to_connected_clients(request))

    return request

def set_team_name(team_id, team_name):
    """Set a team name for a custom match."""
    request = events_pb2.Request()
    request.customMatch_SetTeamName.teamId = team_id
    request.customMatch_SetTeamName.teamName = team_name
    request.withAck = True

    logger.info("Sent request to set team name.")

    asyncio.create_task(send_request_to_connected_clients(request))

    return request

def set_spawn_point(team_id, spawn_point):
    """Set spawn point for a team."""
    request = events_pb2.Request()
    request.customMatch_SetSpawnPoint.teamId = team_id
    request.customMatch_SetSpawnPoint.spawnPoint = spawn_point
    request.withAck = True

    logger.info("Sent request to set spawn point.")

    asyncio.create_task(send_request_to_connected_clients(request))

    return request

def set_end_ring_exclusion(section_to_exclude):
    """Set end ring exclusion area."""
    request = events_pb2.Request()
    request.customMatch_SetEndRingExclusion.sectionToExclude = section_to_exclude
    request.withAck = True

    logger.info("Sent request to set end ring exclusion.")

    asyncio.create_task(send_request_to_connected_clients(request))

    return request

def get_legend_ban_status():
    """Get legend ban status."""
    request = events_pb2.Request()
    request.customMatch_GetLegendBanStatus.CopyFrom(events_pb2.CustomMatch_GetLegendBanStatus())
    request.withAck = True

    logger.info("Sent request to get legend ban status.")

    asyncio.create_task(send_request_to_connected_clients(request))

    return request

def set_legend_ban(legend_refs):
    """Set legend ban list."""
    request = events_pb2.Request()
    request.customMatch_SetLegendBan.legendRefs.extend(legend_refs)
    request.withAck = True

    logger.info("Sent request to set legend ban.")

    asyncio.create_task(send_request_to_connected_clients(request))

    return request

def change_camera_by_nucleus_hash(nucleus_hash):
    """Change camera to a player by nucleus hash."""
    request = events_pb2.Request()
    request.changeCam.nucleusHash = nucleus_hash
    request.withAck = True

    logger.info("Sent request to change camera by nucleus hash.")

    asyncio.create_task(send_request_to_connected_clients(request))

    return request

async def get_lobby_token():
    request = get_lobby_players()
    # Assuming get_lobby_players will somehow obtain a lobby token
    return await get_data_by_type('rtech.liveapi.CustomMatch_LobbyPlayers')

def set_camera_position(x: float, y: float, z: float):
    """Sets the camera position."""
    request = events_pb2.Request()
    request.customMatch_SetCameraPosition.x = x
    request.customMatch_SetCameraPosition.y = y
    request.customMatch_SetCameraPosition.z = z
    request.withAck = True

    logger.info(f"Sent request to set camera position to x={x}, y={y}, z={z}.")
    asyncio.create_task(send_request_to_connected_clients(request))
    return request

# api_routes.py
import aiohttp_jinja2
from aiohttp import web
import logging
import apex_events
import discord_manager
import json
import asyncio  # Added missing asyncio import
from data_store import get_data_by_type, get_data_store, get_redis_connection
import config  # Added import for config module
from datetime import datetime
from pubsub_manager import get_pubsub_status

logger = logging.getLogger('websocket_server')

async def get_data(request):
    result_type = request.match_info.get('type', None)
    if result_type:
        data = await get_data_by_type(result_type) 
        return web.json_response(data)
    data = await get_data_store()  
    return web.json_response(data)

async def get_lobby_request(request):
    lobby_players = await apex_events.fetch_lobby_players()
    return web.json_response(lobby_players)

async def create_lobby_request(request):
    response = apex_events.create_lobby()
    response_json = apex_events.message_to_dict(response)  # Convert the protobuf message to a dictionary
    return web.json_response(response_json)

async def change_camera_request(request):
    body = await request.json()
    poi_str = body.get('poi')
    name = body.get('name')
    poi_int = None
    if poi_str:
        try:
            poi_int = int(poi_str)
        except ValueError:
            # Log an error or return a proper HTTP error response
            logger.error(f"Invalid POI value received: {poi_str}")
            return web.Response(text="Invalid POI value. Must be an integer.", status=400)
    response = apex_events.change_camera(poi=poi_int, name=name)
    response_json = apex_events.message_to_dict(response)
    return web.json_response(response_json)

async def pause_toggle_request(request):
    body = await request.json()
    pre_timer = body.get('preTimer')
    response = apex_events.pause_toggle(pre_timer)
    response_json = apex_events.message_to_dict(response)
    return web.json_response(response_json)

async def set_ready_request(request):
    body = await request.json()
    is_ready = body.get('isReady')
    response = apex_events.set_ready(is_ready)
    response_json = apex_events.message_to_dict(response)
    return web.json_response(response_json)

async def set_matchmaking_request(request):
    logger.info(f"Received set_matchmaking_request. Headers: {request.headers}")
    try:
        body = await request.json()
        logger.info(f"Request body: {body}")
    except Exception as e:
        logger.error(f"Error parsing JSON body: {e}")
        # Attempt to read raw body for debugging if JSON parsing fails
        try:
            raw_body = await request.text()
            logger.info(f"Raw request body: {raw_body}")
        except Exception as re:
            logger.error(f"Error reading raw request body: {re}")
        return web.Response(text="Invalid JSON body", status=400)
        
    enabled = body.get('enabled')
    if not isinstance(enabled, bool):
        logger.warning(f"'enabled' flag is not a boolean: {enabled} (type: {type(enabled)})")
        # Optionally, return an error if 'enabled' is not a boolean or handle as needed
        # return web.Response(text="'enabled' flag must be a boolean", status=400)
        
    response = apex_events.set_matchmaking(enabled)
    response_json = apex_events.message_to_dict(response)
    return web.json_response(response_json)

async def set_team_request(request):
    body = await request.json()
    team_id = body.get('teamId')
    target_hardware_name = body.get('targetHardwareName')
    target_nucleus_hash = body.get('targetNucleusHash')
    response = apex_events.set_team(team_id, target_hardware_name, target_nucleus_hash)
    response_json = apex_events.message_to_dict(response)
    return web.json_response(response_json)

async def kick_player_request(request):
    body = await request.json()
    target_hardware_name = body.get('targetHardwareName')
    target_nucleus_hash = body.get('targetNucleusHash')
    response = apex_events.kick_player(target_hardware_name, target_nucleus_hash)
    response_json = apex_events.message_to_dict(response)
    return web.json_response(response_json)

async def set_settings_request(request):
    logger.info(f"Received set_settings_request. Headers: {request.headers}")
    raw_body = await request.text()
    logger.info(f"Raw request body for set_settings: {raw_body}")
    try:
        body = json.loads(raw_body) # Try parsing with json.loads for detailed error
        logger.info(f"Successfully parsed JSON body: {body}")
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON body for set_settings: {str(e)} (at position {e.pos})") # Changed e.message to str(e)
        return web.Response(text=f"Invalid JSON body: {str(e)}", status=400) # Changed e.message to str(e)
    except Exception as e:
        logger.error(f"Unexpected error processing set_settings request: {e}")
        return web.Response(text="Unexpected error processing request", status=500)
        
    response = apex_events.set_settings(body)
    response_json = apex_events.message_to_dict(response)
    return web.json_response(response_json)

async def send_chat_request(request):
    body = await request.json()
    text = body.get('text')
    response = apex_events.send_chat(text)
    response_json = apex_events.message_to_dict(response)
    return web.json_response(response_json)

async def get_lobby_token_request(request):
    response = await apex_events.get_lobby_token()
    if response and 'playerToken' in response: # Ensure playerToken exists
        await discord_manager.send_discord_message(config.DISCORD_CHANNEL, config.DISCORD_BOT_TOKEN, f"!schedule_autostart {response['playerToken']} false")
        return web.json_response({'key': response['playerToken']})
    # Return an empty JSON object or an error status if token is not found
    logger.warning("Lobby token not found or response was empty.") # Log this event
    return web.json_response({}, status=404 if not response else 200) # Or appropriate status

async def schedule_autostart_request(request):
    body = await request.json()
    lobby_channel_name = body.get('lobby_channel_name')
    min_max_teams = body.get('min_max_teams')
    min_max_team_size = body.get('min_max_team_size')
    time_to_wait = body.get('time_to_wait')
    private_message = body.get('private_message')
    keep_autostart = body.get('keep_autostart')

    # Fetch the player token
    token_response = await apex_events.get_lobby_token() # Assuming this returns a dict like {'playerToken': 'TOKEN_VALUE'}
    
    player_token = None
    if token_response and isinstance(token_response, dict) and 'playerToken' in token_response:
        player_token = token_response['playerToken']
    
    if player_token:
        # Corrected call: ensure all parameters including player_token are passed
        await discord_manager.schedule_autostart(
            lobby_channel_name=lobby_channel_name, 
            min_max_teams=min_max_teams, 
            min_max_team_size=min_max_team_size, 
            time_to_wait=time_to_wait, 
            private_message=private_message, 
            keep_autostart=keep_autostart, 
            player_token=player_token  # Pass the fetched player_token
        )
        return web.json_response({'message': 'Autostart scheduled successfully', 'playerToken': player_token})
    else:
        logger.error("Failed to retrieve player token for scheduling autostart.")
        return web.json_response({'error': 'Failed to retrieve player token'}, status=500)

@aiohttp_jinja2.template('index.html')
async def index(request):
    return {}

# New endpoints for fetching player names, hardware names, and nucleus hashes
# (These functions have been moved to the bottom of the file as _request versions)

# Health check endpoint
async def health_check(request):
    """Check the status of WebSocket connections, Redis, game data, and pubsub streaming"""
    try:
        # Check WebSocket status
        websocket_connected = False
        websocket_count = 0
        try:
            from websocket_server import connected_websockets
            websocket_connected = len(connected_websockets) > 0
            websocket_count = len(connected_websockets)
        except ImportError as e:
            logger.warning(f"Could not import websocket_server: {e}")
        except Exception as e:
            logger.warning(f"Error checking websocket status: {e}")
        
        # Check Redis connection
        redis_connected = False
        try:
            r = await get_redis_connection()
            await r.ping()
            await r.close()
            redis_connected = True
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
        
        # Check if game data is available and recent
        game_data_available = False
        data_freshness = "unknown"
        try:
            data = await get_data_store()
            if data and isinstance(data, dict) and len(data) > 0:
                game_data_available = True
                
                # Check for recent lobby data
                lobby_data = data.get('rtech.liveapi.CustomMatch_LobbyPlayers')
                if lobby_data:
                    data_freshness = "recent"
                else:
                    data_freshness = "stale"
        except Exception as e:
            logger.warning(f"Error checking game data: {e}")
        
        # Check pubsub streaming status
        pubsub_status = {"streaming": False, "error": "Unable to check"}
        try:
            pubsub_status = get_pubsub_status()
        except ImportError:
            pubsub_status["error"] = "Pubsub manager not available"
        except Exception as e:
            pubsub_status["error"] = str(e)
        
        # Test websocket responsiveness by checking recent API responses
        websocket_responsive = False
        if websocket_connected:
            # Check if we have recent successful API responses
            try:
                # Look for recent lobby data or response data
                response_data = await get_data_by_type('rtech.liveapi.CustomMatch_LobbyPlayers')
                if response_data and response_data != "{}":
                    websocket_responsive = True
            except:
                pass
            
            if not websocket_responsive:
                try:
                    response_data = await get_data_by_type('rtech.liveapi.Response')
                    if response_data and response_data != "{}":
                        websocket_responsive = True
                except:
                    pass
        
        # Determine overall status
        if websocket_connected and websocket_responsive and redis_connected and game_data_available:
            overall_status = "healthy"
        elif websocket_connected and redis_connected:
            if websocket_responsive:
                overall_status = "degraded"  # Connected but no game data
            else:
                overall_status = "issues"    # Connected but not responding
        else:
            overall_status = "error"
        
        status = {
            "status": overall_status,
            "websocket": {
                "connected": websocket_connected,
                "responsive": websocket_responsive,
                "connections": websocket_count
            },
            "redis": {
                "connected": redis_connected
            },
            "game_data": {
                "available": game_data_available,
                "freshness": data_freshness
            },
            "pubsub": pubsub_status,
            "timestamp": datetime.now().isoformat()
        }
        
        return web.json_response(status)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return web.json_response({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status=500)

async def get_settings_request(request):
    # First send the request to get fresh settings
    response = apex_events.get_settings()
    
    # Wait for the response to come back and be processed
    await asyncio.sleep(1.0)  # Increased wait time
    
    # Get the settings from the data store (they should have been updated by the response)
    try:
        # Try to get the latest Response data that might contain settings
        response_data = await get_data_by_type('rtech.liveapi.Response')
        if response_data:
            if isinstance(response_data, str):
                try:
                    response_dict = json.loads(response_data)
                except json.JSONDecodeError:
                    response_dict = {}
            else:
                response_dict = response_data
            
            # Check if this response contains settings data
            if 'result' in response_dict:
                result = response_dict['result']
                if isinstance(result, dict) and ('playlistName' in result or 'selfAssign' in result or 'aimAssist' in result):
                    # This looks like settings data
                    settings = {
                        "playlistName": result.get('playlistName', ''),
                        "adminChat": result.get('adminChat', False),
                        "teamRename": result.get('teamRename', False),
                        "selfAssign": result.get('selfAssign', False),
                        "aimAssist": result.get('aimAssist', False),
                        "anonMode": result.get('anonMode', False)
                    }
                    return web.json_response({"settings": settings})
        
        # Also try to get CustomMatch_SetSettings data directly
        settings_data = await get_data_by_type('rtech.liveapi.CustomMatch_SetSettings')
        if settings_data:
            if isinstance(settings_data, str):
                try:
                    settings_dict = json.loads(settings_data)
                except json.JSONDecodeError:
                    settings_dict = {}
            else:
                settings_dict = settings_data
            
            # Return the settings if found
            if settings_dict:
                settings = {
                    "playlistName": settings_dict.get('playlistName', ''),
                    "adminChat": settings_dict.get('adminChat', False),
                    "teamRename": settings_dict.get('teamRename', False),
                    "selfAssign": settings_dict.get('selfAssign', False),
                    "aimAssist": settings_dict.get('aimAssist', False),
                    "anonMode": settings_dict.get('anonMode', False)
                }
                return web.json_response({"settings": settings})
        
        # Fallback: return empty settings structure
        return web.json_response({
            "settings": {
                "playlistName": "",
                "adminChat": False,
                "teamRename": False,
                "selfAssign": False,
                "aimAssist": False,
                "anonMode": False
            }
        })
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        return web.json_response({
            "settings": {
                "playlistName": "",
                "adminChat": False,
                "teamRename": False,
                "selfAssign": False,
                "aimAssist": False,
                "anonMode": False
            }
        })

async def set_team_name_request(request):
    body = await request.json()
    team_id = body.get('teamId')
    team_name = body.get('teamName')
    
    # Validate inputs
    if team_id is None:
        return web.json_response({'error': 'teamId is required'}, status=400)
    if team_name is None:
        return web.json_response({'error': 'teamName is required'}, status=400)
    
    # Convert team_id to integer if it's a string
    try:
        team_id = int(team_id)
    except (ValueError, TypeError):
        return web.json_response({'error': 'teamId must be a valid integer'}, status=400)
    
    response = apex_events.set_team_name(team_id, team_name)
    response_json = apex_events.message_to_dict(response)
    return web.json_response(response_json)

async def set_spawn_point_request(request):
    body = await request.json()
    team_id = body.get('teamId')
    spawn_point = body.get('spawnPoint')  # This should be an integer ID for pre-defined spawn points
    response = apex_events.set_spawn_point(team_id, spawn_point)
    response_json = apex_events.message_to_dict(response)
    return web.json_response(response_json)

async def set_end_ring_exclusion_request(request):
    body = await request.json()
    # According to protobuf, this should be a MapRegion enum value
    section_to_exclude = body.get('sectionToExclude')
    response = apex_events.set_end_ring_exclusion(section_to_exclude)
    response_json = apex_events.message_to_dict(response)
    return web.json_response(response_json)

async def get_legend_ban_status_request(request):
    # Send request to get fresh legend ban status
    response = apex_events.get_legend_ban_status()
    
    # Wait for the response to come back
    await asyncio.sleep(0.8)
    
    try:
        # Try to get the legend ban status from the data store
        legend_ban_data = await get_data_by_type('rtech.liveapi.CustomMatch_LegendBanStatus')
        if legend_ban_data:
            if isinstance(legend_ban_data, str):
                try:
                    legend_dict = json.loads(legend_ban_data)
                except json.JSONDecodeError:
                    legend_dict = {}
            else:
                legend_dict = legend_ban_data
            
            # Return the legend ban data if found
            if legend_dict and 'legends' in legend_dict:
                return web.json_response(legend_dict)
        
        # Also check in Response messages for legend ban data
        response_data = await get_data_by_type('rtech.liveapi.Response')
        if response_data:
            if isinstance(response_data, str):
                try:
                    response_dict = json.loads(response_data)
                except json.JSONDecodeError:
                    response_dict = {}
            else:
                response_dict = response_data
            
            # Check if this response contains legend ban data
            if 'result' in response_dict:
                result = response_dict['result']
                if isinstance(result, dict) and 'legends' in result:
                    return web.json_response(result)
        
        # If no data found, return empty structure
        return web.json_response({"legends": []})
    except Exception as e:
        logger.error(f"Error getting legend ban status: {e}")
        return web.json_response({"legends": []})

async def set_legend_ban_request(request):
    body = await request.json()
    legend_refs = body.get('legendRefs', [])
    # Support both single character name and list format
    character_name = body.get('characterName')
    is_banned = body.get('isBanned', True)
    
    if character_name:
        # Convert single character ban/unban to list format
        current_bans = []
        try:
            current_status = apex_events.get_legend_ban_status()
            current_status_dict = apex_events.message_to_dict(current_status)
            if 'legends' in current_status_dict:
                current_bans = [legend['reference'] for legend in current_status_dict['legends'] if legend.get('banned', False)]
        except:
            pass
        
        if is_banned and character_name not in current_bans:
            current_bans.append(character_name)
        elif not is_banned and character_name in current_bans:
            current_bans.remove(character_name)
        
        legend_refs = current_bans
    
    response = apex_events.set_legend_ban(legend_refs)
    response_json = apex_events.message_to_dict(response)
    return web.json_response(response_json)

async def change_camera_nucleus_hash_request(request):
    body = await request.json()
    nucleus_hash = body.get('nucleusHash')
    response = apex_events.change_camera_by_nucleus_hash(nucleus_hash)
    response_json = apex_events.message_to_dict(response)
    return web.json_response(response_json)

async def get_player_names_request(request):
    """Get list of current player names for autocomplete"""
    try:
        lobby_data = await get_data_by_type('CustomMatch_LobbyPlayers')
        if lobby_data and 'players' in lobby_data:
            player_names = [player.get('name', '') for player in lobby_data['players'] if player.get('name')]
            return web.json_response(player_names)
        return web.json_response([])
    except Exception as e:
        logger.warning(f"Could not get player names: {e}")
        return web.json_response([])

async def get_hardware_names_request(request):
    """Get list of current hardware names for autocomplete"""
    try:
        lobby_data = await get_data_by_type('CustomMatch_LobbyPlayers')
        if lobby_data and 'players' in lobby_data:
            hardware_names = [player.get('hardwareName', '') for player in lobby_data['players'] if player.get('hardwareName')]
            return web.json_response(hardware_names)
        return web.json_response([])
    except Exception as e:
        logger.warning(f"Could not get hardware names: {e}")
        return web.json_response([])

async def get_nucleus_hashes_request(request):
    """Get list of current nucleus hashes for autocomplete"""
    try:
        lobby_data = await get_data_by_type('CustomMatch_LobbyPlayers')
        if lobby_data and 'players' in lobby_data:
            nucleus_hashes = [player.get('nucleusHash', '') for player in lobby_data['players'] if player.get('nucleusHash')]
            return web.json_response(nucleus_hashes)
        return web.json_response([])
    except Exception as e:
        logger.warning(f"Could not get nucleus hashes: {e}")
        return web.json_response([])

async def set_camera_position_request(request):
    """Handles the /set_camera_position route."""
    try:
        body = await request.json()
        x = body.get('x')
        y = body.get('y')
        z = body.get('z')

        if None in [x, y, z]:
            return web.json_response({'error': 'Missing x, y, or z parameters'}, status=400)
        
        # Ensure x, y, z are floats
        try:
            x = float(x)
            y = float(y)
            z = float(z)
        except ValueError:
            return web.json_response({'error': 'x, y, and z must be numbers'}, status=400)

        response_proto = apex_events.set_camera_position(x=x, y=y, z=z)
        response_json = apex_events.message_to_dict(response_proto)
        return web.json_response(response_json)
    except json.JSONDecodeError:
        logger.error("Error decoding JSON for set_camera_position_request")
        return web.Response(text="Invalid JSON body", status=400)
    except Exception as e:
        logger.error(f"Error in set_camera_position_request: {e}")
        return web.json_response({'error': str(e)}, status=500)

async def pubsub_status_request(request):
    status = get_pubsub_status()
    return web.json_response(status)

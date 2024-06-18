# api_routes.py
import aiohttp_jinja2
from aiohttp import web
import logging
import apex_events
import discord_manager
import json
from data_store import get_data_by_type, get_data_store

logger = logging.getLogger('websocket_server')

async def get_data(request):
    result_type = request.match_info.get('type', None)
    if result_type:
        data = get_data_by_type(result_type)
        return web.json_response(data)
    return web.json_response(get_data_store())

async def get_lobby_request(request):
    lobby_players = await apex_events.fetch_lobby_players()
    return web.json_response(lobby_players)

async def create_lobby_request(request):
    response = apex_events.create_lobby()
    response_json = apex_events.message_to_dict(response)  # Convert the protobuf message to a dictionary
    return web.json_response(response_json)

async def change_camera_request(request):
    body = await request.json()
    poi = body.get('poi')
    name = body.get('name')
    response = apex_events.change_camera(poi=poi, name=name)
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
    body = await request.json()
    enabled = body.get('enabled')
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
    body = await request.json()
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
    if response:
        await discord_manager.send_discord_message(config.DISCORD_CHANNEL, config.DISCORD_BOT_TOKEN, f"!schedule_autostart {json.loads(response)['playerToken']} false")
        return web.json_response({'key': json.loads(response)['playerToken']})
    return web.json_response()

async def schedule_autostart_request(request):
    body = await request.json()
    lobby_channel_name = body.get('lobby_channel_name')
    min_max_teams = body.get('min_max_teams')
    min_max_team_size = body.get('min_max_team_size')
    time_to_wait = body.get('time_to_wait')
    private_message = body.get('private_message')
    keep_autostart = body.get('keep_autostart')

    response = await apex_events.get_lobby_token()
    if response:
        player_token = json.loads(response)['playerToken']
        await discord_manager.schedule_autostart(lobby_channel_name, min_max_teams, min_max_team_size, time_to_wait, private_message, keep_autostart, player_token)
        return web.json_response({'key': player_token})
    return web.json_response()

@aiohttp_jinja2.template('index.html')
async def index(request):
    return {}

# New endpoints for fetching player names, hardware names, and nucleus hashes

async def get_player_names(request):
    players = get_data_store().get('rtech.liveapi.CustomMatch_LobbyPlayers', {}).get('players', [])
    if not players:
        await apex_events.fetch_lobby_players()
        players = get_data_store().get('rtech.liveapi.CustomMatch_LobbyPlayers', {}).get('players', [])
    
    player_names = [player['name'] for player in players]
    logger.info(f"Player names: {player_names}")
    return web.json_response(player_names)

async def get_hardware_names(request):
    players = get_data_store().get('rtech.liveapi.CustomMatch_LobbyPlayers', {}).get('players', [])
    if not players:
        await apex_events.fetch_lobby_players()
        players = get_data_store().get('rtech.liveapi.CustomMatch_LobbyPlayers', {}).get('players', [])
    
    hardware_names = [player['hardwareName'] for player in players]
    logger.info(f"Hardware names: {hardware_names}")
    return web.json_response(hardware_names)

async def get_nucleus_hashes(request):
    players = get_data_store().get('rtech.liveapi.CustomMatch_LobbyPlayers', {}).get('players', [])
    if not players:
        await apex_events.fetch_lobby_players()
        players = get_data_store().get('rtech.liveapi.CustomMatch_LobbyPlayers', {}).get('players', [])
    
    nucleus_hashes = [player['nucleusHash'] for player in players]
    logger.info(f"Nucleus hashes: {nucleus_hashes}")
    return web.json_response(nucleus_hashes)

def setup_routes(app):
    app.router.add_get('/create_lobby', create_lobby_request)
    app.router.add_get('/get_players', get_lobby_request)
    app.router.add_get('/get_data/{type}', get_data)
    app.router.add_get('/get_data', get_data)
    app.router.add_get('/send_discord_token', get_lobby_token_request)
    app.router.add_post('/schedule_autostart', schedule_autostart_request)
    app.router.add_post('/change_camera', change_camera_request)
    app.router.add_post('/pause_toggle', pause_toggle_request)
    app.router.add_post('/set_ready', set_ready_request)
    app.router.add_post('/set_matchmaking', set_matchmaking_request)
    app.router.add_post('/set_team', set_team_request)
    app.router.add_post('/kick_player', kick_player_request)
    app.router.add_post('/set_settings', set_settings_request)
    app.router.add_post('/send_chat', send_chat_request)
    app.router.add_get('/get_player_names', get_player_names)
    app.router.add_get('/get_hardware_names', get_hardware_names)
    app.router.add_get('/get_nucleus_hashes', get_nucleus_hashes)
    app.router.add_get('/', index)

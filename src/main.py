# main.py
import asyncio
from aiohttp import web
import aiohttp_jinja2
import jinja2
from logging_config import setup_logging
import api_routes
import websockets
import websocket_server

logger = setup_logging()

async def main():
    app = web.Application()

    # Register routes
    app.router.add_get('/create_lobby', api_routes.create_lobby_request)
    app.router.add_get('/get_players', api_routes.get_lobby_request)
    app.router.add_get('/send_discord_token', api_routes.get_lobby_token_request)
    app.router.add_post('/schedule_autostart', api_routes.schedule_autostart_request)
    app.router.add_post('/change_camera', api_routes.change_camera_request)
    app.router.add_post('/pause_toggle', api_routes.pause_toggle_request)
    app.router.add_post('/set_ready', api_routes.set_ready_request)
    app.router.add_post('/set_matchmaking', api_routes.set_matchmaking_request)
    app.router.add_post('/set_team', api_routes.set_team_request)
    app.router.add_post('/kick_player', api_routes.kick_player_request)
    app.router.add_post('/set_settings', api_routes.set_settings_request)
    app.router.add_post('/send_chat', api_routes.send_chat_request)
    
    # New routes for fetching data for autocomplete functionality
    app.router.add_get('/get_player_names', api_routes.get_player_names)
    app.router.add_get('/get_hardware_names', api_routes.get_hardware_names)
    app.router.add_get('/get_nucleus_hashes', api_routes.get_nucleus_hashes)
    
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates'))

    app.router.add_get('/', api_routes.index)

    web_runner = web.AppRunner(app)
    await web_runner.setup()
    site = web.TCPSite(web_runner, 'localhost', 8080)
    await site.start()

    start_server = websockets.serve(websocket_server.ws_handler, 'localhost', 7777)

    logger.info("Server starting...")
    await start_server

    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())

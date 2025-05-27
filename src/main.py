# main.py
import asyncio
from aiohttp import web
import aiohttp_jinja2
import jinja2
import os # Added for path manipulation
import sys # Added for path manipulation

# Adjust path to import from src directory if main.py is moved or run from elsewhere
current_script_directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_script_directory)

from logging_config import setup_logging
import api_routes
import websockets
import websocket_server
import data_store # Import data_store to initialize Redis

logger = setup_logging()

async def on_startup(app):
    """Signal handler for application startup."""
    logger.info("Application starting up...")
    # Initialize the data_updated_event with the current event loop
    # before initializing the Redis pool which might use it.
    await data_store.init_data_store_event(asyncio.get_event_loop())
    await data_store.init_redis_pool() # Initialize Redis connection pool

async def on_shutdown(app):
    """Signal handler for application shutdown."""
    logger.info("Application shutting down...")
    if data_store.redis_pool:
        await data_store.redis_pool.disconnect()
        logger.info("Redis connection pool disconnected.")

async def main_app():
    app = web.Application()

    # Register startup and shutdown signals
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

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
    
    # Additional custom match routes
    app.router.add_get('/get_settings', api_routes.get_settings_request)
    app.router.add_post('/set_team_name', api_routes.set_team_name_request)
    app.router.add_post('/set_spawn_point', api_routes.set_spawn_point_request)
    app.router.add_post('/set_end_ring_exclusion', api_routes.set_end_ring_exclusion_request)
    app.router.add_get('/get_legend_ban_status', api_routes.get_legend_ban_status_request)
    app.router.add_post('/set_legend_ban', api_routes.set_legend_ban_request)
    app.router.add_post('/change_camera_nucleus_hash', api_routes.change_camera_nucleus_hash_request)
    
    # New routes for fetching data for autocomplete functionality
    app.router.add_get('/get_player_names', api_routes.get_player_names_request)
    app.router.add_get('/get_hardware_names', api_routes.get_hardware_names_request)
    app.router.add_get('/get_nucleus_hashes', api_routes.get_nucleus_hashes_request)
    
    # Health check route
    app.router.add_get('/health-check', api_routes.health_check)
    app.router.add_get('/pubsub-status', api_routes.pubsub_status_request)
    app.router.add_post('/set_camera_position', api_routes.set_camera_position_request) # Added set_camera_position route
    
    # Setup static file serving
    static_path = os.path.join(current_script_directory, 'static')
    app.router.add_static('/static/', static_path, name='static')
    
    # Setup Jinja2 templates
    # Ensure the path to templates is correct, especially when Dockerized
    templates_path = os.path.join(current_script_directory, 'templates')
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(templates_path))

    app.router.add_get('/', api_routes.index)

    return app

async def run_server():
    app = await main_app()
    web_runner = web.AppRunner(app)
    await web_runner.setup()
    # Listen on 0.0.0.0 to be accessible from outside the Docker container
    http_site = web.TCPSite(web_runner, '0.0.0.0', 8080)
    await http_site.start()
    logger.info("HTTP server started on 0.0.0.0:8080")

    # Start WebSocket server, also listen on 0.0.0.0
    ws_server = await websockets.serve(
        websocket_server.ws_handler,
        '0.0.0.0', 7777
    )
    logger.info("WebSocket server started on 0.0.0.0:7777")

    # Keep the servers running
    try:
        while True:
            await asyncio.sleep(3600) # Sleep for an hour, or use another keep-alive mechanism
    except KeyboardInterrupt:
        logger.info("Servers shutting down...")
    finally:
        ws_server.close()
        await ws_server.wait_closed()
        await web_runner.cleanup()
        logger.info("Servers stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Main application interrupted. Exiting.")

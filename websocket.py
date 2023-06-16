import asyncio
import websockets
import logging
from google.cloud import pubsub_v1
from google.protobuf import symbol_database
import os
from google.protobuf import any_pb2
from websockets.server import WebSocketServerProtocol
import events_pb2
from aiohttp import web, ClientSession
import aiohttp_jinja2
import jinja2

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('websocket_server')

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"
os.environ["DISCORD_BOT_TOKEN"] = ""
os.environ["DISCORD_CHANNEL"] = ""

# Initialize Pub/Sub
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path('', 'apexlegends')

# Set of all currently connected websockets
connected_websockets = set()

def publish_message(message):
    data = message.SerializeToString()
    #future = publisher.publish(topic_path, data=data)
    logger.info(f"Message published with ID {future.result()}")

def create_lobby():
    request = events_pb2.Request()
    request.customMatch_CreateLobby.CopyFrom(events_pb2.CustomMatch_CreateLobby())
    request.withAck = True  # Set withAck to true if you want to receive an acknowledgement

    # Create a LiveAPIEvent message
    # Publish the LiveAPIEvent message
    publish_message(request)
    logger.info("Sent request to create a custom match lobby.")

    # Send to all connected websockets
    for ws in connected_websockets:
        asyncio.create_task(ws.send(request.SerializeToString()))

def get_lobby_players():
    request = events_pb2.Request()
    request.customMatch_GetLobbyPlayers.CopyFrom(events_pb2.CustomMatch_GetLobbyPlayers())
    request.withAck = True  # Set withAck to true if you want to receive an acknowledgement

    # Create a LiveAPIEvent message
    # Publish the LiveAPIEvent message
    publish_message(request)
    logger.info(f"Pulling player info. {request}")

    # Send to all connected websockets
    for ws in connected_websockets:
        asyncio.create_task(ws.send(request.SerializeToString()))

async def get_lobby_request(request):
    get_lobby_players()
    return web.json_response({"status": "success", "message": "Request <get_lobby_request> sent."}) 

async def create_lobby_request(request):
    create_lobby()
    return web.json_response({"status": "success", "message": "Request <create_lobby_request> sent."})

async def get_lobby_token_request(request):
    get_lobby_token()
    return web.json_response({"status": "success", "message": "Request <get_lobby_token_request> sent."})

async def ws_handler(websocket, path):
    # Add the new websocket to our set
    connected_websockets.add(websocket)
    logger.info("New client connected.")
    try:
        async for message in websocket:
            # Handle incoming messages
            pblist = events_pb2.LiveAPIEvent()
            pblist.ParseFromString(message)
            result_type = pblist.gameMessage.TypeName()
            logger.info(f"Result type: {result_type}")
            msg_result = symbol_database.Default().GetSymbol(result_type)()
            pblist.gameMessage.Unpack(msg_result)
            logger.info(f"Received message from client: {msg_result}")
            publish_message(msg_result)
    except websockets.exceptions.ConnectionClosedError:
        logger.info("Client disconnected.")
    except Exception as e:
        logger.error(f"Error handling client connection: {e}")
        await websocket.close()
    finally:
        # Remove the websocket from our set when it disconnects
        connected_websockets.remove(websocket)

async def send_discord_message(channel_id: str, token: str, content: str):
    url = f"https://discord.com/api/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
    }

    data = {
        "content": content,
    }

    async with ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            if resp.status != 200:
                logger.error(f"Failed to send message to Discord: {await resp.text()}")

async def get_lobby_token():
    # Here I'm assuming that get_lobby_players will somehow obtain a lobby token and I'm using a placeholder.
    lobbytoken = get_lobby_players()
    await send_discord_message(os.getenv('DISCORD_CHANNEL'), os.getenv('DISCORD_BOT_TOKEN'), f"!store_token {lobbytoken} false")


async def main():
    app = web.Application()
    app.router.add_get('/create_lobby', create_lobby_request)
    app.router.add_get('/get_players', get_lobby_request)
    app.router.add_get('/send_discord_token', get_lobby_token_request)
    
    # Setup Jinja2
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('web'))

    # Add route for index page
    app.router.add_get('/', index)

    # Add route for static css files
    #app.router.add_static('/static/', path='/path/to/your/static/files', name='static')

    web_runner = web.AppRunner(app)
    await web_runner.setup()
    site = web.TCPSite(web_runner, 'localhost', 8080)
    await site.start()

    start_server = websockets.serve(ws_handler, 'localhost', 7777)

    logger.info("Server starting...")
    await start_server

    # Keep the server running
    while True:
        await asyncio.sleep(1)

@aiohttp_jinja2.template('index.html')
async def index(request):
    return {}

# Run the main function until it completes
asyncio.run(main())

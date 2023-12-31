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
from google.protobuf.json_format import MessageToJson # Import the MessageToJson
from google.protobuf.json_format import MessageToDict
import json


# In memory store
data_store = {}

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


def create_lobby():
    request = events_pb2.Request()
    request.customMatch_CreateLobby.CopyFrom(events_pb2.CustomMatch_CreateLobby())
    request.withAck = True  # Set withAck to true if you want to receive an acknowledgement

    # Create a LiveAPIEvent message
    # Publish the LiveAPIEvent message
    #publish_message(request)
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
    #publish_message(request)
    logger.info(f"Pulling player info. {request}")

    # Send to all connected websockets
    for ws in connected_websockets:
        asyncio.create_task(ws.send(request.SerializeToString()))


def publish_message(message):
    data = message.encode("utf-8")
    future = publisher.publish(topic_path, data=data)
    logger.info(f"Message published with ID {future.result()}")

async def get_lobby_request(request):
    response = get_lobby_players()
    # Pull lobby data from in-memory store
    await asyncio.sleep(1)
    return web.json_response(data_store.get('rtech.liveapi.CustomMatch_LobbyPlayers', {}))

async def create_lobby_request(request):
    # Create lobby and store response in memory
    response = create_lobby()
    return web.json_response(response)

async def get_lobby_token_request(request):
    # Pull lobby token from in-memory store
    response = await get_lobby_token()
    if response:
        # Requires bot to bot messages parsing in the Bot class of discord.py
        await send_discord_message(os.getenv('DISCORD_CHANNEL'), os.getenv('DISCORD_BOT_TOKEN'), f"!schedule_autostart {json.loads(response)['playerToken']} false")
        return web.json_response(json.dumps({'key' : json.loads(response)['playerToken']}))
    return web.json_response()

async def schedule_autostart_request(request):
    # Read parameters from request body
    body = await request.json()
    lobby_channel_name = body.get('lobby_channel_name')
    min_max_teams = body.get('min_max_teams')
    min_max_team_size = body.get('min_max_team_size')
    time_to_wait = body.get('time_to_wait')
    start_message = body.get('start_message')
    private_message = body.get('private_message')
    keep_autostart = body.get('keep_autostart')

    # Pull lobby token from in-memory store
    response = await get_lobby_token()
    if response:
        player_token = json.loads(response)['playerToken']
        message = f'!schedule_autostart "{lobby_channel_name}" {min_max_teams} {min_max_team_size} {time_to_wait} "{player_token}" "{private_message}" {keep_autostart}'
        await send_discord_message(os.getenv('DISCORD_CHANNEL'), os.getenv('DISCORD_BOT_TOKEN'), message)
        return web.json_response({'key': player_token})
    return web.json_response()

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
            
            # Send the packet data to the WebSocket client
            msg_dict = MessageToJson(msg_result)
            if msg_dict:  
                jsonreq = json.dumps(msg_dict)
                publish_message(jsonreq)
                # Store data to in-memory store
                await websocket.send(jsonreq)
                data_store[result_type] = msg_dict
                print(f"Writing {result_type} to data store")

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
    get_lobby_players()
    # Pull lobby data from in-memory store
    await asyncio.sleep(2)
    return data_store.get('rtech.liveapi.CustomMatch_LobbyPlayers', {})

async def main():
    app = web.Application()
    app.router.add_get('/create_lobby', create_lobby_request)
    app.router.add_get('/get_players', get_lobby_request)
    app.router.add_get('/send_discord_token', get_lobby_token_request)
    app.router.add_post('/schedule_autostart', schedule_autostart_request)
    # Setup Jinja2
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('.'))

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

# Apex Legends LiveAPI 2.0 (Bindings) Project

This Python project is a live API that uses websockets and Google's Pub/Sub messaging middleware for real-time data transmission. It has various features like creating lobbies, getting player information, sending messages to Discord, and scheduling autostarts.

## Features
* WebSocket Server: Receives and handles messages from the client-side.
* Google Pub/Sub: Publishes live API events to a specified topic.
* Discord Interactions: Sends messages to a specific Discord channel.
* REST API: Provides endpoints for managing lobby and player data.
* Asynchronous Task Management: Ensures non-blocking operations for smooth WebSocket interactions.

## Python Modules Used
* asyncio
* websockets
* google.cloud
* aiohttp
* aiohttp_jinja2
* jinja2

## Project Structure
* websocket_server.py: Handles WebSocket connections and messages.
* data_store.py: Manages in-memory storage of lobby and player data.
* api_routes.py: Contains REST API endpoints for data management and other server functionalities.
* discord_manager.py: Manages interactions with Discord.
* main.py: Initializes and runs the server, setting up WebSocket and REST API routes.
* pubsub_manager.py: Handles Google Pub/Sub messaging.
* index.html: Client-side script for interacting with the server.

## Setup

### Prerequisites
You need to install the following Python libraries, if they're not already installed.
* websockets
* google-cloud-pubsub
* aiohttp
* aiohttp_jinja2
* jinja2

You can install these libraries using pip:

    ```sh
    pip install websockets google-cloud-pubsub aiohttp aiohttp_jinja2 jinja2
    ```

### Environment Variables
You also need to set up a few environment variables:
* GOOGLE_APPLICATION_CREDENTIALS: Set this to the path of your Google Cloud Service Account JSON key file.
* DISCORD_BOT_TOKEN: Set this to your Discord bot token.
* DISCORD_CHANNEL: Set this to your Discord channel ID.

### Running the server
You can run the server script using Python 3.8 or later:

    ```sh
    python main.py
    ```

### Client-Side Interactions
Open `index.html` in your web browser. This client-side script provides a user interface to interact with the server. You can create lobbies, get player information, send Discord token, and schedule autostart.

## Usage
Once the server is running, you can interact with it from the `index.html` page. There are four buttons that can be used to send requests to the server:
* Create Lobby: Creates a new lobby.
* Get Players: Gets player information.
* Send Discord Token: Sends the Discord token.
* Schedule Autostart: Schedules autostart with the specified parameters.

### REST API Endpoints
The following endpoints are available for interacting with the server:
* `GET /create_lobby`: Creates a new lobby.
* `GET /get_players`: Retrieves the list of players in the lobby.
* `GET /get_data/{type}`: Retrieves data of the specified type from the data store.
* `GET /get_data`: Retrieves all data from the data store.
* `POST /schedule_autostart`: Schedules autostart with the specified parameters.
* `POST /change_camera`: Changes the camera to the specified point of interest or name.
* `POST /pause_toggle`: Toggles the pause state with the specified pre-timer.
* `POST /set_ready`: Sets the ready state with the specified flag.
* `POST /set_matchmaking`: Sets the matchmaking state with the specified flag.
* `POST /set_team`: Sets the team with the specified parameters.
* `POST /kick_player`: Kicks a player with the specified parameters.
* `POST /set_settings`: Sets the lobby settings with the specified parameters.
* `POST /send_chat`: Sends a chat message with the specified text.

### New Data Fetching Endpoints
* `GET /get_player_names`: Retrieves the list of player names.
* `GET /get_hardware_names`: Retrieves the list of player hardware names.
* `GET /get_nucleus_hashes`: Retrieves the list of player nucleus hashes.
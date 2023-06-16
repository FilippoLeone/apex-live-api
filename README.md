# LiveAPI 2.0 (Bindings) Project

This Python project is a live API that uses websockets and Google's Pub/Sub messaging middleware for real-time data transmission. It has various features like creating lobbies, getting player information, sending messages to Discord, and scheduling autostarts.

## Features
* WebSocket Server: Receives and handles messages from the client-side.
* Google Pub/Sub: Publishes live API events to a specified topic.
* Discord Interactions: Sends messages to a specific Discord channel.
* In-Memory Store: Stores lobby and player data in-memory for faster access.

## Python Modules Used
* asyncio
* websockets
* google.cloud
* aiohttp
* aiohttp_jinja2
* jinja2

## Project Structure
* websocket.py: This is the main server script that contains all the logic related to websockets, Pub/Sub, Discord interactions, and in-memory store.
* index.html: This is the client-side script that sends requests to the server and displays the response.

## Setup

### Prerequisites
You need to install the following Python libraries, if they're not already installed.
* websockets
* google-cloud-pubsub
* aiohttp
* aiohttp_jinja2
* jinja2

You can install these libraries using pip:

`pip install websockets google-cloud-pubsub aiohttp aiohttp_jinja2 jinja2`

### Environment Variables
You also need to set up a few environment variables:
* GOOGLE_APPLICATION_CREDENTIALS: Set this to the path of your Google Cloud Service Account JSON key file.
* DISCORD_BOT_TOKEN: Set this to your Discord bot token.
* DISCORD_CHANNEL: Set this to your Discord channel ID.

### Running the server
You can run the server script using Python 3.8 or later:
`python websocket.py`

### Client-Side Interactions
Open `index.html` in your web browser. This client-side script provides a user interface to interact with the server. You can create lobbies, get player information, send Discord token, and schedule autostart.

## Usage
Once the server is running, you can interact with it from the `index.html` page. There are four buttons that can be used to send requests to the server:
* Create Lobby: Creates a new lobby.
* Get Players: Gets player information.
* Send Discord Token: Sends the Discord token.
* Schedule Autostart: Schedules autostart with the specified parameters.

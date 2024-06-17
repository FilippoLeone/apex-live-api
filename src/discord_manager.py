# discord_manager.py
from aiohttp import ClientSession
import logging
import config

logger = logging.getLogger('websocket_server')

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
            else:
                logger.info(f"Message sent to Discord channel {channel_id}")

async def schedule_autostart(lobby_channel_name, min_max_teams, min_max_team_size, time_to_wait, start_message, private_message, keep_autostart, player_token):
    message = f'!schedule_autostart "{lobby_channel_name}" {min_max_teams} {min_max_team_size} {time_to_wait} "{player_token}" "{private_message}" {keep_autostart}'
    await send_discord_message(config.DISCORD_CHANNEL, config.DISCORD_BOT_TOKEN, message)

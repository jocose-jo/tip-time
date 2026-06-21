import asyncio
import os
from aiohttp import web

from env import DISCORD_TOKEN, MODE
import bot_commands

"""
Tip-time discord bot. Powered by Pycord, MongoDB
Authors: Joseph Gutierrez, Angelo Jay Delacruz
"""

async def health_check(request):
    return web.Response(text="OK")

async def start_http_server():
    app = web.Application()
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv('PORT', 8000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"HTTP server started on port {port}")

def setup_client():
    client = bot_commands.init_client()
    bot_commands.add_bot_commands(client)
    return client

async def main():
    client = setup_client()
    await start_http_server()
    await client.start(DISCORD_TOKEN)

if __name__ == "__main__":
    if MODE == 'development':
        client = setup_client()
        client.run(DISCORD_TOKEN)
    else:
        asyncio.run(main())

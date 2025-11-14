#!/usr/bin/env python3
import asyncio
import aiohttp
import json
from config import settings

async def get_health():
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{settings.claude_base_url}/health') as resp:
            data = await resp.json()
            print(json.dumps(data, indent=2))

if __name__ == "__main__":
    asyncio.run(get_health())

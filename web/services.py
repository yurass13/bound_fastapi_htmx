import os
from asyncio import sleep

import redis.asyncio as redis

client = redis.from_url(os.environ.get('REDIS_URL', "redis://redis:6379/0"))


async def emit_file_status_changed(file_id: str) -> None:
    await client.publish(channel='file_status_changed', message=file_id)


async def subscribe_file_status_changed() -> str:
    async with client.pubsub() as pubsub:
        await pubsub.subscribe('file_status_changed')

        while True:
            # NOTE message is not None
            if message := await pubsub.get_message(ignore_subscribe_messages=True):
                return message
            else:
                await sleep(1)

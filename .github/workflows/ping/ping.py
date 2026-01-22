from os import environ
from websockets import connect
from asyncio import run, wait_for

async def main():
    async with connect(environ["URL"]) as websocket: await wait_for(websocket.ping(), 10)

run(main())
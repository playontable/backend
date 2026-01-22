from websockets import connect
from asyncio import run, wait_for

async def main():
    async with connect("wss://api.playontable.com/websocket/") as websocket: wait_for(await websocket.ping(), 10)

run(main())
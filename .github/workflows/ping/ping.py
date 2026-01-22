from asyncio import run
from websockets import connect

async def main():
    async with connect("wss://api.playontable.com/websocket/") as websocket: await websocket.ping()

run(main())
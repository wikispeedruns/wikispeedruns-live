import asyncio
import json

from websockets.server import serve
from websockets import broadcast

lobbies = {}

async def sub_to_lobby(websocket):
    message = await websocket.recv()
    message = json.loads(message)
    lobby = message["lobby_id"]
    prompt = message["prompt_id"]

    key = (lobby, prompt)
    if key not in lobbies:
        lobbies[key] = set()


    print(key)
    print(lobbies[key])
    # Notify other people waiting for lobby leaderboard of new entry
    if len(lobbies[key]) > 0:
        broadcast(lobbies[key], "Refresh lobby!")

    try:
        lobbies[key].add(websocket)

        await websocket.send(f"Subscribed to {lobby}/{prompt}")
        await websocket.wait_closed()
        
    finally:
        lobbies[key].remove(websocket)

async def main():
    async with serve(sub_to_lobby, "localhost", 9000):
        await asyncio.Future()  # run forever

asyncio.run(main())
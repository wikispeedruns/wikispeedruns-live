import asyncio
import json

from websockets.server import serve
from websockets import broadcast


# Data structure for lobbys, keyed by (lobby_id, prompt_id)
prompts = {}

# Data structure for leaderboard subscriptions, keyed by (lobby_id, prompt_id)
leaderboards = {}


async def wait_for_start(ws, lobby_id, prompt_id, user):
    key = (lobby_id, prompt_id)

    if key not in prompts:
        prompts[key] = {
            "usersReady": {},
            "connections": set()
        } # TODO don't use a dict here lol

    # Dumb hack to handle multiple users with the same username,
    # just change their username to "also user" for the user list
    # Will just keep on appending "also" # TODO maybe something better
    while user in prompts[key]["usersReady"]:
        # Rename to 
        user = "also " + user

    prompts[key]["connections"].add(ws)
    prompts[key]["usersReady"][user] = False # ready status

    broadcast(prompts[key]["connections"], json.dumps(prompts[key]["usersReady"])) 

    try:
        while True:
            msg = ws.recv()
            msg = json.loads(msg)
            prompts[key]["usersReady"][user] = msg["ready"]

            if all(prompts[key]["usersReady"].values()):
                broadcast(prompts[key]["connections"], "start") 
            else:
                broadcast(prompts[key]["connections"], json.dumps(prompts[key]["usersReady"])) 
            
    finally:
        prompts[key]["connections"].remove(ws)
        del prompts[key]["usersReady"][user]

        if len(prompts[key]["connections"]) == 0:
            del prompts[key]
    
    

async def sub_to_leaderboard(ws, lobby_id, prompt_id):
    key = (lobby_id, prompt_id)
    if key not in leaderboards:
        leaderboards[key] = set()


    leaderboards[key].add(ws)

    # print(f"{len(leaderboards[key])} subbed to Lobby #{lobby_id} Prompt #{prompt_id}")

    try:
        # await websocket.send(f"ack {lobby_id}/{prompt_id}")
        await ws.wait_closed()

    finally:
        leaderboards[key].remove(ws)
        if len(leaderboards[key]) == 0:
            del leaderboards[key]


async def update_leaderboard(ws, lobby_id, prompt_id):
    key = (lobby_id, prompt_id)

    # print(f"Update for Lobby #{lobby_id} Prompt #{prompt_id}")

    if key in leaderboards and len(leaderboards[key]) > 0:
        broadcast(leaderboards[key], "refresh")
    
    return await ws.close()


async def connect(websocket):
    message = await websocket.recv()
    message = json.loads(message)

    # TODO exceptions?
    msgType = message["type"]
    lobby = message["lobby_id"]
    prompt = message["prompt_id"]

    if msgType == "play":
        user = message["user"]
        await wait_for_start(websocket, lobby, prompt, user)
    elif msgType == "leaderboard":
        await sub_to_leaderboard(websocket, lobby, prompt)
    elif msgType == "update":
        await update_leaderboard(websocket, lobby, prompt)
    else:
        print("Invalid Message type: '{msgType}'")
        await websocket.close(reason="invalid message type")


async def main():
    async with serve(connect, "localhost", 8000):
        await asyncio.Future()  # run forever

asyncio.run(main())
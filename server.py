import asyncio
import json

from websockets.server import serve
from websockets import broadcast


# Data structure for lobby starts, keyed by (lobby_id, prompt_id)
prompts = {}

# Data structure for leaderboard subscriptions, keyed by (lobby_id, prompt_id)
leaderboards = {}


async def wait_for_start(ws, lobby_id, prompt_id, user):
    key = (lobby_id, prompt_id)

    print(f"{user} waiting to start for Lobby #{lobby_id} Prompt #{prompt_id}")

    if key not in prompts:
        prompts[key] = {
            "users": set(),
            "connections": set()
        } # TODO don't use a dict here lol

    # Dumb hack to handle multiple users with the same username,
    # just change their username to "also user" for the user list
    # Will just keep on prepending "also" # TODO maybe something better
    # Note if we don't do this we could accidentally delete users twice
    while user in prompts[key]["users"]:
        user = "also " + user

    prompts[key]["connections"].add(ws)
    prompts[key]["users"].add(user) # ready status

    broadcast(prompts[key]["connections"], json.dumps({
        "type": "update",
        "users": list(prompts[key]["users"])
    }))

    try:
        while True:
            msg = await ws.recv()
            msg = json.loads(msg)

            # TODO enforce that this only happens for host
            if (msg["type"] == "start"):
                broadcast(prompts[key]["connections"], json.dumps({"type": "start"})) 
            
    finally:
        prompts[key]["connections"].remove(ws)
        prompts[key]["users"].remove(user)

        if len(prompts[key]["connections"]) == 0:
            del prompts[key]

        else: 
            # If there are still players in the lobby, update list of players
            broadcast(prompts[key]["connections"], json.dumps({
                "type": "update",
                "users": list(prompts[key]["users"])
            }))
    

    

async def sub_to_leaderboard(ws, lobby_id, prompt_id):
    key = (lobby_id, prompt_id)
    if key not in leaderboards:
        leaderboards[key] = set()


    leaderboards[key].add(ws)

    print(f"{len(leaderboards[key])} subbed to Lobby #{lobby_id} Prompt #{prompt_id}")

    try:
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

    print(message)
    # TODO exceptions?
    msgType = message["type"]
    lobby = message["lobby_id"]
    prompt = message["prompt_id"]

    if msgType == "wait_start":
        user = message["user"]
        await wait_for_start(websocket, lobby, prompt, user)
    elif msgType == "leaderboard":
        await sub_to_leaderboard(websocket, lobby, prompt)
    elif msgType == "update":
        await update_leaderboard(websocket, lobby, prompt)
    else:
        print(f"Invalid Message type: '{msgType}'")
        await websocket.close(reason="invalid message type")


async def main():
    async with serve(connect, "localhost", 8000):
        await asyncio.Future()  # run forever

asyncio.run(main())
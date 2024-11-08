import asyncio
import json

import websockets
from websockets.server import serve
from websockets import broadcast


# Data structure for lobby pormpts, keyed by lobby_id
lobbys = {}

# Data structure for lobby starts, keyed by (lobby_id, prompt_id)
prompt_starts = {}

# Data structure for leaderboard subscriptions, keyed by (lobby_id, prompt_id)
leaderboards = {}


async def wait_for_start(ws, lobby_id, prompt_id, user):
    key = (lobby_id, prompt_id)

    print(f"{user} waiting to start for Lobby #{lobby_id} Prompt #{prompt_id}")

    if key not in prompt_starts:
        prompt_starts[key] = {
            "users": set(),
            "connections": set()
        } # TODO don't use a dict here lol

    # Dumb hack to handle multiple users with the same username,
    # just change their username to "also user" for the user list
    # Will just keep on prepending "also" # TODO maybe something better
    # Note if we don't do this we could accidentally delete users twice
    while user in prompt_starts[key]["users"]:
        user = "also " + user

    prompt_starts[key]["connections"].add(ws)
    prompt_starts[key]["users"].add(user) # ready status

    broadcast(prompt_starts[key]["connections"], json.dumps({
        "type": "update",
        "users": list(prompt_starts[key]["users"])
    }))

    try:
        while True:
            msg = await ws.recv()
            msg = json.loads(msg)

            # TODO enforce that this only happens for host
            if (msg["type"] == "start"):
                broadcast(prompt_starts[key]["connections"], json.dumps({"type": "start"})) 
            
    finally:
        prompt_starts[key]["connections"].remove(ws)
        prompt_starts[key]["users"].remove(user)

        if len(prompt_starts[key]["connections"]) == 0:
            del prompt_starts[key]

        else: 
            # If there are still players in the lobby, update list of players
            broadcast(prompt_starts[key]["connections"], json.dumps({
                "type": "update",
                "users": list(prompt_starts[key]["users"])
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


async def sub_to_lobby_prompts(ws, lobby_id):
    key = lobby_id
    if key not in lobbys:
        lobbys[key] = set()

    lobbys[key].add(ws)

    try:
        while True:
            msg = await ws.recv()
            msg = json.loads(msg)
            print(msg)
            if (msg["type"] == "lobby_prompts_update"):
                # print("Triggering lobby ")
                broadcast(lobbys[key], "refresh") 
    finally:
        lobbys[key].remove(ws)
        if len(lobbys[key]) == 0:
            del lobbys[key]


async def connect(websocket):
    message = await websocket.recv()
    message = json.loads(message)

    print(message)
    # TODO exceptions?
    msgType = message["type"]
    lobby = message["lobby_id"]

    try:
        if msgType == "wait_start":
            user = message["user"]
            prompt = message["prompt_id"]
            await wait_for_start(websocket, lobby, prompt, user)

        elif msgType == "leaderboard":
            prompt = message["prompt_id"]
            await sub_to_leaderboard(websocket, lobby, prompt)

        elif msgType == "leaderboard_update":
            prompt = message["prompt_id"]
            await update_leaderboard(websocket, lobby, prompt)

        elif msgType == "lobby_prompts":
            await sub_to_lobby_prompts(websocket, lobby)

        else:
            print(f"Invalid message type: '{msgType}'")
            await websocket.close(reason="invalid message type")
    
    except websockets.exceptions.WebSocketException as e:
        print(f"Websocket error: '{e}'")
 


async def main():
    async with serve(connect, "localhost", 8000):
        await asyncio.Future()  # run forever

asyncio.run(main())
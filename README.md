# Live Service for Wikipedia Speedruns

A basic websocket server for supporting live (-ish) game modes on
wikispeedruns.com. This server implemented in this repo is mostly
a proof of concept. We use the webserver to signal events to clients
about other clients, such as players finishing a prompt or being
ready to start. Retrieving data, recording paths/time, and other
functionality is still done by the main server. Essentially, the
main game is still asynchronous, this server just allows us to see
updates.

## Documentation of features

Following are some of the live featrues we support, and how we support
them.

### 1. Lobby Prompt Start

Client intially sends a message upon getting ready to play the prompt
```
{
    "type": "wait_start",
    "user": "dan",
    "lobby_id": 10,
    "prompt_id": 5,
}
```

If this is the first client, the server creates an entry for this lobby prompt,
which includes an array indicating which users are waiting.

The host can then send a message of the form
```
{
    "type": "start", 
}
```
to indicate whether they are ready to start the prompt. The server broadcasts this 
message to other clients so they can start the prompt.


### 2. Leaderboard Updating

When a client views the leaderboard, it establishes a connection to
the server
```
{
    "type": "leaderboard"
    "lobby_id": 10,
    "prompt_id": 5, 
}
```

The server keeps track of which users are connected to the server, and when
a client updates their run, it sends a signal to the server which updates
each other client subscribed to the leaderboard, which causes them to refresh
the leaderboard.

```
{
    "type": "leaderboard_update"
    "lobby_id": 10,
    "prompt_id": 5, 
}
```

### 3. Lobby Prompt Updating

Similar to above, if the host adds a prompt, we want to update users to refresh
their page. This is accomplished with 2 messages.

```
{
    "type": "lobby_prompts"
    "lobby_id": 10,
}
```

to establish a connection, and on the same connection

{
    "type": "lobby_prompts_update"
}

to force an update to other clients.

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
    "type": "play",
    "user": "dan",
    "lobby_id": 10,
    "prompt_id": 5,
}
```

If this is the first client, the server creates an entry for this lobby prompt,
which includes an array indicating which users are ready and which can force 
the game to start. It returns a list of players. TODO, currently, any user can
start the game

Clients can send messages of the form
```
{
    "ready": true, // or false
}
```
to indicate whether they are ready to start the prompt. If all clients indicate they 
are ready, then the prompt starts. The server broadcasts this message to other clients
in the lobby so they can update the list of who isn't ready.


### 2. Lobby Prompt Leaderboard Finishing

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
a client finishes a prompt, it sends a signal to the server which updates
each other client subscribed to the leaderboard, which causes them to refresh
the leaderboard.

TODO: show partial prompts too! And refresh on click instead.

```
{
    "type": "update"
    "lobby_id": 10,
    "prompt_id": 5, 
}
```
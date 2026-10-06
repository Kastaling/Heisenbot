# Heisenbot

Heisenbot is a self-hosted Discord bot that learns from server messages, retrieves relevant memories with ChromaDB, and generates replies through a local [Ollama](https://ollama.com/) model. It can also index images and short videos with a vision-capable model, search the web for time-sensitive questions, generate memes, and expose per-server channel controls.

The current code replaces the repository's original Markov-chain prototype. Runtime data is kept outside the image and is never intended to be committed.

## How it works

1. Every message in every non-NSFW guild channel or thread visible to the bot is consumed by default. NSFW channels are never learned from, and administrators can explicitly disable listening in any additional channel.
2. Text is upserted into a guild-specific ChromaDB collection. Media is downloaded with size, type, redirect, and public-network checks, then stored by content hash.
3. When the bot is mentioned, replied to, or selected by the configured random reply chance, it retrieves related server memories and recent channel history.
4. Ollama generates the response. Optional search and verification steps can add current public information.

Each guild has separate message and media collections. SQLite stores operational and word-count statistics.

## Requirements

- Docker Engine with Compose
- A Discord application/bot token
- An accessible Ollama server and installed model
- Discord's **Message Content Intent** and **Server Members Intent** enabled for the bot
- Optional NVIDIA Container Toolkit if Ollama or bot-side GPU inspection uses NVIDIA hardware

## Quick start

```bash
cp .env.example .env
# Edit .env with DISCORD_TOKEN, OWNER_ID, OLLAMA_HOST, and model names.
mkdir -p database media logs cache
docker compose -f compose.example.yaml up -d --build
docker compose -f compose.example.yaml logs -f heisenbot
```

The example assumes Ollama is reachable at `http://ollama:11434`. Put both services on the same Docker network, or set `OLLAMA_HOST` to a reachable host address.

Never commit `.env`. If a token has ever been committed or printed publicly, rotate it in the Discord Developer Portal.

## Configuration

See [.env.example](.env.example) for every common setting. Useful behavior controls include:

| Variable | Default | Purpose |
| --- | --- | --- |
| `COMMAND_PREFIX` | `..` | Prefix for text commands |
| `RANDOM_REPLY_CHANCE` | `0.33` | Chance of replying without a mention; `0` disables random replies |
| `VISION_ENABLED` | `true` | Enables image/video descriptions |
| `AUTO_SEARCH_ENABLED` | `true` | Lets the model request web search |
| `LOG_MESSAGE_CONTENT` | `false` | Opt-in message previews in logs; leave off for privacy |
| `CONNECT4_SEARCH_DEPTH` | `5` | Connect Four look-ahead depth (`1`–`7`) |
| `CONNECT4_TIMEOUT_SECONDS` | `1800` | Inactive Connect Four game expiry (`60`–`86400`) |
| `SYSTEM_PROMPT` | built in | Inline personality override |
| `SYSTEM_PROMPT_FILE` | unset | UTF-8 file that replaces the built-in personality prompt |

Invalid numeric or boolean values fail fast at startup instead of silently choosing unsafe behavior.

## Data and privacy

By default, Heisenbot consumes content from every non-NSFW guild channel and thread it can see. NSFW channels are excluded from RAG ingestion, media downloads, and statistics. Automatic replies and reactions are attempted only where both Heisenbot's `respond` policy and Discord's effective channel permissions allow them. A direct bot command bypasses the random/mention reply decision, but it still requires the `commands` policy and Discord's send permission. Discord permissions can never be bypassed.

Server administrators should explicitly disable learning anywhere messages should not be retained:

```text
..channel deny #private-channel listen
..channel deny #quiet-channel respond
..channel deny #no-bots all
..channels
```

Heisenbot stores message text, Discord user IDs/display names, channel metadata, media, media descriptions, and aggregate statistics. Operators are responsible for member notice/consent, retention rules, backups, and deletion requests. The `database/`, `media/`, `logs/`, and `cache/` directories are ignored by both Git and Docker builds.

## Commands

- `..ping`, `..invite`
- `..context` — last assembled prompt context (owner only)
- `..stats [30m|12h|7d]` — current-server stats for managers; global totals for the owner
- `..leaderboard [timespan]` — cross-server leaderboard (owner only)
- `..wordstats [@member]`, `..wordleaderboard [word]`
- `..channel allow|deny|reset`, `..channels`
- `..tictactoe`, `..connect4 [botfirst]`, `..getcaptioned`, `..poster`, `..rage`
- `..gpu` — owner-only NVIDIA status

Use Discord channel permissions as the primary access boundary. Heisenbot now skips reply generation when it lacks `Send Messages`, avoiding expensive work followed by a Discord 403.

## Development

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
ruff check .
ruff format --check .
pytest
```

CI runs linting, formatting, tests, and compilation on every pull request. Dependabot checks Python and GitHub Actions dependencies weekly.

## Updating an existing deployment

Back up `database/` and `media/`, pull the code, then rebuild the bot service. The update is backward-compatible with existing ChromaDB, SQLite, permissions, and media directories. New media filenames are content-addressed to prevent duplicate storage; existing files remain readable.

```bash
docker compose build --pull heisenbot
docker compose up -d heisenbot
docker compose logs --tail=100 heisenbot
```

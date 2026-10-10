# Heisenbot repository guide for coding agents

This file is tool-neutral project guidance. Read it before changing code, then follow the user's request and the actual current code. It lives at the repository root so an assistant opened in this project can find it. Do not treat it as a replacement for a tool's own instruction mechanism or for human review.

## What this repository is

Heisenbot is a Python 3.12–3.14 Discord bot deployed in Docker. Its current implementation consumes eligible guild messages, stores text in guild-scoped ChromaDB collections for RAG, stores media on disk, tracks operational statistics in SQLite, and uses a local Ollama server for chat and some game commentary. `main.py` is the application entry point and Discord integration layer; `heisenbot/` contains testable helpers. The original Markov-chain prototype and removed Secret Santa feature are historical, not the architecture to restore.

The deployed Ollama model and host are environment/deployment choices, not code constants. Do not reintroduce a required custom `heisenbot:latest` model or put personality only in an Ollama Modelfile: the user also uses stock models in Open WebUI. The app's personality can be configured with `SYSTEM_PROMPT` or `SYSTEM_PROMPT_FILE`, while the output/security contract in `heisenbot/prompts.py` must still apply.

## Source map

| Area | Source of truth |
| --- | --- |
| Discord events, commands, policies, Ollama/RAG/media orchestration, SQLite, interactive views | `main.py` |
| Prompt composition, JSON data envelope, response cleanup/leak checks | `heisenbot/prompts.py` |
| URL/filename validation and SSRF boundary | `heisenbot/security.py` |
| Pure Connect Four search/rules, tic-tac-toe helpers, chess rules/Stockfish wrapper | `heisenbot/connect4.py`, `heisenbot/tictactoe.py`, `heisenbot/chess_game.py` |
| Media size/count presentation and Discord batching; duration parsing | `heisenbot/stats.py`, `heisenbot/timeutils.py` |
| Validated environment parsing | `heisenbot/config.py` |
| Configuration/deployment examples | `.env.example`, `compose.example.yaml`, `Dockerfile`, `README.md`, `SECURITY.md` |
| Tests and CI | `tests/`, `pyproject.toml`, `.github/workflows/ci.yaml` |

Prefer moving self-contained new rules/formatting into `heisenbot/` with focused tests instead of growing `main.py` further. Keep Discord I/O and orchestration in `main.py`. Preserve the established APIs and persisted data unless a migration is explicitly planned.

## Non-negotiable behavior and privacy boundaries

- `on_message` handles explicit prefixed commands first, subject to the per-channel `commands` policy and Discord's effective permissions. Ordinary non-command messages in NSFW channels or NSFW threads must **never** be learned from: no RAG insertion, media download/description, tracked-word counting, message statistics, reaction, or automatic reply. Keep the NSFW check before all ordinary ingestion. Explicit commands may still run there under the command policy; they must not turn the surrounding channel into training data.
- For other visible guild channels and threads, `listen`, `respond`, and `commands` default to `true`; administrators can deny each via `..channel`. Threads inherit the parent channel's policy. Do not silently narrow the default listening scope, broaden an opt-out, or confuse `respond` with `listen`. Discord channel/role permissions remain authoritative for outbound sends. The default random-reply chance is configurable, so “respond allowed” does not mean “reply to every message.”
- Keep guild RAG and media separated by guild ID. Never mix private server content across guilds or expose cross-server stats to non-owners. `..stats` is for server managers/owner; `..leaderboard` and raw `..context` are owner-only. Do not log raw message content by default (`LOG_MESSAGE_CONTENT=false`).
- Treat message text, display names, filenames, URLs, RAG memories, web results, and LLM output as untrusted. Keep them as data in the JSON prompt envelope, not instruction text. Preserve the non-overridable output/security contract, first-person Heisenbot voice, response cleanup, and prompt-leak/third-person checks. A model failure should not reveal a prompt or block the event loop.
- For media downloads, preserve public HTTP(S) validation, validation of **each** redirect with redirects disabled in the client, bounded streaming/size, safe filenames/extensions, and content-addressed files. Do not follow arbitrary URLs or expose the local network. The in-process Chroma `PersistentClient` must not be replaced with a public Chroma HTTP service by accident.
- Statistics distinguish `reply_sent` from `reply_failed`. Count only successful sends in “Last Message Sent.” Message/reply time filters do not time-filter “media on disk” or the all-time last-send timestamp; label these scopes honestly. Keep Discord embed/message size limits in mind.
- Interactive games must validate player identity and legal moves server-side, acknowledge component interactions without accumulating “thinking” messages, guard rapid clicks/races, and expire or end cleanly. Tic-tac-toe uses Ollama for moves with legal fallback; Connect Four uses local search; chess uses `python-chess` and packaged Stockfish for moves. Chess calls Ollama only for notable-event/end commentary, never for move legality or selection. Games live in memory and end on restart.

## Working safely in this checkout

1. Check `git status` before editing; preserve unrelated changes. Use `rg`/`rg --files` to locate code. Review nearby tests and relevant commit history when changing behavior, especially the hardening commits after the Docker modernization. History explains intent but current code and tests determine present behavior.
2. Make the smallest coherent change. Keep blocking Ollama, Stockfish, database, scanning, and CPU-heavy work off the Discord event loop (`asyncio.to_thread`/the existing semaphore pattern). Bound work and concurrency. Do not make network or LLM calls in unit tests.
3. Add or update focused tests for new parsing, rules, permissions, security boundaries, formatting, and failure paths. When touching `on_message` or commands, explicitly check NSFW, policy, Discord permission, cross-guild, owner/admin, and duplicate-interaction effects where applicable.
4. Run the checks below. If a check cannot run, report exactly why. Review the diff for secrets, persisted-data changes, user-visible strings, and accidental generated files before handing off.
5. Do not start, restart, rebuild, deploy, delete data/models, or push to a remote merely because a code edit was requested. Do those operational steps only when the user requests them or clearly includes them in the task; warn that restarting ends in-memory games. Never run tests against production Discord credentials or real user data.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
ruff check .
ruff format --check .
pytest -q
python -m py_compile main.py heisenbot/*.py
pip-audit -r requirements.txt \
  --ignore-vuln PYSEC-2026-311 \
  --ignore-vuln PYSEC-2026-3813 \
  --ignore-vuln PYSEC-2026-3814 \
  --ignore-vuln PYSEC-2026-3815
```

CI runs these checks with specific, documented Chroma advisory exclusions in `.github/workflows/ci.yaml` and `SECURITY.md`; do not add or retain exclusions without checking whether the vulnerable surface is reachable and whether a fixed version exists. Runtime dependencies are exact-pinned in `requirements.txt`; update pins deliberately and test the built image when changing them. If using `uv` for local checks, avoid committing a generated `uv.lock` unless the project intentionally adopts it.

## Deployment and data

`compose.example.yaml` is an example, not proof of the active deployment's settings. The production Compose file may live in the parent Docker workspace and configure different Ollama models, GPU access, and mounts. Read the actual deployment file before a requested rollout; never copy secrets from it into this repository. The container is intended to run as a non-root user with a read-only root filesystem, `no-new-privileges`, writable mounted `database/`, `media/`, `logs/`, `cache/`, and a private network. Docker installs Stockfish for chess; Ollama is a separate service.

`.env`, databases, Chroma collections, member media, caches, and logs are sensitive runtime data and are excluded from Git and the image build context. Do not delete, rewrite, migrate, or publish them without explicit scope, a backup/rollback plan, and a verified target. Keep tokens out of code, tests, commits, shell output, and issue reports. See `SECURITY.md` for vulnerability reporting and deployment boundaries.

## Historical context worth preserving

- `2b49c56` replaced the old prototype with the Docker/RAG implementation and added CI and security boundaries.
- `e734392` and `07c3319` clarified listening versus replying and redacted signed media URLs from logs.
- `69a00f3` and `2ef9e97` fixed game interactions/player identity and audited commands.
- `a7801d6`, `71b193e`, and `528b8f3` added local-search Connect Four, Stockfish chess, and selective chess commentary.
- `931b14a` and `4a70d42` established media-on-disk sizing and last-successful-send semantics for stats.
- `5d66b72` hardened prompts against leaks and third-person self-reference.

These hashes are navigation aids, not a request to preserve every old implementation detail. Recheck this guide when architecture, privacy policy, dependencies, or deployment changes; stale agent instructions are worse than a shorter accurate guide.

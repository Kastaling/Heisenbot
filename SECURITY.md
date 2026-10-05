# Security

Please report suspected vulnerabilities privately through GitHub's security-advisory feature rather than a public issue. Do not include bot tokens, message data, database copies, or member media in a report.

## Deployment boundary

Heisenbot uses ChromaDB only through its in-process `PersistentClient`. It does not start or expose a Chroma HTTP server. Keep the bot container, its persistent volumes, and Ollama on a private network; publish no Chroma or Ollama port to the internet.

Dependency auditing currently suppresses `PYSEC-2026-311`, `PYSEC-2026-3813`, `PYSEC-2026-3814`, and `PYSEC-2026-3815`. Those advisories concern Chroma's HTTP API, remote model configuration, or multi-tenant server authorization and have no upstream fixed release at the time of this update. They are not reachable in Heisenbot's embedded-only design. The suppressions should be removed when Chroma publishes a fixed release.

## Operator checklist

- Keep `.env`, databases, media, caches, and logs out of source control and image build contexts.
- Run the supplied container as its non-root user with `no-new-privileges` and a read-only root filesystem.
- Rotate a Discord token immediately if it may have been exposed.
- Leave `LOG_MESSAGE_CONTENT=false` unless message-content logging is explicitly required and disclosed.
- Back up and protect `database/` and `media/`; both may contain personal server data.
- Use `..channel deny <channel> listen` for channels that must not be retained.

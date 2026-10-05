"""Network and filesystem boundary validation."""

from __future__ import annotations

import asyncio
import ipaddress
import re
import socket
from pathlib import Path
from urllib.parse import urlsplit

_SAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(filename: str, *, fallback: str = "upload") -> str:
    """Return a portable basename suitable for a server-controlled directory."""
    name = Path((filename or "").replace("\\", "/")).name
    name = _SAFE_FILENAME_CHARS.sub("_", name).strip("._")
    if not name:
        name = fallback
    stem = Path(name).stem.strip("._")[:96]
    suffix = Path(name).suffix[:16].lower()
    return f"{stem or fallback}{suffix}"


def is_public_ip(value: str) -> bool:
    """Reject loopback, private, link-local, reserved, and unspecified addresses."""
    try:
        return ipaddress.ip_address(value).is_global
    except ValueError:
        return False


async def validate_public_http_url(url: str) -> bool:
    """Allow only HTTP(S) URLs whose current DNS answers are all public.

    Redirects must be disabled by callers and each redirect target revalidated.
    """
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False
        if parsed.username is not None or parsed.password is not None:
            return False
        if parsed.port not in {None, 80, 443}:
            return False
        host = parsed.hostname.rstrip(".")
        if host.lower() == "localhost":
            return False
        if is_public_ip(host):
            return True
        try:
            ipaddress.ip_address(host)
            return False
        except ValueError:
            pass

        loop = asyncio.get_running_loop()
        infos = await loop.getaddrinfo(
            host,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
        addresses = {info[4][0] for info in infos}
        return bool(addresses) and all(is_public_ip(address) for address in addresses)
    except (OSError, UnicodeError, ValueError):
        return False

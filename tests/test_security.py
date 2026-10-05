import socket

import pytest

from heisenbot.security import sanitize_filename, validate_public_http_url


def test_sanitize_filename_removes_paths_and_unsafe_characters():
    assert sanitize_filename("../../weird file?.PNG") == "weird_file.png"
    assert sanitize_filename("..") == "upload"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "http://localhost/secret",
        "http://127.0.0.1/admin",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/",
        "https://user:password@example.com/file.png",
        "https://example.com:8443/file.png",
    ],
)
async def test_private_or_unsafe_urls_are_rejected(url):
    assert await validate_public_http_url(url) is False


@pytest.mark.asyncio
async def test_public_dns_result_is_allowed(monkeypatch):
    loop = __import__("asyncio").get_running_loop()

    async def fake_getaddrinfo(*args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]

    monkeypatch.setattr(loop, "getaddrinfo", fake_getaddrinfo)
    assert await validate_public_http_url("https://example.com/image.png") is True

FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-liberation stockfish \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 heisenbot \
    && useradd --uid 1000 --gid heisenbot --create-home --shell /usr/sbin/nologin heisenbot

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --requirement requirements.txt

COPY --chown=heisenbot:heisenbot main.py ./
COPY --chown=heisenbot:heisenbot heisenbot/ ./heisenbot/
RUN mkdir -p database/chroma media logs /home/heisenbot/.cache \
    && chown -R heisenbot:heisenbot /app /home/heisenbot

USER heisenbot

CMD ["python", "-u", "main.py"]

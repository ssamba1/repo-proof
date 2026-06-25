"""Detect when a repo's quickstart needs external services we will not provision.

R4 in the plan: a quickstart that needs a database, message queue, or other backing
service cannot be honestly "verified" in an isolated sandbox — running it would fail on a
connection error and we would have to report that as a problem with the repo, which it is
not. So we detect the strong, low-false-positive signals up front and skip with a clear
report (SPEC open-Q2's recommended answer) rather than run-then-misclassify.

Signals are deliberately conservative — a SQLite dependency or an optional Redis client is
*not* enough, because plenty of CLIs ship those without needing a running server. We key on:
  * a Docker Compose stack (its whole purpose is to stand up backing services), and
  * an env-template file that declares a service URL the quickstart would read.
"""

from __future__ import annotations

import re
from pathlib import Path

_COMPOSE_FILES = (
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
)

_ENV_TEMPLATES = (
    ".env.example",
    ".env.sample",
    ".env.template",
    ".env.dist",
    "env.example",
)

# Env vars that name a backing service the quickstart would need a live host for.
_SERVICE_ENV = re.compile(
    r"^\s*(?:export\s+)?("
    r"DATABASE_URL|DB_(?:HOST|URL|PORT)|"
    r"POSTGRES_(?:HOST|URL|PORT|DB)|PG(?:HOST|PORT|DATABASE)|"
    r"MYSQL_(?:HOST|URL|PORT)|"
    r"REDIS_URL|REDIS_HOST|"
    r"MONGO(?:DB)?_(?:URL|URI|HOST)|MONGO_URL|"
    r"AMQP_URL|RABBITMQ_(?:URL|HOST)|"
    r"KAFKA_(?:BROKERS?|URL|HOST)|"
    r"ELASTICSEARCH_(?:URL|HOST)|ELASTIC_(?:URL|HOST)"
    r")\b",
    re.IGNORECASE | re.MULTILINE,
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def detect_services(repo: Path) -> str | None:
    """Return a one-line reason if the repo declares external services, else None."""
    repo = Path(repo)

    for name in _COMPOSE_FILES:
        if (repo / name).is_file():
            return f"declares a Docker Compose stack ({name}) — the quickstart likely needs it"

    for name in _ENV_TEMPLATES:
        path = repo / name
        if not path.is_file():
            continue
        found = sorted({m.group(1).upper() for m in _SERVICE_ENV.finditer(_read(path))})
        if found:
            shown = ", ".join(found[:4])
            return f"requires backing-service configuration ({name}: {shown})"

    return None

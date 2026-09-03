"""Logs d'activite du bot, persistes en fichier texte."""

import threading
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
LOG_PATH = DATA_DIR / "bot.log"

_lock = threading.Lock()


def append_log(message: str) -> None:
    with _lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")


def get_recent_logs(limit: int = 100) -> list[str]:
    if not LOG_PATH.exists():
        return []
    lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
    return list(reversed(lines))[:limit]


def count_packs_opened() -> int:
    return sum(1 for line in get_recent_logs(limit=10_000) if "Paquet ouvert" in line)

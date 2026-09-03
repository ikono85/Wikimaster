"""Historique des ouvertures de paquets, persiste en JSON."""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
HISTORY_PATH = DATA_DIR / "history.json"

_lock = threading.Lock()


def _read_all() -> list[dict]:
    if not HISTORY_PATH.exists():
        return []
    return json.loads(HISTORY_PATH.read_text())


def append_drop(card_title: str, rarity: str | None = None) -> None:
    with _lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        entries = _read_all()
        entries.append({
            "title": card_title,
            "rarity": rarity,
            "opened_at": datetime.now(timezone.utc).isoformat(),
        })
        HISTORY_PATH.write_text(json.dumps(entries, indent=2, ensure_ascii=False))


def append_log(message: str) -> None:
    with _lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        log_path = DATA_DIR / "bot.log"
        timestamp = datetime.now(timezone.utc).isoformat()
        with log_path.open("a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")


def get_history(limit: int = 50) -> list[dict]:
    entries = _read_all()
    return list(reversed(entries))[:limit]


def get_recent_logs(limit: int = 100) -> list[str]:
    log_path = DATA_DIR / "bot.log"
    if not log_path.exists():
        return []
    lines = log_path.read_text(encoding="utf-8").splitlines()
    return list(reversed(lines))[:limit]

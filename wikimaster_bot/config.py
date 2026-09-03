"""Configuration persistee de la mini-app (reglages modifiables via le dashboard)."""

import json
import dataclasses
from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
CONFIG_PATH = DATA_DIR / "config.json"

# Intervalles de drop tels qu'annonces par le site (en secondes)
FREE_DROP_INTERVAL_SECONDS = 10 * 60
PREMIUM_DROP_INTERVAL_SECONDS = 3 * 60

STRATEGIES = (
    "immediate",     # ouvre un paquet des qu'un nouveau slot est disponible
    "batch_at_cap",  # attend que le stock soit plein puis ouvre tout d'un coup
    "interval",      # ouvre a intervalle fixe choisi par l'utilisateur
    "manual",        # ne fait qu'observer, l'ouverture reste un clic manuel dans le dashboard
)


@dataclass
class Config:
    premium: bool = False
    max_stock: int = 10
    strategy: str = "immediate"
    interval_minutes: float = 10.0  # utilise uniquement par la strategie "interval"
    headless: bool = True
    bot_enabled: bool = False

    @property
    def drop_interval_seconds(self) -> int:
        return PREMIUM_DROP_INTERVAL_SECONDS if self.premium else FREE_DROP_INTERVAL_SECONDS

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


def load_config() -> Config:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        cfg = Config()
        save_config(cfg)
        return cfg
    raw = json.loads(CONFIG_PATH.read_text())
    return Config(**raw)


def save_config(cfg: Config) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg.to_dict(), indent=2))

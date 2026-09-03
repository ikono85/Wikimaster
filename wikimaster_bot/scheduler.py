"""Boucle de fond qui declenche PackOpener.run_once() au bon rythme.

Le rythme depend de la strategie choisie:
- "immediate" / "batch_at_cap": on verifie a l'intervalle de drop du site
  (10 min en free, 3 min en premium) puisque c'est la frequence a laquelle
  un nouveau slot peut apparaitre.
- "interval": on utilise l'intervalle personnalise choisi par l'utilisateur.
- "manual": le thread tourne mais ne fait rien (l'ouverture se fait depuis
  le dashboard).
"""

import threading
import time

from . import storage
from .config import Config
from .opener import PackOpener


class BotScheduler:
    def __init__(self):
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, config: Config) -> None:
        if self.running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, args=(config,), daemon=True)
        self._thread.start()
        storage.append_log("Bot demarre.")

    def stop(self) -> None:
        self._stop_event.set()
        storage.append_log("Bot arrete.")

    def _loop(self, config: Config) -> None:
        opener = PackOpener(config)
        while not self._stop_event.is_set():
            interval = (
                config.interval_minutes * 60
                if config.strategy == "interval"
                else config.drop_interval_seconds
            )
            try:
                opener.run_once()
            except Exception as exc:  # noqa: BLE001 - on log et on continue
                storage.append_log(f"Erreur pendant l'ouverture: {exc}")
            self._stop_event.wait(timeout=interval)


scheduler = BotScheduler()

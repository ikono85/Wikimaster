"""Logique metier: verifier le stock de paquets et les ouvrir.

Tous les selecteurs viennent de selectors.py -- c'est le seul fichier a
modifier une fois qu'on a les vrais elements du DOM du site.
"""

import re
import time

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

from . import browser, storage
from .config import Config
from .selectors import SELECTORS


class PackOpener:
    def __init__(self, config: Config):
        self.config = config

    def read_stock(self, page: Page) -> int:
        """Lit le texte du bloc "X / Y paquets disponibles" et renvoie X.

        On evite de concatener tous les chiffres du texte (X et Y seraient
        colles, ex. "10 / 10" -> 1010) : on capture uniquement le nombre
        qui precede le "/".
        """
        page.goto(browser.LOGIN_URL)
        stock_locator = page.locator(SELECTORS.pack_stock_count)
        try:
            stock_locator.first.wait_for(state="visible", timeout=15_000)
        except PlaywrightTimeoutError as exc:
            raise RuntimeError(
                "Le compteur de paquets n'apparait pas sur la page apres 15s. "
                "Le compte est probablement pas connecte dans le profil du bot : "
                "decoche 'Navigateur invisible' et connecte-toi manuellement une fois, "
                "ou le selecteur pack_stock_count a change."
            ) from exc
        text = stock_locator.first.inner_text()
        match = re.search(r"(\d+)\s*/", text)
        if not match:
            raise RuntimeError(
                f"Impossible de lire le stock de paquets dans le texte: {text!r}. "
                "Le selecteur pack_stock_count ou le format d'affichage a peut-etre change."
            )
        return int(match.group(1))

    def open_one_pack(self, page: Page) -> bool:
        """Clique sur "Ouvrir" puis passe les cartes une a une jusqu'a revenir
        a l'ecran principal. On ne lit pas le contenu des cartes obtenues.
        """
        button = page.locator(SELECTORS.pack_open_button)
        if button.count() == 0 or not button.first.is_enabled():
            return False
        button.first.click()
        self._skip_through_reveal(page)
        storage.append_log("Paquet ouvert (cartes passees).")
        return True

    def _skip_through_reveal(self, page: Page, timeout_seconds: float = 60.0) -> None:
        """Clique sur le bouton "suivant" tant que le reveal de cartes est actif."""
        skip_button = page.locator(SELECTORS.pack_skip_button)
        open_button = page.locator(SELECTORS.pack_open_button)

        skip_button.first.wait_for(state="visible", timeout=10_000)

        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if open_button.count() > 0 and open_button.first.is_visible():
                return
            if skip_button.count() == 0:
                return
            if skip_button.first.is_enabled():
                skip_button.first.click()
            page.wait_for_timeout(300)

        storage.append_log(
            "Timeout en passant les cartes du paquet : le reveal ne s'est pas termine "
            "dans le delai attendu, verifier pack_skip_button / pack_open_button."
        )

    def run_once(self) -> None:
        """Une passe : lit le stock courant et applique la strategie choisie."""
        with sync_playwright() as p:
            context = browser.launch_context(p, headless=self.config.headless)
            page = context.new_page()
            try:
                stock = self.read_stock(page)
                storage.append_log(f"Stock actuel: {stock}/{self.config.max_stock}")

                if self.config.strategy == "manual":
                    return

                if self.config.strategy == "batch_at_cap":
                    if stock < self.config.max_stock:
                        return
                    to_open = stock
                else:
                    # "immediate" et "interval" ouvrent tout ce qui est disponible
                    # a chaque passage du scheduler.
                    to_open = stock

                for _ in range(to_open):
                    opened = self.open_one_pack(page)
                    if not opened:
                        break
            finally:
                context.close()

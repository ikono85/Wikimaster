"""Logique metier: verifier le stock de paquets et les ouvrir.

Tous les selecteurs viennent de selectors.py -- c'est le seul fichier a
modifier une fois qu'on a les vrais elements du DOM du site.
"""

import re

from playwright.sync_api import Page, sync_playwright

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
        page.goto(browser.BASE_URL)
        text = page.locator(SELECTORS.pack_stock_count).inner_text()
        match = re.search(r"(\d+)\s*/", text)
        if not match:
            raise RuntimeError(
                f"Impossible de lire le stock de paquets dans le texte: {text!r}. "
                "Le selecteur pack_stock_count ou le format d'affichage a peut-etre change."
            )
        return int(match.group(1))

    def is_premium(self, page: Page) -> bool:
        return page.locator(SELECTORS.premium_badge).count() > 0

    def open_one_pack(self, page: Page) -> str | None:
        """Clique sur le bouton d'ouverture et renvoie le titre de la carte obtenue."""
        button = page.locator(SELECTORS.pack_open_button)
        if button.count() == 0 or not button.first.is_enabled():
            return None
        button.first.click()
        result = page.locator(SELECTORS.pack_open_result_card)
        result.first.wait_for(state="visible", timeout=15_000)
        title = result.first.inner_text().strip()
        storage.append_drop(title)
        storage.append_log(f"Paquet ouvert -> {title}")
        return title

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
                    title = self.open_one_pack(page)
                    if title is None:
                        break
            finally:
                context.close()

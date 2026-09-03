"""Gestion de la session Playwright.

On privilegie un "storage_state" (cookies de session) sauvegarde une fois
apres une connexion manuelle, plutot que de stocker un mot de passe en
clair dans la config. Voir README.md, section "Premiere connexion".
"""

from pathlib import Path

from playwright.sync_api import BrowserContext, Playwright, sync_playwright

DATA_DIR = Path(__file__).parent / "data"
STATE_PATH = DATA_DIR / "auth_state.json"

BASE_URL = "https://www.wiki-masters.com"


def has_saved_session() -> bool:
    return STATE_PATH.exists()


def save_login_session(headless: bool = False) -> None:
    """Ouvre un navigateur pour une connexion manuelle unique, puis sauvegarde
    les cookies/local storage dans STATE_PATH. A lancer une seule fois
    (ou a nouveau si la session expire), jamais depuis le scheduler du bot.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        page.goto(BASE_URL)
        input(
            "Connecte-toi manuellement dans la fenetre du navigateur, "
            "puis reviens ici et appuie sur Entree pour sauvegarder la session..."
        )
        context.storage_state(path=str(STATE_PATH))
        browser.close()


def launch_context(playwright: Playwright, headless: bool) -> BrowserContext:
    if not has_saved_session():
        raise RuntimeError(
            "Aucune session sauvegardee. Lance d'abord `python -m wikimaster_bot.browser` "
            "(ou l'action 'Connexion' du dashboard) pour te connecter une fois manuellement."
        )
    browser = playwright.chromium.launch(headless=headless)
    return browser.new_context(storage_state=str(STATE_PATH))


if __name__ == "__main__":
    save_login_session(headless=False)

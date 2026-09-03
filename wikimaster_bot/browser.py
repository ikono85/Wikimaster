"""Gestion du navigateur Playwright utilise par le bot.

On utilise un profil persistant (comme un navigateur normal) : la premiere
fois que le bot ouvre une page, si le compte n'est pas connecte, il suffit
de se connecter manuellement dans la fenetre qui s'affiche. Les cookies
restent ensuite dans le profil pour les lancements suivants, sans etape de
connexion separee a gerer dans l'app.
"""

from pathlib import Path

from playwright.sync_api import BrowserContext, Playwright

DATA_DIR = Path(__file__).parent / "data"
PROFILE_DIR = DATA_DIR / "browser_profile"

BASE_URL = "https://www.wiki-masters.com"
# On navigue toujours via /login plutot que directement sur BASE_URL : si le
# profil n'est pas encore connecte, l'utilisateur tombe sur le vrai formulaire
# de connexion (pas /signup, vers lequel la racine du site redirige les
# visiteurs non connectes). Si le profil est deja connecte, le site redirige
# lui-meme /login vers la page d'accueil.
LOGIN_URL = f"{BASE_URL}/login"


def launch_context(playwright: Playwright, headless: bool) -> BrowserContext:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    return playwright.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        headless=headless,
    )

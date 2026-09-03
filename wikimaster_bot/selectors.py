"""
Point d'entree unique pour tous les selecteurs CSS/XPath du site.

Ces valeurs sont des PLACEHOLDERS. Il faut les remplacer par les vrais
selecteurs releves dans le DOM de wiki-masters.com (clic droit > Inspecter
sur chaque element, ou `playwright codegen https://www.wiki-masters.com`).

Rien d'autre dans le code ne devrait contenir de selecteur en dur: tout
passe par cet objet pour que la mise a jour reste centralisee si le site
change son HTML.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Selectors:
    # Formulaire de connexion
    login_username_input: str = "#login-username"
    login_password_input: str = "#login-password"
    login_submit_button: str = "#login-submit"

    # Page / widget d'ouverture de paquets
    # Le bouton n'a pas d'id/data-testid stable : on le cible via l'image qu'il contient,
    # dont l'attribut alt est fiable ("Ouvrir un paquet").
    pack_open_button: str = 'button:has(img[alt="Ouvrir un paquet"])'
    # Conteneur affichant "X / Y paquets disponibles". On lit le texte complet et on
    # extrait le nombre courant par regex plutot que de cibler un span precis (classes
    # Tailwind dynamiques type text-[var(--color-accent)], fragiles a matcher en CSS).
    pack_stock_count: str = ".card-frame"
    pack_open_result_card: str = "[data-testid='pack-result-card']"  # TODO: a fournir
    pack_next_drop_timer: str = "[data-testid='next-drop-timer']"  # TODO: a fournir

    # Statut premium du compte
    premium_badge: str = "[data-testid='premium-badge']"  # TODO: a fournir


SELECTORS = Selectors()

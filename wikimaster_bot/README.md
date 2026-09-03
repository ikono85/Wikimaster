# WikiMasters Pack Bot

Application desktop (PySide6) pour automatiser l'ouverture de paquets sur
wiki-masters.com, avec une fenetre pour regler le comportement.

## Avant tout : lis ca

- A utiliser uniquement sur un **compte de test**, jamais sur un compte principal.
- L'automatisation d'actions de jeu (farming, auto-open) enfreint tres probablement
  les CGU du site. Le compte utilise peut etre banni si le comportement est detecte
  (frequence trop reguliere, absence d'activite humaine ailleurs, etc.). Ce projet
  ne met en place aucune mesure de contournement de detection anti-bot : c'est de
  l'automatisation simple, pas de l'evasion.
- Les selecteurs CSS dans `selectors.py` (bouton "Ouvrir", compteur de stock, bouton
  "suivant") ont ete releves sur le site reel. Si le site change son HTML, c'est le
  seul fichier a mettre a jour.

## Installation

```bash
cd wikimaster_bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Connexion

Le bot utilise un profil de navigateur persistant (`data/browser_profile/`,
ignore par git). Avant le tout premier lancement (ou si la session expire),
clique sur **"Se connecter (ouvrir le navigateur)"** : une fenetre separee
s'ouvre sur `/login` et reste ouverte tant que tu ne la fermes pas toi-meme.
Connecte-toi manuellement, puis ferme la fenetre — les cookies restent dans
le profil pour les lancements suivants du bot, exactement comme un navigateur
normal. Ce bouton est desactive pendant que le bot tourne (les deux ne
peuvent pas utiliser le meme profil en meme temps).

## Lancer l'application

```bash
python -m wikimaster_bot.gui
```

Une fenetre s'ouvre avec :

- **Reglages** :
  - **Premium** : bascule l'intervalle de drop attendu entre 10 min (free) et 3 min (premium)
  - **Stock maximum** : plafond de paquets non ouverts (10 par defaut)
  - **Strategie d'ouverture** :
    - `immediate` — ouvre chaque paquet des qu'il devient disponible
    - `batch_at_cap` — attend que le stock soit plein puis ouvre tout d'un coup
    - `interval` — ouvre a un rythme personnalise, independant du timer du site
    - `manual` — le bot ne fait qu'observer, aucune ouverture automatique
  - **Headless** : navigateur visible ou invisible pendant l'execution du bot
- **Demarrer / Arreter** — lance ou coupe la boucle de fond
- **Activite** — nombre de paquets ouverts et logs en direct

Le statut premium n'est pas lu sur la page : c'est une simple case a cocher qui
change juste l'intervalle de drop attendu. Le contenu des cartes obtenues n'est
pas lu non plus : le bot clique sur "Ouvrir" puis sur "suivant" jusqu'a revenir
a l'ecran principal, sans se soucier du resultat.

## Structure

- `selectors.py` — tous les selecteurs CSS du site (bouton ouvrir, stock, suivant)
- `config.py` — reglages persistes (JSON dans `data/config.json`)
- `browser.py` — lancement du profil de navigateur persistant utilise par le bot
- `opener.py` — logique d'ouverture (lecture du stock, clic, passage des cartes)
- `scheduler.py` — boucle de fond qui applique la strategie choisie au bon rythme
- `storage.py` — logs et compteur de paquets ouverts
- `gui.py` — application desktop PySide6 (point d'entree : `python -m wikimaster_bot.gui`)

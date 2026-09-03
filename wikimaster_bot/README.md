# WikiMasters Pack Bot

Mini-app pour automatiser l'ouverture de paquets sur wiki-masters.com, avec un
dashboard local (Flask) pour regler le comportement.

## Avant tout : lis ca

- A utiliser uniquement sur un **compte de test**, jamais sur un compte principal.
- L'automatisation d'actions de jeu (farming, auto-open) enfreint tres probablement
  les CGU du site. Le compte utilise peut etre banni si le comportement est detecte
  (frequence trop reguliere, absence d'activite humaine ailleurs, etc.). Ce projet
  ne met en place aucune mesure de contournement de detection anti-bot : c'est de
  l'automatisation simple, pas de l'evasion.
- Les selecteurs CSS dans `selectors.py` sont des **placeholders**. Ils doivent etre
  remplaces par les vrais elements du DOM avant que le bot puisse fonctionner. Sans
  ca, `PackOpener` ne trouvera rien et ne fera rien (echec silencieux cote selecteur,
  visible dans les logs du dashboard).

## Installation

```bash
cd wikimaster_bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Etape 1 : recuperer les vrais selecteurs

Le plus simple est d'utiliser l'outil d'inspection de Playwright :

```bash
playwright codegen https://www.wiki-masters.com
```

Connecte-toi, va sur la page d'ouverture de paquets, et regarde le code genere /
utilise l'inspecteur pour identifier :
- le bouton "Ouvrir un paquet"
- l'element qui affiche le stock actuel de paquets
- l'element affichant le resultat (carte obtenue)
- l'indicateur de statut premium

Reporte ces selecteurs dans `selectors.py`.

## Etape 2 : connexion (une seule fois)

```bash
python -m wikimaster_bot.browser
```

Une fenetre de navigateur s'ouvre, connecte-toi manuellement au compte de test,
puis reviens dans le terminal et appuie sur Entree. La session (cookies) est
sauvegardee dans `data/auth_state.json` (fichier ignore par git). Le bot n'a
jamais besoin de connaitre ton mot de passe.

## Etape 3 : lancer le dashboard

```bash
python -m wikimaster_bot.app
```

Ouvre http://localhost:5000 pour regler :
- **Premium** : bascule l'intervalle de drop attendu entre 10 min (free) et 3 min (premium)
- **Stock maximum** : plafond de paquets non ouvres (10 par defaut)
- **Strategie d'ouverture** :
  - `immediate` — ouvre chaque paquet des qu'il devient disponible
  - `batch_at_cap` — attend que le stock soit plein puis ouvre tout d'un coup
  - `interval` — ouvre a un rythme personnalise, independant du timer du site
  - `manual` — le bot ne fait qu'observer, l'ouverture reste manuelle depuis le dashboard
- **Headless** : navigateur visible ou invisible pendant l'execution du bot

Puis clique sur "Demarrer" pour lancer la boucle de fond.

## Structure

- `selectors.py` — tous les selecteurs CSS/XPath du site (a completer)
- `config.py` — reglages persistes (JSON dans `data/config.json`)
- `browser.py` — connexion Playwright et gestion de la session
- `opener.py` — logique d'ouverture (lecture du stock, clic, lecture du resultat)
- `scheduler.py` — boucle de fond qui applique la strategie choisie au bon rythme
- `storage.py` — historique des cartes obtenues + logs
- `app.py` + `templates/index.html` — dashboard local

# Team Baguette V2

Application web communautaire Team Baguette. Ce dépôt est le **monorepo de la V2**, réunissant le frontend Vue, l'API FastAPI et la configuration Docker.

> **État actuel : socle technique en préparation.** Les environnements DEV et PROD locale sont fonctionnels ; les modules métier, l'authentification Discord et le déploiement sur Raspberry Pi ne sont pas encore implémentés.

## Stack technique

| Composant | Technologie |
| --- | --- |
| Frontend | Vue 3, TypeScript, Vite, PrimeVue 4, Tailwind CSS |
| Backend | Python 3.13, FastAPI |
| Base de données | PostgreSQL 18, SQLAlchemy, Alembic, Psycopg |
| Administration BDD | Adminer (outil de développement facultatif) |
| Frontend en production | Nginx servant le build Vue et relayant `/api/` |
| Conteneurisation | Docker et Docker Compose |
| Temps réel | Contrat de publication préparé ; SSE non implémenté à ce stade |

Les images Docker sont référencées par digest et les dépendances sont verrouillées via `backend/requirements.lock.txt` et `frontend/package-lock.json`. Toute mise à jour doit être volontaire et testée.

## Organisation du dépôt

```text
team-baguette-website/
├── backend/
│   ├── app/
│   │   ├── core/                       # Configuration centrale
│   │   ├── infrastructure/
│   │   │   ├── database/               # Moteur et sessions SQLAlchemy
│   │   │   ├── realtime/               # Contrat d'événements (pas encore de diffusion SSE)
│   │   │   ├── resources/              # Lecture des ressources versionnées
│   │   │   └── storage/                # Lecture/écriture du stockage persistant
│   │   ├── modules/
│   │   │   └── system/                  # Routes de diagnostic
│   │   └── main.py                     # Assemblage de l'application FastAPI
│   ├── migrations/                     # Alembic
│   ├── resources/                      # Fichiers versionnés avec le backend
│   │   ├── tracker_definitions/
│   │   └── tracker_presets/
│   ├── requirements.txt                # Dépendances directes autorisées
│   ├── requirements.lock.txt           # Versions installées figées
│   └── Dockerfile
├── frontend/
│   ├── public/                         # Assets statiques publics
│   ├── src/                            # Application Vue et assets importés
│   ├── nginx.conf                      # Serveur SPA + proxy API de production
│   ├── package.json
│   ├── package-lock.json
│   └── Dockerfile
├── compose.yaml                         # Services communs
├── compose.dev.yaml                     # Surcharges DEV : Vite, rechargement, ports
├── compose.prod.yaml                    # Surcharges PROD : Nginx, port local
├── .env.example                         # Modèle de configuration, sans secret
└── .gitattributes                       # Normalisation des fins de ligne
```

Chaque futur module métier aura son dossier dans `backend/app/modules/`. Les éléments techniques transversaux restent dans `infrastructure/` ; on ne duplique pas la gestion de la BDD, du stockage ou du temps réel dans chaque module.

## Prérequis

- Git.
- Docker Desktop avec Docker Compose v2 (Windows) ou Docker Engine avec le plugin Compose (Linux).
- Un terminal PowerShell pour les exemples ci-dessous ; sous Linux, remplacer `Copy-Item` par `cp`.
- VS Code recommandé, mais facultatif.

Il n'est **pas nécessaire d'installer Python, Node.js ou PostgreSQL sur l'hôte** pour lancer le projet : ces outils fonctionnent dans des conteneurs.

## Installation initiale

Depuis PowerShell :

```powershell
git clone https://github.com/Adri55000/team-baguette-website.git
cd team-baguette-website
Copy-Item .env.example .env.dev
Copy-Item .env.example .env.prod
```

Modifier ensuite **les deux fichiers**, qui ne doivent jamais être commités :

| Variable | `.env.dev` | `.env.prod` (test local) |
| --- | --- | --- |
| `POSTGRES_DB` | `teambaguette` | `teambaguette_prod` |
| `POSTGRES_USER` | `tb_dev` | `tb_prod` |
| `POSTGRES_PASSWORD` | Mot de passe DEV fort | **Autre** mot de passe fort |
| `STORAGE_HOST_PATH` | `./.local-data/dev/storage` | `./.local-data/prod/storage` |

**Important :** une base PostgreSQL déjà initialisée conserve ses identifiants internes. Modifier `POSTGRES_PASSWORD` dans un `.env` ne change pas automatiquement le mot de passe du compte PostgreSQL existant.

Les chemins ci-dessus concernent le PC de développement. Sur le Raspberry Pi, l'emplacement du stockage et la configuration de déploiement seront adaptés lors d'un chantier ultérieur.

## Démarrer le développement

```powershell
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml up -d --build
```

Pour démarrer également Adminer (profil facultatif `tools`) :

```powershell
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml --profile tools up -d
```

| Adresse | Usage |
| --- | --- |
| <http://127.0.0.1:5173> | Frontend Vue avec hot reload |
| <http://127.0.0.1:8000/docs> | Documentation interactive FastAPI |
| <http://127.0.0.1:8000/api/health> | Vérification API |
| <http://127.0.0.1:8000/api/health/db> | Vérification PostgreSQL |
| <http://127.0.0.1:8080> | Adminer, si démarré |

Dans Adminer : serveur `db`, système PostgreSQL, et identifiants définis dans `.env.dev`.

Le dossier `backend/` est monté dans le conteneur pour permettre le rechargement automatique de FastAPI. Le dossier `frontend/` est également monté dans Vite ; ses `node_modules` sont conservés dans un volume Docker séparé.

## Démarrer la production **locale de test**

```powershell
docker compose --env-file .env.prod -f compose.yaml -f compose.prod.yaml up -d --build
```

Accès : <http://127.0.0.1:8081>.

Cette configuration démarre un projet Docker **distinct** (`team-baguette-v2-prod`), avec sa propre base PostgreSQL et son propre stockage. Le frontend est compilé puis servi par Nginx. Le backend et PostgreSQL n'exposent pas de port directement sur l'hôte.

**Attention :** « PROD » désigne ici le mode de fonctionnement compilé, testé localement. Ce n'est **pas encore** la configuration publique finale du Raspberry Pi (HTTPS, reverse proxy externe, sauvegardes, durcissement et déploiement restent à terminer).

## Communication entre les services

- **Développement :** le navigateur appelle `/api/...` sur le port `5173`, et le proxy Vite relaie vers `http://backend:8000` dans le réseau Docker.
- **Production locale :** le navigateur appelle `/api/...` sur le port `8081`, et Nginx relaie vers `http://backend:8000`.
- **Backend :** SQLAlchemy rejoint PostgreSQL via le nom de service Docker `db` sur le port interne `5432`.

Le frontend utilise donc des chemins relatifs (`fetch('/api/health')`) dans les deux environnements, sans adresse API codée en dur.

## Commandes de maintenance

Toutes les commandes sont à lancer depuis la racine du dépôt.

**État des conteneurs :**

```powershell
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml ps
docker compose --env-file .env.prod -f compose.yaml -f compose.prod.yaml ps
docker compose ls
```

**Logs :**

```powershell
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml logs --tail=100 backend
docker compose --env-file .env.prod -f compose.yaml -f compose.prod.yaml logs --tail=100 frontend
```

**Reconstruire un service après modification de son image :**

```powershell
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml up -d --build backend
docker compose --env-file .env.prod -f compose.yaml -f compose.prod.yaml up -d --build frontend
```

**Arrêter un environnement sans supprimer ses volumes de données :**

```powershell
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml --profile tools down
docker compose --env-file .env.prod -f compose.yaml -f compose.prod.yaml down
```

> **Ne pas utiliser `down -v`** : cette option supprime aussi les volumes du projet, dont les données PostgreSQL. Une reconstruction ou un `down` simple ne doit pas être confondu avec une suppression de données.

Après recréation du backend de production, une réponse `502` du proxy peut nécessiter temporairement le redémarrage du frontend Nginx :

```powershell
docker compose --env-file .env.prod -f compose.yaml -f compose.prod.yaml restart frontend
```

La résolution durable de ce cas sera examinée avant déploiement public.

## Sauvegardes et restaurations locales

Les environnements DEV et PROD locale disposent d'un script
PowerShell de sauvegarde PostgreSQL et du stockage persistant.

Les procédures, les tests de restauration et leurs limites
sont documentés dans [Sauvegardes locales](docs/sauvegardes-locales.md).

L'automatisation et la conservation des sauvegardes sur le
Raspberry Pi seront préparées lors du déploiement.

## Base de données et Alembic

Le moteur et la base SQLAlchemy partagée se trouvent dans `backend/app/infrastructure/database/database.py`. Alembic utilise la même configuration depuis `backend/migrations/env.py`.

**Consulter la migration courante en DEV :**

```powershell
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml exec backend alembic current
```

**Appliquer les migrations existantes en DEV :**

```powershell
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml exec backend alembic upgrade head
```

Aucune table métier n'a encore été créée. Les commandes de création de migrations et leur procédure de déploiement seront précisées avec les premiers modèles SQLAlchemy. Ne pas exécuter les migrations de développement sur la base de production par erreur.

## Ressources et stockage

Deux mécanismes sont séparés :

- **Ressources versionnées :** `backend/resources/`, intégrées aux images Docker sous `/app/resources` et lues par `ResourceReader`. Elles comprennent les futures définitions et presets de trackers fournis avec le site.
- **Fichiers persistants :** chemin hôte défini par `STORAGE_HOST_PATH`, monté dans le backend à `/data/storage` et accessible via `LocalStorage`. Leurs données ne sont pas versionnées sur GitHub.

La convention de stockage prévue par le modèle de données est :

```text
storage/
├── uploads/             # Fichiers uploadés
├── overlay_packs/       # Versions de packs extraites
└── restreams/           # États live : hints, trackers, données runtime
```

Cette arborescence correspond à une **convention cible**, pas à des modules métier déjà implémentés. Les uploads seront référencés ultérieurement en BDD ; les états live pourront utiliser des chemins déterministes.

Le code d'accès aux fichiers est centralisé sous `backend/app/infrastructure/`. Les contrôles actuels de chemins sont préliminaires : ils ne remplacent pas les futures validations et autorisations d'upload.

## Dépendances et versions

- **Python :** `backend/requirements.txt` décrit les dépendances directes ; `backend/requirements.lock.txt` fixe les versions installées dans les images.
- **Frontend :** `frontend/package-lock.json` fixe les dépendances ; Docker exécute `npm ci` pour installer exactement celles du lockfile.
- **Images Docker :** les références dans les Dockerfiles et Compose utilisent des digests SHA-256. Une mise à jour doit être volontaire et suivie de tests.
- **Git :** `.gitattributes` normalise les fichiers texte en LF ; les fichiers `.env.dev`, `.env.prod` et `.local-data/` ne doivent pas être commités (contrairement à `.env.example`).

Pour vérifier les dépendances du backend DEV :

```powershell
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml exec backend python -m pip check
```

Pour vérifier la compilation du frontend, reconstruire son image de production ou lancer `npm run build` dans un environnement Node approprié.

## État des validations

**Déjà vérifié localement :** démarrage DEV et PROD, communication Vue → FastAPI → PostgreSQL, indépendance des deux bases et des deux dossiers de stockage, persistance des fichiers après recréation de conteneurs, lecture des ressources versionnées, builds et tests de compatibilité ARM64 préliminaires.

**Reste à faire avant la mise en ligne :** sauvegardes et restauration éprouvées, sécurité et secrets de déploiement, configuration Nginx/HTTPS sur le Raspberry Pi, cohabitation avec la V1, validation native ARM64 sur le Pi. Les routes de diagnostic, notamment `/api/health/db`, devront aussi faire l'objet d'une revue avant exposition publique.

Les fonctionnalités métier (Discord OAuth, utilisateurs, permissions, tournois, restreams, trackers, etc.) ne sont pas encore développées dans la V2.

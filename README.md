# Team Baguette V2

Application web communautaire Team Baguette. Ce dépôt est le **monorepo de la V2**, réunissant le frontend Vue, l'API FastAPI et la configuration Docker.

> **État au 9 novembre 2026 : socle technique déployé.** Les environnements DEV et PROD locale fonctionnent sur PC, et la V2 est accessible sur le Raspberry Pi à [dev.teambaguette.fr](https://dev.teambaguette.fr), en parallèle de la V1. Le déploiement, HTTPS et les sauvegardes automatiques ont été testés. Les fonctionnalités métier et l'authentification Discord ne sont pas encore développées.

## Stack technique

| Composant | Technologie |
| --- | --- |
| Frontend | Vue 3, TypeScript, Vite, PrimeVue 4, Tailwind CSS |
| Backend | Python 3.13, FastAPI |
| Base de données | PostgreSQL 18, SQLAlchemy, Alembic, Psycopg |
| Administration BDD | Adminer (outil de développement facultatif) |
| Frontend en production | Nginx servant le build Vue et relayant `/api/` |
| Conteneurisation | Docker et Docker Compose |
| Publication ARM64 | GitHub Actions et GitHub Container Registry (GHCR) |
| Temps réel | Contrat de publication préparé ; SSE non implémenté à ce stade |

Les images de base Docker sont référencées par digest et les dépendances sont verrouillées via `backend/requirements.lock.txt` et `frontend/package-lock.json`. Les images applicatives destinées au Pi sont publiées dans GHCR avec un tag basé sur le SHA du commit Git. Toute mise à jour doit être volontaire et testée.

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
├── compose.pi.yaml                      # Surcharges Raspberry Pi : images ARM64 GHCR
├── .github/workflows/
│   └── publish-images.yml               # Build et publication ARM64 sur main
├── docs/
│   ├── sauvegardes-locales.md           # Sauvegardes DEV et PROD locale
│   ├── deploiement-pi.md                # Déploiement et maintenance du Pi
│   └── restauration-pi.md               # Sauvegardes et reprise après incident sur le Pi
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

Les chemins ci-dessus concernent le PC de développement. Sur le Raspberry Pi, le dépôt est installé dans `/srv/team-baguette-v2`, le stockage persistant dans `/srv/team-baguette-v2-data/storage`, et les paramètres secrets restent dans le fichier local `.env.prod` (non versionné). Voir [Déploiement sur Raspberry Pi](docs/deploiement-pi.md).

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

**Attention :** « PROD locale » désigne ici le mode de fonctionnement compilé, testé sur le PC. Le déploiement Raspberry Pi utilise les mêmes fichiers Compose de base, complétés par `compose.pi.yaml`, des images ARM64 publiées dans GHCR et un Nginx hôte avec HTTPS. Voir [Déploiement sur Raspberry Pi](docs/deploiement-pi.md).

## Communication entre les services

- **Développement :** le navigateur appelle `/api/...` sur le port `5173`, et le proxy Vite relaie vers `http://backend:8000` dans le réseau Docker.
- **Production locale :** le navigateur appelle `/api/...` sur le port `8081`, et Nginx relaie vers `http://backend:8000`.
- **Raspberry Pi :** le Nginx de l'hôte termine HTTPS sur `dev.teambaguette.fr` et transmet les requêtes au frontend Docker sur `127.0.0.1:8081`. Le Nginx du frontend sert Vue et relaie `/api/` vers FastAPI. Le backend et PostgreSQL ne publient pas de port sur l'hôte. La V1 et Archipelago continuent de fonctionner séparément.
- **Backend :** SQLAlchemy rejoint PostgreSQL via le nom de service Docker `db` sur le port interne `5432`.

Le frontend utilise donc des chemins relatifs (`fetch('/api/health')`) dans les deux environnements, sans adresse API codée en dur.

## Déploiement sur Raspberry Pi

La V2 est déployée sur le Raspberry Pi de développement à [dev.teambaguette.fr](https://dev.teambaguette.fr), sans remplacer la V1 accessible sur `teambaguette.fr`.

À chaque `push` sur `main`, `.github/workflows/publish-images.yml` construit et publie deux images `linux/arm64` dans GHCR. Sur le Pi, le déploiement consiste à synchroniser le dépôt, sélectionner dans `.env.prod` le tag `TB_IMAGE_TAG=sha-<SHA_GIT_COMPLET>`, puis à effectuer `docker compose pull` et `up -d --no-build` avec `compose.yaml`, `compose.prod.yaml` et `compose.pi.yaml`. **Aucune compilation de la V2 n'est nécessaire sur le Pi.**

Les procédures détaillées et les contrôles après mise à jour sont documentés ici :

- [Déploiement, maintenance et retour arrière sur le Pi](docs/deploiement-pi.md).
- [Sauvegardes et restauration sur le Pi](docs/restauration-pi.md).

Les éléments propres à l'hôte (Nginx externe, Certbot, cron, script de sauvegarde et secrets) ne sont pas tous versionnés sur GitHub. Les fichiers `.env.prod` ne doivent jamais être commités.

## Commandes de maintenance locale

Les commandes ci-dessous concernent **uniquement le PC** (DEV et PROD locale) et sont à lancer depuis la racine du dépôt. Pour le Raspberry Pi, utiliser la [procédure dédiée](docs/deploiement-pi.md).

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

Après recréation du backend en PROD locale, un `502` transitoire peut apparaître avant que FastAPI soit prêt. Retester `/api/health`, consulter les logs si le problème persiste, puis, si nécessaire, redémarrer le frontend Nginx :

```powershell
docker compose --env-file .env.prod -f compose.yaml -f compose.prod.yaml restart frontend
```

Pour le déploiement Raspberry Pi, le test HTTP doit être fait **après** le démarrage effectif du backend ; un `502` transitoire a été observé puis résolu sans intervention lors d'une mise à jour.

## Sauvegardes et restaurations

**Sur le PC :** les environnements DEV et PROD locale disposent d'un script PowerShell de sauvegarde de PostgreSQL et du stockage persistant. Les tests et limites sont décrits dans [Sauvegardes locales](docs/sauvegardes-locales.md).

**Sur le Raspberry Pi :** une sauvegarde V2 automatique est exécutée à 03 h 30 et copiée sur Windows via WinSCP à 12 h. Chaque archive datée contient `database.dump`, `storage.tar.gz`, `config.tar.gz` et `env.prod.gpg` (secrets chiffrés avec GPG). Le Pi conserve les sept dernières sauvegardes et la synchronisation Windows conserve les copies déjà récupérées. Les tests de sauvegarde, de transfert, de déchiffrement GPG et de restauration isolée ont réussi ; **une reprise complète après panne du Pi reste à tester**. Voir [Sauvegardes et restauration sur le Pi](docs/restauration-pi.md).

**Protection des données :** à ce stade, seuls les secrets `.env.prod` sont chiffrés ; `database.dump` et `storage.tar.gz` ne le sont pas. Il faudra revoir cette protection avant d'y stocker des données personnelles d'utilisateurs.

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

## État des validations — 9 novembre 2026

**Validé sur le PC :** démarrage DEV et PROD locale, communication Vue → FastAPI → PostgreSQL, indépendance des bases et dossiers de stockage, persistance après recréation des conteneurs, accès aux ressources versionnées, builds et tests de restauration isolée.

**Validé sur le Raspberry Pi :** images Docker ARM64 construites via GitHub Actions et exécutées sur le Pi, cohabitation avec la V1 et Archipelago, Nginx/HTTPS sur `dev.teambaguette.fr`, renouvellement Certbot testé à blanc, redémarrage automatique des trois conteneurs, contrôle des ports, protection Nginx des chemins cachés (`404`), réponses des endpoints de diagnostic et chaîne de sauvegarde V2 jusqu'à Windows. Les archives PostgreSQL et de stockage ont fait l'objet de tests de restauration isolés.

**À valider ou réévaluer ultérieurement :** restauration intégrale après panne du Pi, migrations Alembic et retour arrière avec données métier, surveillance/alertes, protection des futures données personnelles dans les sauvegardes et revue de l'exposition publique de `/api/health/db`. Le dimensionnement mémoire définitif et un éventuel hébergement externe seront examinés sur des charges représentatives, en tenant compte de l'arrêt de la V1 et d'un audit d'Archipelago.

Les fonctionnalités métier (Discord OAuth, utilisateurs, permissions, tournois, restreams, trackers, etc.) ne sont pas encore développées dans la V2.

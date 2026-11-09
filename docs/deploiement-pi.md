# Déploiement V2 sur Raspberry Pi — Team Baguette

> **État au 9 novembre 2026.** Procédure de mise à jour vérifiée sur le Pi. Le domaine `dev.teambaguette.fr` sert la V2 en parallèle de la V1 sur `teambaguette.fr`.
>
> **Portée :** exploitation du Pi. Les scripts et configurations propres à l'hôte ne sont pas tous versionnés dans ce dépôt. Ne jamais commiter `.env.prod`, des clés privées, des exports PostgreSQL ou des sauvegardes de production.

## Architecture et emplacements

| Élément | Emplacement / service |
| --- | --- |
| Dépôt Git sur le Pi | `/srv/team-baguette-v2` |
| Configuration secrète du Pi | `/srv/team-baguette-v2/.env.prod` |
| Stockage persistant | `/srv/team-baguette-v2-data/storage` |
| Projet Docker Compose | `team-baguette-v2-pi` |
| Frontend Docker | `127.0.0.1:8081` sur l'hôte → Nginx du conteneur |
| Backend FastAPI | Service Docker interne `backend:8000`, non publié sur l'hôte |
| PostgreSQL 18 | Service Docker interne `db:5432`, volume Docker persistant |
| Nginx hôte | `/etc/nginx/sites-available/dev.teambaguette.fr` |
| Certificat HTTPS V2 | `/etc/letsencrypt/live/dev.teambaguette.fr/` |
| Script de sauvegarde | `/usr/local/sbin/backup_team_baguette_v2.sh` |

Le Nginx **hôte** termine HTTPS et relaie vers `127.0.0.1:8081` ; le Nginx **frontend Docker** sert Vue et relaie `/api/` à FastAPI. Sa configuration est versionnée dans `frontend/nginx.conf`.

La V1 et Archipelago restent des services **distincts**, à ne pas redémarrer lors d'une mise à jour V2.

## Publication des images

Le workflow `.github/workflows/publish-images.yml` s'exécute à chaque `push` sur `main` : il construit des images `linux/arm64` et publie les deux images dans GHCR :

- `ghcr.io/adri55000/tb-v2-backend:sha-<SHA_GIT_COMPLET>` ;
- `ghcr.io/adri55000/tb-v2-frontend:sha-<SHA_GIT_COMPLET>`.

Les tags `:dev` existent mais **ne pas les employer pour un déploiement reproductible** : utiliser le tag `sha-...`. Le workflow doit être terminé avec succès avant la mise à jour du Pi.

## Mettre à jour la V2 sur le Pi (procédure utilisée)

1. Sur le PC, après commit/push et validation du workflow GitHub Actions, relever le SHA complet :

   ```powershell
   git rev-parse HEAD
   ```

2. Sur le Pi, synchroniser les fichiers versionnés :

   ```bash
   cd /srv/team-baguette-v2
   git pull --ff-only origin main
   ```

3. Conserver le **tag précédent** (utile pour un retour arrière). Afficher uniquement la variable concernée :

   ```bash
   sudo grep '^TB_IMAGE_TAG=' .env.prod
   ```

4. Modifier **uniquement** `TB_IMAGE_TAG=sha-<SHA_GIT_COMPLET>` dans `.env.prod` :

   ```bash
   sudo nano .env.prod
   ```

   Ne jamais afficher, copier dans un ticket ou commiter l'intégralité de ce fichier.

5. Récupérer puis lancer les images, sans build sur le Pi :

   ```bash
   sudo docker compose --env-file .env.prod \
     -f compose.yaml -f compose.prod.yaml -f compose.pi.yaml pull

   sudo docker compose --env-file .env.prod \
     -f compose.yaml -f compose.prod.yaml -f compose.pi.yaml up -d --no-build
   ```

6. Vérifier l'état :

   ```bash
   sudo docker compose --env-file .env.prod \
     -f compose.yaml -f compose.prod.yaml -f compose.pi.yaml ps
   ```

7. Tester la réponse HTTPS **après le démarrage effectif du backend** :

   ```bash
   for path in / /api/health /api/health/db /.env /.git/config; do
     curl -sS -o /dev/null -w "$path -> %{http_code}\n" \
       "https://dev.teambaguette.fr$path"
   done
   ```

   Résultats attendus actuellement : `/`, `/api/health` et `/api/health/db` → `200` ; `/.env` et `/.git/config` → `404`.

Un `502` transitoire peut apparaître juste après `up -d` pendant le démarrage de FastAPI. **Ne pas conclure à une panne sur un test unique** : retester après disponibilité du backend, puis examiner les logs si le problème persiste. Ce mécanisme n'assure pas un déploiement sans interruption.

### Diagnostic en cas d'échec

```bash
sudo docker compose --env-file .env.prod \
  -f compose.yaml -f compose.prod.yaml -f compose.pi.yaml logs --tail=100 backend

sudo docker compose --env-file .env.prod \
  -f compose.yaml -f compose.prod.yaml -f compose.pi.yaml logs --tail=100 frontend

sudo docker compose --env-file .env.prod \
  -f compose.yaml -f compose.prod.yaml -f compose.pi.yaml logs --tail=100 db
```

Attention : consulter les logs avant de les partager, car des messages applicatifs peuvent contenir des informations sensibles.

## Retour à une image précédente

Si l'application ne fonctionne plus après une mise à jour **sans changement incompatible du schéma de base de données ou des données** :

1. Vérifier que les anciennes images existent encore dans GHCR.
2. Rétablir dans `.env.prod` l'ancien `TB_IMAGE_TAG=sha-...` conservé avant déploiement.
3. Relancer `pull` puis `up -d --no-build` avec les trois fichiers Compose (commandes ci-dessus).
4. Refaire les tests HTTPS et consulter les logs.

**Important :** changer le tag Docker ne revient pas automatiquement sur une migration Alembic ni sur des modifications de données. En cas de migration incompatible, définir d'abord une stratégie de restauration PostgreSQL, à partir d'une sauvegarde appropriée. Si les fichiers Compose ont eux-mêmes changé, le retour arrière doit aussi prendre en compte leur version Git ; ne pas faire de `git reset --hard` sans connaître les changements locaux.

## Maintenance courante

- Les trois conteneurs utilisent `restart: unless-stopped`. Le redémarrage du Pi a déjà été testé avec succès.
- Les ports publiés par Docker ont été vérifiés : seul le frontend est publié sur `127.0.0.1:8081`; backend et PostgreSQL restent internes.
- Le certificat Let's Encrypt de `dev.teambaguette.fr` se renouvelle avec Certbot ; hook de rechargement Nginx : `/etc/letsencrypt/renewal-hooks/deploy/reload-nginx-dev.sh`. Un test de renouvellement à blanc a été réalisé.
- Les sauvegardes V2 sont planifiées à **03 h 30** sur le Pi et synchronisées depuis Windows par WinSCP à **12 h**. Voir [Restauration Pi](restauration-pi.md).
- La RAM de la V2 a été mesurée au repos. **Aucune limite mémoire définitive n'a été arrêtée** : dimensionnement à revoir après développement, audit Archipelago et décision d'hébergement.
- L'endpoint `/api/health/db` reste public pour le développement ; revoir sa visibilité lors de l'ouverture de la production définitive.

## Points restant à valider

- Déploiement avec migrations Alembic et rollback compatible lorsque les premières tables métier existeront.
- Vérification du comportement en charge et dimensionnement RAM final ; éventuel hébergement externe.
- Procédure de restauration intégrale après destruction du volume PostgreSQL ou panne totale du Pi (voir document dédié).
- Surveillance automatisée et alerte en cas d'échec de sauvegarde, de certificat ou de disponibilité de la V2.

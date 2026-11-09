# Sauvegardes et restauration du Raspberry Pi — Team Baguette V2

> **État au 9 novembre 2026.** La sauvegarde automatisée, le transfert vers Windows, le déchiffrement GPG et des tests de restauration **isolés** ont été validés. **Une restauration complète du site après panne du Pi n'a pas encore été testée** : les sections de reprise après sinistre sont des instructions de préparation, pas une procédure garantie.
>
> Les sauvegardes V1 sont distinctes et ne doivent pas être remplacées par celles de la V2.

## Ce qui est sauvegardé

Sur le Pi : `/home/adri/backups/team-baguette-v2/<AAAAMMJJ_HHMMSS>/`.

| Fichier | Contenu | Protection |
| --- | --- | --- |
| `database.dump` | PostgreSQL avec `pg_dump -Fc` | Archive **non chiffrée** |
| `storage.tar.gz` | `/srv/team-baguette-v2-data/storage` | Archive **non chiffrée** |
| `config.tar.gz` | Configuration Nginx DEV, cron, hook Certbot, script de sauvegarde | Archive **non chiffrée** |
| `env.prod.gpg` | `/srv/team-baguette-v2/.env.prod` | **Chiffré avec clé publique GPG** |

Les ressources versionnées de l'application et ses Dockerfiles restent dans GitHub, et les images publiées dans GHCR. Les certificats et clés privées Let's Encrypt ne sont pas inclus dans `config.tar.gz` : ils peuvent être réémis si nécessaire.

**Attention aux données personnelles futures :** `database.dump` et `storage.tar.gz` ne sont pas chiffrés. Quand les fonctionnalités utilisateurs seront actives, ils pourraient contenir des informations privées. Protéger l'accès au PC de sauvegarde et réévaluer le chiffrement de l'ensemble des archives avant l'ouverture publique.

## Automatisation et emplacement des scripts

- Script exécuté par `root` : `/usr/local/sbin/backup_team_baguette_v2.sh`, permissions `700`, propriétaire `root`.
- Cron : `/etc/cron.d/team-baguette-v2-backup`, chaque jour à **03 h 30**.
- Journal : `/var/log/team-baguette-v2-backup.log`.
- Le script vérifie la lisibilité de l'export PostgreSQL et des archives tar avant publication ; il conserve **7 dossiers de sauvegarde datés** sur le Pi.
- La sauvegarde se construit d'abord dans un dossier `.inprogress-*` ; sa publication intervient seulement après succès.
- Sur Windows, tâche planifiée **Backup TeamBaguette** à **12 h**, via `backup_auto.bat` et WinSCP, session `BackupPi`.
- Archives Windows V2 : dossier `backups_autos_v2` sous le répertoire de sauvegarde configuré dans WinSCP (chemin propre au PC). La synchronisation actuelle ne supprime pas automatiquement les archives Windows déjà récupérées.

La planification **ne garantit pas** que Windows ait récupéré toutes les archives : consulter les journaux du script et de WinSCP après un incident, et vérifier l'horodatage de la dernière copie.

### Créer une sauvegarde à la demande

```bash
sudo /usr/local/sbin/backup_team_baguette_v2.sh
ls -lh "$(ls -dt /home/adri/backups/team-baguette-v2/20* | head -n 1)"
```

Résultat attendu : quatre fichiers, tous non vides. Le script peut échouer si Docker/PostgreSQL n'est pas opérationnel ; dans ce cas, ne pas considérer la tentative comme une sauvegarde réussie.

## Contrôles non destructifs d'une archive

Sur le Pi, remplacer `<DOSSIER>` par le nom daté **exact** de la sauvegarde à examiner :

```bash
BACKUP="/home/adri/backups/team-baguette-v2/<DOSSIER>"
ls -lh "$BACKUP"
sudo docker compose --env-file /srv/team-baguette-v2/.env.prod \
  -f /srv/team-baguette-v2/compose.yaml \
  -f /srv/team-baguette-v2/compose.prod.yaml \
  -f /srv/team-baguette-v2/compose.pi.yaml \
  exec -T db pg_restore -l < "$BACKUP/database.dump" > /dev/null

tar -tzf "$BACKUP/storage.tar.gz" > /dev/null
tar -tzf "$BACKUP/config.tar.gz"
```

`pg_restore -l` contrôle seulement que l'archive PostgreSQL est lisible ; **il ne prouve pas qu'une restauration complète réussira**. Les fichiers de sauvegarde doivent être traités comme des données de confiance avant extraction.

## Tester PostgreSQL sans toucher à la base V2 active

Une restauration dans un conteneur PostgreSQL **temporaire et isolé du réseau** a été réalisée lors de la mise en place. Pour répéter l'exercice, adapter le chemin de l'archive ; vérifier qu'aucun conteneur portant le nom de test n'existe déjà.

```bash
BACKUP="/home/adri/backups/team-baguette-v2/<DOSSIER>"
sudo docker run -d --rm --name tb-v2-restore-test --network none \
  -e POSTGRES_PASSWORD=temporary-test-only \
  postgres:18@sha256:3a4264520e121176619f54ff867d12774bc81e95e7b84db58d63bccdb6144b81

sudo docker exec tb-v2-restore-test pg_isready -U postgres
sudo docker cp "$BACKUP/database.dump" tb-v2-restore-test:/tmp/database.dump
sudo docker exec tb-v2-restore-test createdb -U postgres tb_v2_restore_test
sudo docker exec tb-v2-restore-test pg_restore -U postgres \
  -d tb_v2_restore_test --no-owner --no-acl --exit-on-error \
  /tmp/database.dump
sudo docker exec tb-v2-restore-test psql -U postgres \
  -d tb_v2_restore_test -c 'SELECT current_database();'

sudo docker stop tb-v2-restore-test
```

La version de PostgreSQL et son digest ci-dessus correspondent à ceux référencés par le dépôt au 9 novembre 2026. Pour un autre environnement ou une sauvegarde future, vérifier leur compatibilité. Ne pas utiliser le volume PostgreSQL de production pour ce test.

### Tester le stockage et les configurations

Extraire **dans un nouveau dossier de test**, jamais dans les chemins actifs :

```bash
BACKUP="/home/adri/backups/team-baguette-v2/<DOSSIER>"
TEST_DIR="$(mktemp -d /tmp/tb-v2-restore-test.XXXXXXXX)"
tar -xzf "$BACKUP/storage.tar.gz" -C "$TEST_DIR"
tar -xzf "$BACKUP/config.tar.gz" -C "$TEST_DIR"
find "$TEST_DIR" -maxdepth 4 -type f
```

Comparer ensuite les fichiers restaurés avec les originaux si ceux-ci sont toujours disponibles et inchangés (par exemple via `diff -qr` ou SHA-256). Supprimer le dossier de test seulement après inspection. Les archives de configuration ne doivent **pas** être extraites directement dans `/` pendant un test.

## Secrets : déchiffrer `env.prod.gpg` sur Windows

La clé **publique** GPG est installée dans le trousseau dédié `/root/.gnupg-tb-v2-backup` du Pi. La clé **privée**, protégée par une phrase secrète, reste dans Gpg4win sur Windows ; un export de secours est conservé sur une clé USB déconnectée. La clé privée ne doit **jamais** être envoyée sur le Pi, GitHub ou dans un dossier de sauvegarde synchronisé.

1. Récupérer `env.prod.gpg` avec FileZilla **en SFTP** ou depuis le dossier de sauvegarde Windows.
2. Vérifier son déchiffrement **sans afficher ni écrire les secrets** :

   ```powershell
   & 'C:\Program Files\GnuPG\bin\gpg.exe' --decrypt 'C:\chemin\vers\env.prod.gpg' > $null
   $LASTEXITCODE
   ```

   Code retour attendu : `0`. La phrase secrète peut être demandée.

3. Pour une **restauration réelle uniquement**, déchiffrer vers un fichier temporaire protégé sur Windows, transférer avec SFTP vers le Pi, puis installer en tant que `root` avec permission `600`. Supprimer les copies temporaires en clair après usage. **Cette procédure de remise en place après panne n'a pas encore été testée.**

Si Windows a été réinstallé, importer l'export de clé privée de la clé USB dans Gpg4win et retrouver sa phrase secrète avant de poursuivre. Sans la clé privée (ou sa sauvegarde) et sa phrase secrète, l'archive chiffrée ne pourra pas être récupérée.

## Reprise après panne : ordre de travail à suivre

En cas de destruction du disque/volume ou de réinstallation du Pi, **ne pas lancer directement des commandes qui écrasent le volume PostgreSQL**. Une remise en service complète devra suivre cet ordre :

1. Identifier la dernière **sauvegarde cohérente** (`database.dump`, `storage.tar.gz`, `config.tar.gz`, `env.prod.gpg`) et copier les archives vers un support de travail fiable.
2. Préparer la machine (Linux, Docker Engine/Compose, Git, Nginx et Certbot) et récupérer le dépôt depuis GitHub, à la version de code compatible avec la sauvegarde.
3. Vérifier les chemins, les volumes et les permissions (notamment le compte backend UID/GID **10001** pour le stockage).
4. Restaurer la configuration secrète `.env.prod` après déchiffrement GPG, sans la rendre publique.
5. Restaurer PostgreSQL dans un **nouveau volume** et le stockage persistant dans son emplacement préparé ; vérifier le contenu avant ouverture publique.
6. Reconstituer ou restaurer la configuration Nginx hôte, le cron, le script de sauvegarde et le hook Certbot à partir de `config.tar.gz` ; vérifier les permissions `root`.
7. Réémettre ou restaurer correctement les certificats Let's Encrypt, vérifier DNS, HTTPS et le routage Nginx.
8. Démarrer les conteneurs sur le tag compatible, vérifier `/api/health` et `/api/health/db`, puis tester les données et les fonctionnalités métier avant de rouvrir le service.
9. Revalider les sauvegardes planifiées, la synchronisation WinSCP et la possibilité de restauration hors machine.

**État de validation :** nous avons testé `pg_restore` en environnement isolé, l'extraction des fichiers, la copie WinSCP et le déchiffrement des secrets. **Le remplacement effectif de la BDD/du stockage en service et la reconstruction intégrale du Pi restent à tester avant de considérer la procédure de reprise comme opérationnelle.**

## Améliorations à planifier

- Chiffrement ou protection renforcée des archives **BDD + stockage**, en plus du fichier de secrets, avant qu'elles ne contiennent des données utilisateurs.
- Alerte sur les sauvegardes échouées, l'espace disque, la rétention et la non-réception sur Windows ; rotation du journal de backup.
- Test périodique de restauration isolée avec des données représentatives.
- Vérification de la copie de secours GPG et de la conservation de la phrase secrète ; idéalement stockage USB chiffré.
- Documentation et répétition d'une reprise complète à partir d'une machine vierge.

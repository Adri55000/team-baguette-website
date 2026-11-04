# Sauvegardes et restaurations locales — Team Baguette V2

> **Portée :** procédures testées sur le PC Windows avec Docker Desktop et PowerShell. Elles concernent les environnements DEV et PROD **locaux**. Le Raspberry Pi, la sauvegarde planifiée et la conservation hors machine feront l'objet du chantier de déploiement.

## Données concernées

Une sauvegarde locale associe deux archives portant le **même horodatage** :

- `database-<horodatage>.dump` : base PostgreSQL, créée avec `pg_dump` au format personnalisé (`-Fc`) ;
- `storage-<horodatage>.tar.gz` : dossier de stockage persistant référencé par `STORAGE_HOST_PATH`.

Les archives sont enregistrées sous `.local-data/backups/dev/` ou `.local-data/backups/prod/` et sont ignorées par Git. Elles **ne comprennent pas** les fichiers `.env`, le code source ni les secrets. Conserver ces éléments et leurs procédures de récupération séparément.

## Créer une sauvegarde

Depuis la racine du dépôt, dans PowerShell :

```powershell
.\scripts\backup-local.ps1 -Target dev
.\scripts\backup-local.ps1 -Target prod
```

Le script `backup-local.ps1` :

1. lit la configuration Docker Compose de l'environnement choisi ;
2. exporte PostgreSQL via `pg_dump` et copie l'archive sur Windows ;
3. contrôle sa lisibilité avec `pg_restore -l` ;
4. archive le stockage persistant avec le `tar.exe` de Windows ;
5. contrôle la lisibilité de l'archive de fichiers.

Une exécution réussie affiche `SAUVEGARDE TERMINEE AVEC SUCCES` et les chemins des deux fichiers. En cas d'erreur, **ne pas considérer la sauvegarde comme complète** ; inspecter les fichiers éventuellement produits avant de relancer.

**Prérequis :** Docker Desktop démarré, PostgreSQL de l'environnement concerné opérationnel, fichiers `.env.dev` / `.env.prod` renseignés et dossier de stockage disponible.

## Tester une restauration DEV

```powershell
.\scripts\test-restore-local.ps1 -Target dev
```

Le script choisit la paire de sauvegardes complète la plus récente, extrait les fichiers sous `.local-data/restore-tests/` et **crée une nouvelle base de test** dans PostgreSQL DEV. Il affiche le nom de cette base et le chemin du dossier restauré. Il ne remplace pas la base `teambaguette` ni son stockage.

Après l'exécution, vérifier les données de la base et comparer les empreintes de fichiers utiles :

```powershell
Get-FileHash .local-data/dev/storage/test-persistence.txt
Get-FileHash <chemin-du-dossier-restaure>/storage/test-persistence.txt
```

Adapter les chemins aux fichiers effectivement présents. Les deux empreintes d'un même fichier doivent coïncider.

### Nettoyage d'un test DEV

Reprendre **exactement** le nom de base et le dossier de restauration affichés par le script :

```powershell
docker compose --env-file .env.dev -f compose.yaml -f compose.dev.yaml exec db psql -U tb_dev -d postgres -c "DROP DATABASE <nom-exact-de-la-base-de-test>;"
Remove-Item -LiteralPath "<chemin-exact-du-dossier-de-test>" -Recurse -Force
```

Remplacer les valeurs entre chevrons avant exécution. **Ne jamais** appliquer ces commandes à `teambaguette` ni à un dossier de stockage actif.

## Tester une restauration PROD sans toucher à PostgreSQL PROD

**Ne pas lancer `test-restore-local.ps1 -Target prod` dans sa version actuelle :** ce script créerait une base de test sur le serveur PostgreSQL PROD. Pour la production locale, la restauration PostgreSQL a été validée manuellement dans un conteneur totalement indépendant et sans réseau :

```powershell
docker run -d --rm --name tb-prod-restore-test --network none -e POSTGRES_PASSWORD=temporary-test-only postgres:18@sha256:3a4264520e121176619f54ff867d12774bc81e95e7b84db58d63bccdb6144b81
docker exec tb-prod-restore-test pg_isready -U postgres

$dump = Get-ChildItem '.local-data/backups/prod/database-*.dump' | Sort-Object Name -Descending | Select-Object -First 1
docker cp $dump.FullName tb-prod-restore-test:/tmp/prod-backup.dump
docker exec tb-prod-restore-test createdb -U postgres tb_restore_prod
docker exec tb-prod-restore-test pg_restore -U postgres -d tb_restore_prod --no-owner --no-acl --exit-on-error /tmp/prod-backup.dump
docker exec tb-prod-restore-test psql -U postgres -d tb_restore_prod -c 'SELECT current_database();'
```

Ces commandes ne publient aucun port et ne montent aucun volume du projet. Elles supposent que le nom `tb-prod-restore-test` est disponible. Après vérification, arrêter et supprimer automatiquement le conteneur temporaire :

```powershell
docker stop tb-prod-restore-test
```

Pour le stockage PROD, extraire la paire d'archive correspondante dans un dossier neuf sous `.local-data/restore-tests/`, puis comparer les empreintes SHA-256 des fichiers originaux et restaurés. Ne jamais extraire une archive dans le stockage actif. Ne restaurer que des archives **de confiance**.

## Validation réalisée le 4 novembre 2026

- Sauvegardes DEV et PROD produites et lues avec succès.
- Restauration PostgreSQL avec une table et trois lignes fictives dans une base DEV indépendante.
- Sauvegarde copiée sur Windows puis restaurée dans une nouvelle base DEV.
- Restauration PostgreSQL PROD dans un conteneur temporaire isolé.
- Extraction du stockage DEV et PROD dans des dossiers séparés et comparaison positive d'empreintes SHA-256.
- Exécution réussie des scripts de sauvegarde DEV/PROD et du script de restauration DEV.

## Limites actuelles et étapes ultérieures

- Les archives sont enregistrées sur **le même PC** que les données ; elles ne protègent pas contre une panne ou une perte de cette machine.
- Aucune rotation, rétention, copie externe ou exécution planifiée n'est encore configurée.
- Les archives PostgreSQL et fichiers sont produites successivement : si l'application modifie les deux simultanément, leur cohérence fonctionnelle n'est pas garantie par ce mécanisme seul.
- Le contrôle `pg_restore -l` valide la lisibilité de l'archive, **pas** une restauration complète ; d'où la nécessité des tests isolés.
- Le script de restauration DEV conserve sa base et ses fichiers temporaires jusqu'au nettoyage manuel.
- Le test de restauration PROD reste une procédure manuelle isolée ; le script de restauration générique doit être revu avant toute utilisation contre PostgreSQL PROD.
- La restauration complète d'un service après incident (arrêt, remise en place, migrations éventuelles, vérifications applicatives) n'est pas encore automatisée.
- Sur le Raspberry Pi, les chemins, permissions du compte applicatif (`UID 10001`), destination externe des sauvegardes, automatisation et restauration réelle seront définis au chantier de déploiement, **sans perturber la V1**.

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("dev")]
    [string]$Target
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$tarExe = Join-Path $env:SystemRoot "System32\tar.exe"

Push-Location $projectRoot

$tempDump = $null

try {
    $composeArgs = @(
        "compose",
        "--env-file", ".env.$Target",
        "-f", "compose.yaml",
        "-f", "compose.$Target.yaml"
    )

    $backupDir = Join-Path $projectRoot ".local-data/backups/$Target"

    if (-not (Test-Path -LiteralPath $backupDir)) {
        throw "Aucun dossier de sauvegarde pour $Target."
    }

    # Rechercher la sauvegarde complete la plus recente
    $backup = Get-ChildItem -LiteralPath $backupDir -Filter "database-*.dump" -File |
        Sort-Object Name -Descending |
        Where-Object {
            $id = $_.BaseName.Substring("database-".Length)
            Test-Path -LiteralPath (Join-Path $backupDir "storage-$id.tar.gz")
        } |
        Select-Object -First 1

    if ($null -eq $backup) {
        throw "Aucune paire de sauvegardes complete trouvee."
    }

    $backupId = $backup.BaseName.Substring("database-".Length)

    $dumpPath = $backup.FullName
    $archivePath = Join-Path $backupDir "storage-$backupId.tar.gz"

    # Generer des destinations independantes
    $runId = Get-Date -Format "yyyyMMddHHmmssfff"
    $restoreDb = "tb_restore_${Target}_$runId"

    $restoreDir = Join-Path $projectRoot ".local-data/restore-tests/$Target-$runId"
    $tempDump = "/tmp/restore-$runId.dump"

    Write-Host "Test de restauration Team Baguette - $Target"
    Write-Host "Sauvegarde selectionnee : $backupId"

    # 1. Copier et verifier l'archive PostgreSQL
    Write-Host "[1/4] Verification PostgreSQL..."

    & docker @composeArgs cp $dumpPath "db:$tempDump"

    if ($LASTEXITCODE -ne 0) {
        throw "Impossible de copier le dump."
    }

    & docker @composeArgs exec -T db pg_restore -l $tempDump | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "Archive PostgreSQL invalide."
    }

    # 2. Restaurer les fichiers dans un dossier separe
    Write-Host "[2/4] Restauration du stockage..."

    $entries = & $tarExe -tzf $archivePath

    if ($LASTEXITCODE -ne 0) {
        throw "Archive de stockage invalide."
    }

    foreach ($entry in $entries) {
        if (
            $entry -notmatch '^storage(/|$)' -or
            $entry -match '(^|/)\.\.(/|$)'
        ) {
            throw "Chemin inattendu dans l'archive : $entry"
        }
    }

    New-Item -ItemType Directory -Force -Path $restoreDir | Out-Null

    & $tarExe -xzf $archivePath -C $restoreDir

    if ($LASTEXITCODE -ne 0) {
        throw "Echec de la restauration des fichiers."
    }

    # 3. Creer une nouvelle base de test
    Write-Host "[3/4] Creation de la base de restauration..."

    $createCommand = 'createdb -U "$POSTGRES_USER" ' + $restoreDb

    & docker @composeArgs exec -T db sh -c $createCommand

    if ($LASTEXITCODE -ne 0) {
        throw "Impossible de creer la base de test."
    }

    # 4. Restaurer PostgreSQL dans cette nouvelle base
    Write-Host "[4/4] Restauration PostgreSQL..."

    $restoreCommand = 'pg_restore -U "$POSTGRES_USER" --exit-on-error -d ' +
        $restoreDb + ' ' + $tempDump

    & docker @composeArgs exec -T db sh -c $restoreCommand

    if ($LASTEXITCODE -ne 0) {
        throw "Echec de la restauration PostgreSQL."
    }

    Write-Host ""
    Write-Host "RESTAURATION DE TEST TERMINEE"
    Write-Host "Base restauree : $restoreDb"
    Write-Host "Fichiers restaures : $restoreDir"
    Write-Host ""
    Write-Host "Les donnees originales n'ont pas ete remplacees."
}
finally {
    if ($null -ne $tempDump) {
        & docker @composeArgs exec -T db rm -f $tempDump 2>$null | Out-Null
    }

    Pop-Location
}

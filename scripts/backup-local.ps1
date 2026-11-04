param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("dev", "prod")]
    [string]$Target
)

$ErrorActionPreference = "Stop"

# Utiliser le tar natif de Windows
$tarExe = Join-Path $env:SystemRoot "System32\tar.exe"

# Toujours travailler depuis la racine du projet
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot

try {
    $composeArgs = @(
        "compose",
        "--env-file", ".env.$Target",
        "-f", "compose.yaml",
        "-f", "compose.$Target.yaml"
    )

    # Recuperer le chemin reel du stockage depuis Docker Compose
    $configJson = & docker @composeArgs config --format json
    if ($LASTEXITCODE -ne 0) {
        throw "Configuration Docker Compose invalide."
    }

    $config = ($configJson -join "`n") | ConvertFrom-Json

    $mount = @(
        $config.services.backend.volumes |
        Where-Object {
            $_.type -eq "bind" -and
            $_.target -eq "/data/storage"
        }
    )

    if ($mount.Count -ne 1) {
        throw "Montage du stockage introuvable ou ambigu."
    }

    $storagePath = $mount[0].source

    if (-not (Test-Path -LiteralPath $storagePath -PathType Container)) {
        throw "Dossier de stockage introuvable : $storagePath"
    }

    # Dossier et noms des sauvegardes
    $backupDir = Join-Path $projectRoot ".local-data/backups/$Target"
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss-fff"

    $dumpName = "database-$timestamp.dump"
    $archiveName = "storage-$timestamp.tar.gz"

    $dumpPath = Join-Path $backupDir $dumpName
    $archivePath = Join-Path $backupDir $archiveName

    $containerDump = "/tmp/$dumpName"
    $containerVerify = "/tmp/verify-$dumpName"

    Write-Host "Sauvegarde Team Baguette - $Target"

    try {
        # 1. Sauvegarder PostgreSQL
        Write-Host "[1/4] Sauvegarde PostgreSQL..."

        $dumpCommand = 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f ' + $containerDump

        & docker @composeArgs exec -T db sh -c $dumpCommand

        if ($LASTEXITCODE -ne 0) {
            throw "Echec de pg_dump."
        }

        # 2. Copier et verifier le dump local
        Write-Host "[2/4] Verification de PostgreSQL..."

        & docker @composeArgs cp "db:$containerDump" $dumpPath

        if ($LASTEXITCODE -ne 0) {
            throw "Echec de la copie du dump."
        }

        & docker @composeArgs cp $dumpPath "db:$containerVerify"

        if ($LASTEXITCODE -ne 0) {
            throw "Echec de la verification de la copie."
        }

        & docker @composeArgs exec -T db pg_restore -l $containerVerify | Out-Null

        if ($LASTEXITCODE -ne 0) {
            throw "Archive PostgreSQL illisible."
        }

        # 3. Archiver le stockage persistant
        Write-Host "[3/4] Sauvegarde du stockage..."

        $storageParent = Split-Path -Parent $storagePath
        $storageFolder = Split-Path -Leaf $storagePath

        & $tarExe -czf $archivePath -C $storageParent $storageFolder

        if ($LASTEXITCODE -ne 0) {
            throw "Echec de l'archivage du stockage."
        }

        # 4. Verifier l'archive de fichiers
        Write-Host "[4/4] Verification de l'archive..."

        & $tarExe -tzf $archivePath | Out-Null

        if ($LASTEXITCODE -ne 0) {
            throw "Archive de stockage illisible."
        }

        Write-Host ""
        Write-Host "SAUVEGARDE TERMINEE AVEC SUCCES"
        Write-Host "PostgreSQL : $dumpPath"
        Write-Host "Stockage   : $archivePath"
    }
    finally {
        # Nettoyage des fichiers temporaires du conteneur
        & docker @composeArgs exec -T db rm -f $containerDump $containerVerify | Out-Null
    }
}
finally {
    Pop-Location
}

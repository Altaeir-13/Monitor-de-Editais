[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BackupDirectory,
    [string]$EnvFile = (Join-Path $PSScriptRoot "..\.env.prod"),
    [string]$ComposeFile = (Join-Path $PSScriptRoot "..\docker-compose.prod.yml"),
    [string]$ProjectName = ""
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$containerBackupPath = $null
$compose = $null

try {
    $envFilePath = Resolve-RepositoryPath -Path $EnvFile
    $composeFilePath = Resolve-RepositoryPath -Path $ComposeFile
    $values = Read-DotEnvFile -Path $envFilePath
    $project = Resolve-ComposeProjectName -ProjectName $ProjectName -Values $values

    $postgresUser = Get-RequiredDotEnvValue -Values $values -Name "POSTGRES_USER"
    $postgresDatabase = Get-RequiredDotEnvValue -Values $values -Name "POSTGRES_DB"
    if ($postgresUser -notmatch "^[A-Za-z0-9_]+$" -or $postgresDatabase -notmatch "^[A-Za-z0-9_]+$") {
        throw "PostgreSQL user and database names contain unsupported characters."
    }

    $backupDirectoryPath = [System.IO.Path]::GetFullPath($BackupDirectory)
    if (Test-PathInsideRepository -Path $backupDirectoryPath) {
        throw "BackupDirectory must be outside the repository."
    }
    if (-not (Test-Path -LiteralPath $backupDirectoryPath -PathType Container)) {
        [void](New-Item -ItemType Directory -Path $backupDirectoryPath)
    }

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupPath = Join-Path $backupDirectoryPath "monitor_editais_$timestamp.dump"
    if (Test-Path -LiteralPath $backupPath) {
        throw "Timestamped backup path already exists; no file was overwritten."
    }

    $containerBackupPath = "/tmp/monitor_editais_$timestamp.dump"
    $compose = New-ComposeArgumentList -ProjectName $project -EnvFile $envFilePath -ComposeFile $composeFilePath

    Invoke-CheckedCommand -FilePath "docker" -ArgumentList (
        $compose + @(
            "exec", "-T", "db",
            "pg_dump",
            "--username", $postgresUser,
            "--dbname", $postgresDatabase,
            "--format", "custom",
            "--file", $containerBackupPath
        )
    )
    Invoke-CheckedCommand -FilePath "docker" -ArgumentList (
        $compose + @("cp", "db:$containerBackupPath", $backupPath)
    )

    $backupFile = Get-Item -LiteralPath $backupPath
    if ($backupFile.Length -le 0) {
        throw "Backup file is empty."
    }

    Write-Host "PostgreSQL backup created at $backupPath"
    exit 0
}
catch {
    [Console]::Error.WriteLine("PostgreSQL backup failed: $($_.Exception.Message)")
    exit 1
}
finally {
    if ($null -ne $containerBackupPath -and $null -ne $compose) {
        & docker @($compose + @("exec", "-T", "db", "rm", "-f", $containerBackupPath))
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Could not remove the task-created temporary file from the db container."
        }
    }
}

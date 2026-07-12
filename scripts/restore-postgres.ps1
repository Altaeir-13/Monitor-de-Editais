[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BackupPath,
    [Parameter(Mandatory = $true)]
    [string]$TargetDatabase,
    [Parameter(Mandatory = $true)]
    [string]$ConfirmDatabase,
    [switch]$ReplaceExisting,
    [string]$EnvFile = (Join-Path $PSScriptRoot "..\.env.prod"),
    [string]$ComposeFile = (Join-Path $PSScriptRoot "..\docker-compose.prod.yml"),
    [string]$ProjectName = ""
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

$containerBackupPath = $null
$compose = $null

try {
    $backupFilePath = [System.IO.Path]::GetFullPath($BackupPath)
    if (-not (Test-Path -LiteralPath $backupFilePath -PathType Leaf)) {
        throw "Backup file not found."
    }
    if ($TargetDatabase -ne $ConfirmDatabase) {
        throw "ConfirmDatabase must exactly match TargetDatabase."
    }
    if ($TargetDatabase -notmatch "^[A-Za-z0-9_]+$") {
        throw "TargetDatabase contains unsupported characters."
    }

    $envFilePath = Resolve-RepositoryPath -Path $EnvFile
    $composeFilePath = Resolve-RepositoryPath -Path $ComposeFile
    $values = Read-DotEnvFile -Path $envFilePath
    $project = Resolve-ComposeProjectName -ProjectName $ProjectName -Values $values
    $postgresUser = Get-RequiredDotEnvValue -Values $values -Name "POSTGRES_USER"
    $primaryDatabase = Get-RequiredDotEnvValue -Values $values -Name "POSTGRES_DB"
    if ($TargetDatabase -eq $primaryDatabase) {
        throw "Refusing to restore into the configured primary database; use a separate controlled database."
    }
    if ($postgresUser -notmatch "^[A-Za-z0-9_]+$") {
        throw "POSTGRES_USER contains unsupported characters."
    }

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $containerBackupPath = "/tmp/monitor_restore_$timestamp.dump"
    $compose = New-ComposeArgumentList -ProjectName $project -EnvFile $envFilePath -ComposeFile $composeFilePath

    Invoke-CheckedCommand -FilePath "docker" -ArgumentList (
        $compose + @("cp", $backupFilePath, "db:$containerBackupPath")
    )
    Invoke-CheckedCommand -FilePath "docker" -ArgumentList (
        $compose + @("exec", "-T", "db", "pg_restore", "--list", $containerBackupPath)
    )

    $restoreArguments = $compose + @(
        "exec", "-T", "db",
        "pg_restore",
        "--exit-on-error",
        "--no-owner",
        "--no-privileges",
        "--username", $postgresUser,
        "--dbname", $TargetDatabase
    )
    if ($ReplaceExisting) {
        $restoreArguments += @("--clean", "--if-exists")
    }
    $restoreArguments += $containerBackupPath

    Invoke-CheckedCommand -FilePath "docker" -ArgumentList $restoreArguments

    Write-Host "PostgreSQL restore completed for the explicitly confirmed target database."
    exit 0
}
catch {
    [Console]::Error.WriteLine("PostgreSQL restore failed: $($_.Exception.Message)")
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

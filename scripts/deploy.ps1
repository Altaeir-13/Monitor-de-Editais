[CmdletBinding()]
param(
    [string]$EnvFile = (Join-Path $PSScriptRoot "..\.env.prod"),
    [string]$ComposeFile = (Join-Path $PSScriptRoot "..\docker-compose.prod.yml"),
    [string]$ProjectName = "",
    [int]$WaitTimeoutSeconds = 180
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

try {
    $envFilePath = Resolve-RepositoryPath -Path $EnvFile
    $composeFilePath = Resolve-RepositoryPath -Path $ComposeFile
    $values = Read-DotEnvFile -Path $envFilePath
    $project = Resolve-ComposeProjectName -ProjectName $ProjectName -Values $values

    $required = @(
        "STAGING_DOMAIN",
        "TLS_CERT_DIRECTORY",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
        "ENVIRONMENT",
        "SECRET_KEY",
        "API_ROOT_PATH",
        "BACKEND_CORS_ORIGINS",
        "CRAWLER_SCHEDULER_ENABLED",
        "UVICORN_WORKERS"
    )
    foreach ($name in $required) {
        [void](Get-RequiredDotEnvValue -Values $values -Name $name)
    }

    $secretKey = [string]$values["SECRET_KEY"]
    $postgresPassword = [string]$values["POSTGRES_PASSWORD"]
    if ($secretKey.Length -lt 32 -or $secretKey.ToLowerInvariant().Contains("change-me")) {
        throw "SECRET_KEY must be a non-placeholder value with at least 32 characters."
    }
    if ($postgresPassword.Length -lt 12 -or $postgresPassword.ToLowerInvariant().Contains("change-me")) {
        throw "POSTGRES_PASSWORD must be a non-placeholder value with at least 12 characters."
    }

    if ($postgresPassword -notmatch "^[A-Za-z0-9._~-]+$") {
        throw "POSTGRES_PASSWORD must use only RFC 3986 unreserved characters."
    }
    foreach ($databaseName in @("POSTGRES_USER", "POSTGRES_DB")) {
        if ([string]$values[$databaseName] -notmatch "^[A-Za-z0-9_]+$") {
            throw "$databaseName contains unsupported characters."
        }
    }

    $domain = [string]$values["STAGING_DOMAIN"]
    if ($domain -match "(^localhost$|example\.(com|org|net)$)") {
        throw "STAGING_DOMAIN must be replaced with the real staging domain."
    }
    if ([string]$values["ENVIRONMENT"] -notin @("staging", "production")) {
        throw "ENVIRONMENT must be staging or production."
    }
    if ([string]$values["API_ROOT_PATH"] -ne "/api") {
        throw "API_ROOT_PATH must be /api for the documented topology."
    }
    if ([string]$values["CRAWLER_SCHEDULER_ENABLED"] -ne "false") {
        throw "CRAWLER_SCHEDULER_ENABLED must remain false during initial deployment."
    }
    if ([string]$values["UVICORN_WORKERS"] -ne "1") {
        throw "UVICORN_WORKERS must be 1 for the initial deployment."
    }

    try {
        $corsOrigins = @(([string]$values["BACKEND_CORS_ORIGINS"]) | ConvertFrom-Json)
    }
    catch {
        throw "BACKEND_CORS_ORIGINS must be a JSON array."
    }
    if ($corsOrigins -notcontains "https://$domain") {
        throw "BACKEND_CORS_ORIGINS must contain the HTTPS staging origin."
    }

    $tlsDirectory = Resolve-RepositoryPath -Path ([string]$values["TLS_CERT_DIRECTORY"])
    foreach ($certificateFile in @("fullchain.pem", "privkey.pem")) {
        if (-not (Test-Path -LiteralPath (Join-Path $tlsDirectory $certificateFile) -PathType Leaf)) {
            throw "TLS certificate files are missing from TLS_CERT_DIRECTORY."
        }
    }

    $compose = New-ComposeArgumentList -ProjectName $project -EnvFile $envFilePath -ComposeFile $composeFilePath
    Invoke-CheckedCommand -FilePath "docker" -ArgumentList ($compose + @("config", "--quiet"))
    Invoke-CheckedCommand -FilePath "docker" -ArgumentList ($compose + @("build"))
    Invoke-CheckedCommand -FilePath "docker" -ArgumentList (
        $compose + @("up", "-d", "--wait", "--wait-timeout", [string]$WaitTimeoutSeconds)
    )
    Invoke-CheckedCommand -FilePath "docker" -ArgumentList ($compose + @("ps"))

    Write-Host "Staging stack is healthy. Run the admin bootstrap, seed, and smoke test as separate controlled steps."
    exit 0
}
catch {
    [Console]::Error.WriteLine("Deployment failed: $($_.Exception.Message)")
    exit 1
}

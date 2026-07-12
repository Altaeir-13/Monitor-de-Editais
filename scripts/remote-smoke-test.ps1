[CmdletBinding()]
param(
    [string]$EnvFile = (Join-Path $PSScriptRoot "..\.env.prod"),
    [string]$ComposeFile = (Join-Path $PSScriptRoot "..\docker-compose.prod.yml"),
    [string]$ProjectName = "",
    [switch]$AllowHttp
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "common.ps1")

try {
    $envFilePath = Resolve-RepositoryPath -Path $EnvFile
    $composeFilePath = Resolve-RepositoryPath -Path $ComposeFile
    $values = Read-DotEnvFile -Path $envFilePath
    $project = Resolve-ComposeProjectName -ProjectName $ProjectName -Values $values

    $baseUrl = $env:SMOKE_BASE_URL
    if ([string]::IsNullOrWhiteSpace($baseUrl)) {
        $baseUrl = Get-RequiredDotEnvValue -Values $values -Name "SMOKE_BASE_URL"
    }
    if (-not $AllowHttp -and -not $baseUrl.StartsWith("https://", [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "SMOKE_BASE_URL must use HTTPS."
    }

    $adminEmail = $env:SMOKE_ADMIN_EMAIL
    if ([string]::IsNullOrWhiteSpace($adminEmail)) {
        $adminEmail = Get-RequiredDotEnvValue -Values $values -Name "SMOKE_ADMIN_EMAIL"
    }
    if ([string]::IsNullOrWhiteSpace($env:SMOKE_ADMIN_PASSWORD)) {
        throw "SMOKE_ADMIN_PASSWORD must be supplied through the process environment."
    }

    $apiPrefix = if ($values.Contains("SMOKE_API_PREFIX")) { [string]$values["SMOKE_API_PREFIX"] } else { "/api" }
    $expectOpenApi = if ($values.Contains("SMOKE_EXPECT_OPENAPI")) { [string]$values["SMOKE_EXPECT_OPENAPI"] } else { "false" }
    $verifyTls = if ($values.Contains("SMOKE_TLS_VERIFY")) { [string]$values["SMOKE_TLS_VERIFY"] } else { "true" }
    $timeout = if ($values.Contains("SMOKE_TIMEOUT")) { [string]$values["SMOKE_TIMEOUT"] } else { "10" }

    $env:SMOKE_BASE_URL = $baseUrl
    $env:SMOKE_API_PREFIX = $apiPrefix
    $env:SMOKE_ADMIN_EMAIL = $adminEmail
    $env:SMOKE_EXPECT_OPENAPI = $expectOpenApi
    $env:SMOKE_TLS_VERIFY = $verifyTls
    $env:SMOKE_TIMEOUT = $timeout

    $compose = New-ComposeArgumentList -ProjectName $project -EnvFile $envFilePath -ComposeFile $composeFilePath
    $passThroughEnvironment = @(
        "-e", "SMOKE_BASE_URL",
        "-e", "SMOKE_API_PREFIX",
        "-e", "SMOKE_ADMIN_EMAIL",
        "-e", "SMOKE_ADMIN_PASSWORD",
        "-e", "SMOKE_EXPECT_OPENAPI",
        "-e", "SMOKE_TLS_VERIFY",
        "-e", "SMOKE_TIMEOUT"
    )
    Invoke-CheckedCommand -FilePath "docker" -ArgumentList (
        $compose + @("exec", "-T") + $passThroughEnvironment + @(
            "backend", "python", "scripts/smoke_test.py"
        )
    )

    Write-Host "Remote smoke test completed successfully."
    exit 0
}
catch {
    [Console]::Error.WriteLine("Remote smoke test failed: $($_.Exception.Message)")
    exit 1
}

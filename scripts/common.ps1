Set-StrictMode -Version Latest

function Get-RepositoryRoot {
    return [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
}

function Resolve-RepositoryPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }

    return [System.IO.Path]::GetFullPath((Join-Path (Get-RepositoryRoot) $Path))
}

function Read-DotEnvFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Environment file not found."
    }

    $values = [ordered]@{}
    foreach ($line in Get-Content -LiteralPath $Path -Encoding UTF8) {
        $trimmed = $line.Trim()
        if ($trimmed.Length -eq 0 -or $trimmed.StartsWith("#")) {
            continue
        }

        $separator = $trimmed.IndexOf("=")
        if ($separator -lt 1) {
            throw "Invalid line in environment file."
        }

        $name = $trimmed.Substring(0, $separator).Trim()
        $value = $trimmed.Substring($separator + 1).Trim()
        $values[$name] = $value
    }

    return $values
}

function Get-RequiredDotEnvValue {
    param(
        [Parameter(Mandatory = $true)]
        [System.Collections.IDictionary]$Values,
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    if (-not $Values.Contains($Name) -or [string]::IsNullOrWhiteSpace([string]$Values[$Name])) {
        throw "$Name is required."
    }

    return [string]$Values[$Name]
}

function Resolve-ComposeProjectName {
    param(
        [string]$ProjectName,
        [Parameter(Mandatory = $true)]
        [System.Collections.IDictionary]$Values
    )

    if ([string]::IsNullOrWhiteSpace($ProjectName)) {
        $ProjectName = Get-RequiredDotEnvValue -Values $Values -Name "COMPOSE_PROJECT_NAME"
    }

    if ($ProjectName -cnotmatch "^[a-z0-9][a-z0-9_-]{1,62}$") {
        throw "Compose project name must use lowercase letters, digits, hyphens, or underscores."
    }

    return $ProjectName
}

function New-ComposeArgumentList {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ProjectName,
        [Parameter(Mandatory = $true)]
        [string]$EnvFile,
        [Parameter(Mandatory = $true)]
        [string]$ComposeFile
    )

    return @(
        "compose",
        "--project-name", $ProjectName,
        "--env-file", $EnvFile,
        "-f", $ComposeFile
    )
}

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [Parameter(Mandatory = $true)]
        [string[]]$ArgumentList
    )

    & $FilePath @ArgumentList
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "$FilePath failed with exit code $exitCode."
    }
}

function Test-PathInsideRepository {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $repositoryRoot = (Get-RepositoryRoot).TrimEnd([System.IO.Path]::DirectorySeparatorChar)
    $candidate = [System.IO.Path]::GetFullPath($Path).TrimEnd([System.IO.Path]::DirectorySeparatorChar)
    $prefix = $repositoryRoot + [System.IO.Path]::DirectorySeparatorChar

    return $candidate.Equals($repositoryRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
        $candidate.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)
}

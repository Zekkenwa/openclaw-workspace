[CmdletBinding()]
param([switch]$VerifyOnly)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$requiredVersion = [version]'2026.11.5'
$versionText = (& openclaw --version 2>&1 | Out-String)
if ($LASTEXITCODE -ne 0 -or $versionText -notmatch '(\d{4}\.\d+\.\d+)') {
    throw 'OpenClaw CLI is unavailable or its version could not be determined.'
}
$currentVersion = [version]$Matches[1]
if ($currentVersion -lt $requiredVersion) {
    throw "OpenClaw $requiredVersion or newer is required; found $currentVersion. Update this device before applying shared capabilities."
}

function Test-EnvPresent([string[]]$Names) {
    foreach ($name in $Names) {
        $value = [Environment]::GetEnvironmentVariable($name, 'Process')
        if ([string]::IsNullOrWhiteSpace($value)) { $value = [Environment]::GetEnvironmentVariable($name, 'User') }
        if ([string]::IsNullOrWhiteSpace($value)) { $value = [Environment]::GetEnvironmentVariable($name, 'Machine') }
        if (-not [string]::IsNullOrWhiteSpace($value)) { return $name }
    }
    return $null
}

$gutsaiEnv = Test-EnvPresent @('GUTSAI_API_KEY', 'OPENAI_API_KEY')
$geminiEnv = Test-EnvPresent @('GEMINI_API_KEY', 'GOOGLE_API_KEY')
Write-Output ('GutsAI credential environment: ' + $(if ($gutsaiEnv) { "$gutsaiEnv present" } else { 'missing' }))
Write-Output ('Gemini credential environment: ' + $(if ($geminiEnv) { "$geminiEnv present" } else { 'missing' }))

if ($VerifyOnly) {
    if (-not $gutsaiEnv -or -not $geminiEnv) { exit 2 }
    & openclaw config validate
    exit $LASTEXITCODE
}

if (-not $gutsaiEnv) {
    throw 'Missing GUTSAI_API_KEY (preferred) or OPENAI_API_KEY. Add it to the Gateway process environment or ~/.openclaw/.env; never to the workspace repository.'
}
if (-not $geminiEnv) {
    throw 'Missing GEMINI_API_KEY or GOOGLE_API_KEY. Add it to the Gateway process environment or ~/.openclaw/.env; never to the workspace repository.'
}

$providerPath = Join-Path $repoRoot 'capabilities\gutsai-provider.json'
if (-not (Test-Path $providerPath)) { throw "Capability manifest missing: $providerPath" }
$provider = Get-Content $providerPath -Raw | ConvertFrom-Json
$batchPath = Join-Path ([IO.Path]::GetTempPath()) ("openclaw-capabilities-{0}.json" -f [guid]::NewGuid())
$batch = ,([pscustomobject]@{ path = 'models.providers.custom-api-gutsai-id'; value = $provider })
[IO.File]::WriteAllText($batchPath, (ConvertTo-Json -InputObject $batch -Depth 30), [Text.UTF8Encoding]::new($false))

# Configuration writes are idempotent. Credentials are referenced by environment name only.
try {
    & openclaw config set --batch-file $batchPath --merge
    if ($LASTEXITCODE -ne 0) { throw 'Failed to install the shared GutsAI provider catalog.' }
} finally {
    Remove-Item $batchPath -Force -ErrorAction SilentlyContinue
}
& openclaw config set models.providers.custom-api-gutsai-id.apiKey --ref-provider default --ref-source env --ref-id $gutsaiEnv
if ($LASTEXITCODE -ne 0) { throw 'Failed to bind the GutsAI provider credential SecretRef.' }
& openclaw config set memory.search.provider gemini
if ($LASTEXITCODE -ne 0) { throw 'Failed to select Gemini for memory search.' }
& openclaw config set memory.search.remote.apiKey --ref-provider default --ref-source env --ref-id $geminiEnv
if ($LASTEXITCODE -ne 0) { throw 'Failed to bind the Gemini memory credential SecretRef.' }

& openclaw config validate
if ($LASTEXITCODE -ne 0) { throw 'OpenClaw configuration validation failed.' }
& openclaw doctor --lint
if ($LASTEXITCODE -ne 0) { Write-Warning 'doctor --lint reported findings; review them before relying on this device.' }

Write-Output 'Shared capability configuration applied. Start a new session (or restart the Gateway if requested by OpenClaw) to load it.'

[CmdletBinding()]
param(
    [ValidateSet('start', 'push', 'status')]
    [string]$Mode = 'status',

    [string]$Message = 'Sync shared OpenClaw workspace'
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$sharedPaths = @(
    '.gitignore',
    'AGENTS.md',
    'HEARTBEAT.md',
    'IDENTITY.md',
    'MEMORY.md',
    'SOUL.md',
    'TOOLS.md',
    'USER.md',
    'memory',
    'skills',
    'scripts'
)

function Invoke-Git {
    param([string[]]$GitArgs)
    & git @GitArgs
    if ($LASTEXITCODE -ne 0) { throw "git $($GitArgs -join ' ') failed." }
}

function Get-SharedChanges {
    $changes = @()
    foreach ($path in $sharedPaths) {
        $changes += @(git status --porcelain -- $path)
    }
    return @($changes | Where-Object { $_ })
}

switch ($Mode) {
    'status' {
        Invoke-Git -GitArgs @('status', '--short', '--branch')
        $changes = Get-SharedChanges
        if ($changes.Count -eq 0) { Write-Output 'No uncommitted shared-workspace changes.' }
        else { $changes }
    }

    'start' {
        $changes = Get-SharedChanges
        if ($changes.Count -gt 0) {
            Write-Warning 'Shared files have local changes. Not pulling, to avoid overwriting or creating a conflict. Run push mode first.'
            $changes
            exit 2
        }

        Invoke-Git -GitArgs @('fetch', 'origin')
        $aheadBehind = git rev-list --left-right --count 'HEAD...@{upstream}'
        if ($LASTEXITCODE -ne 0) { throw 'Unable to compare the local branch with its upstream.' }
        $counts = $aheadBehind -split '\s+'
        $ahead = [int]$counts[0]
        $behind = [int]$counts[1]

        if ($ahead -gt 0) {
            throw "Local branch is $ahead commit(s) ahead of origin. Push it before starting a session."
        }
        if ($behind -gt 0) {
            Invoke-Git -GitArgs @('pull', '--ff-only', 'origin', 'main')
            Write-Output "Pulled $behind commit(s) from origin/main."
        } else {
            Write-Output 'Already up to date with origin/main.'
        }
    }

    'push' {
        $changes = Get-SharedChanges
        if ($changes.Count -eq 0) {
            Write-Output 'No shared-workspace changes to commit or push.'
            exit 0
        }

        $existingSharedPaths = @($sharedPaths | Where-Object { Test-Path $_ })
        Invoke-Git -GitArgs (@('add', '--') + $existingSharedPaths)
        & git diff --cached --quiet
        if ($LASTEXITCODE -eq 0) {
            Write-Output 'No staged shared-workspace changes to commit or push.'
            exit 0
        }
        if ($LASTEXITCODE -gt 1) { throw 'Unable to inspect staged changes.' }

        Invoke-Git -GitArgs @('commit', '-m', $Message)
        Invoke-Git -GitArgs @('push', 'origin', 'main')
        Write-Output 'Committed and pushed shared-workspace changes.'
    }
}

param(
    [string]$CommitMessage = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not (Test-Path ".git")) {
    throw "This directory is not a Git repository: $repoRoot"
}

$status = git status --porcelain
if (-not $status) {
    Write-Output "No changes to publish."
    exit 0
}

if (-not $CommitMessage) {
    $date = Get-Date -Format "yyyy-MM-dd"
    $CommitMessage = "Update daily digest for $date"
}

git add reports site
if (-not (git diff --cached --name-only)) {
    Write-Output "No report or site changes to publish."
    exit 0
}

git commit -m $CommitMessage

$remote = git remote
if (-not $remote) {
    Write-Output "Committed locally, but no Git remote is configured yet."
    exit 0
}

$branch = git branch --show-current
git push origin $branch
Write-Output "Published changes to origin/$branch."

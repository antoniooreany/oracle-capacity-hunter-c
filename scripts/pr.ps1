param(
    [string]$BaseBranch = "develop",
    [string]$Title = "Feature: Streamlit UI and OCI config alignment"
)

$ErrorActionPreference = "Stop"

# 1. Определяем текущую ветку
$CurrentBranch = git rev-parse --abbrev-ref HEAD

if ($CurrentBranch -eq $BaseBranch) {
    Write-Host "Current branch is the base branch ($BaseBranch), nothing to PR." -ForegroundColor Yellow
    exit 1
}

Write-Host "Creating PR from '$CurrentBranch' into '$BaseBranch'..." -ForegroundColor Cyan

# 2. Коммиты и изменённые файлы
$CommitsRange = "$BaseBranch..$CurrentBranch"
$CommitsList = git log --oneline $CommitsRange
$ChangedFiles = git diff --name-only "$BaseBranch...$CurrentBranch"

if (-not $ChangedFiles) {
    Write-Host "No changes between $BaseBranch and $CurrentBranch, nothing to PR." -ForegroundColor Yellow
    exit 1
}

$ChangesLines = $ChangedFiles | ForEach-Object { "- $_" } | Out-String

# 3. Стандартный Markdown‑body
$Body = @"
## Summary

Introduce changes from branch `$CurrentBranch` into `$BaseBranch`. This PR is intended to be further refined by the docs-assistant workflow (Code-to-Docs) based on the actual diff and file set.

## Changes

$ChangesLines
## Commits

"@

param(
    [string]$BaseBranch = "develop",
    [string]$Title = "feat(ui): Streamlit UI over CapacityHunter"
)

$ErrorActionPreference = "Stop"

# 1. Текущая ветка
$CurrentBranch = git rev-parse --abbrev-ref HEAD

if ($CurrentBranch -eq $BaseBranch) {
    Write-Host "Current branch is the base branch ($BaseBranch), nothing to PR." -ForegroundColor Yellow
    exit 1
}

Write-Host "Using branch '$CurrentBranch' against base '$BaseBranch'..." -ForegroundColor Cyan

# 2. Ищем открытый PR для этой ветки
try {
    $ExistingPrJson = gh pr list `
        --base $BaseBranch `
        --head $CurrentBranch `
        --state open `
        --json number `
        --limit 1
} catch {
    Write-Host "gh pr list failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

$ExistingPr = $null
if ($ExistingPrJson) {
    $ExistingPr = $ExistingPrJson | ConvertFrom-Json
}

# 3. Коммиты и изменённые файлы
$CommitsRange = "$BaseBranch..$CurrentBranch"
$CommitsList = git log --oneline $CommitsRange
$ChangedFiles = git diff --name-only "$BaseBranch...$CurrentBranch"

if (-not $ChangedFiles) {
    Write-Host "No changes between $BaseBranch and $CurrentBranch, nothing to PR." -ForegroundColor Yellow
    exit 1
}

$ChangesLines = $ChangedFiles | ForEach-Object { "- $_" } | Out-String

# 4. Стандартный Markdown-body
$Body = @"
## Summary

Introduce changes from branch $CurrentBranch into $BaseBranch.

## Changes

$ChangesLines
## Commits

$CommitsList

## Risks

$RisksLines
## Config

$ConfigLines
## Testing

$TestingLines
## Notes

$NotesLines

_Last updated by scripts/pr.ps1 at $Timestamp._
"@

# 5. Если PR уже есть — обновляем, иначе создаём
if ($ExistingPr -and $ExistingPr.number) {
    $PrNumber = $ExistingPr.number
    Write-Host "Open PR #$PrNumber found for branch '$CurrentBranch'. Updating it..." -ForegroundColor Green

    gh pr edit $PrNumber `
        --title $Title `
        --body $Body
} else {
    Write-Host "No open PR found for branch '$CurrentBranch'. Creating a new one..." -ForegroundColor Cyan

    gh pr create `
      --base $BaseBranch `
      --head $CurrentBranch `
      --title $Title `
      --body $Body
}

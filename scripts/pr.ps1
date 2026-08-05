param(
    [string]$BaseBranch = "develop",
    [string]$Title = "feat(ui): Streamlit UI over CapacityHunter",
    [string]$Risks = "- Low: see commit history for scope of change.",
    [string]$Config = "- No new required environment variables beyond existing ones.",
    [string]$Testing = "- ruff check, pytest, manual smoke test.",
    [string]$Notes = "-"
)

$ErrorActionPreference = "Stop"

# 1. Текущая ветка
$CurrentBranch = git rev-parse --abbrev-ref HEAD

if ($CurrentBranch -eq $BaseBranch) {
    Write-Host "Current branch is the base branch ($BaseBranch), nothing to PR." -ForegroundColor Yellow
    exit 1
}

Write-Host "Using branch '$CurrentBranch' against base '$BaseBranch'..." -ForegroundColor Cyan

# 2. Ищем ВСЕ открытые PR для этой ветки (не полагаемся на --limit 1)
try {
    $ExistingPrsJson = gh pr list `
        --base $BaseBranch `
        --head $CurrentBranch `
        --state open `
        --json number,title,url
} catch {
    Write-Host "gh pr list failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

$ExistingPrs = @()
if ($ExistingPrsJson) {
    $ExistingPrs = $ExistingPrsJson | ConvertFrom-Json
}

if ($ExistingPrs.Count -gt 1) {
    Write-Host "Found $($ExistingPrs.Count) open PRs for branch '$CurrentBranch' - refusing to guess which to update:" -ForegroundColor Red
    $ExistingPrs | ForEach-Object { Write-Host "  #$($_.number): $($_.title) -> $($_.url)" }
    Write-Host "Close/merge the duplicates manually, then re-run this script." -ForegroundColor Red
    exit 1
}

# 3. Коммиты и изменённые файлы
$CommitsRange = "$BaseBranch..$CurrentBranch"
$CommitsList = git log --oneline $CommitsRange | Out-String
$ChangedFiles = git diff --name-only "$BaseBranch...$CurrentBranch"

if (-not $ChangedFiles) {
    Write-Host "No changes between $BaseBranch and $CurrentBranch, nothing to PR." -ForegroundColor Yellow
    exit 1
}

$ChangesLines = $ChangedFiles | ForEach-Object { "- $_" } | Out-String
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss K"

# 4. Стандартный Markdown-body
$Body = @"
## Summary

Introduce changes from branch $CurrentBranch into $BaseBranch.

## Changes

$ChangesLines
## Commits

$CommitsList
## Risks

$Risks

## Config

$Config

## Testing

$Testing

## Notes

$Notes

_Last updated by scripts/pr.ps1 at $Timestamp._
"@

# 5. Если PR уже есть — обновляем, иначе создаём
if ($ExistingPrs.Count -eq 1) {
    $PrNumber = $ExistingPrs[0].number
    Write-Host "Open PR #$PrNumber found for branch '$CurrentBranch'. Updating it..." -ForegroundColor Green

    gh pr edit $PrNumber `
        --title $Title `
        --body $Body

    Write-Host "Updated: $($ExistingPrs[0].url)" -ForegroundColor Green
} else {
    Write-Host "No open PR found for branch '$CurrentBranch'. Creating a new one..." -ForegroundColor Cyan

    gh pr create `
      --base $BaseBranch `
      --head $CurrentBranch `
      --title $Title `
      --body $Body
}

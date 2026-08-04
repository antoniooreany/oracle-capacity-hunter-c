param(
    [string]$BaseBranch = "develop",
    [string]$Title = "Temporary: will be updated by docs-assistant"
)

$ErrorActionPreference = "Stop"

$CurrentBranch = git rev-parse --abbrev-ref HEAD

if ($CurrentBranch -eq $BaseBranch) {
    Write-Host "Current branch is the base branch ($BaseBranch), nothing to PR." -ForegroundColor Yellow
    exit 1
}

Write-Host "Creating PR from '$CurrentBranch' into '$BaseBranch'..." -ForegroundColor Cyan

$Body = @"
This PR was created locally and is intended to be updated by the docs-assistant workflow.

Please trigger the workflow using `[review-pr]` in a comment to refresh title, body, and labels.
"@

gh pr create `
  --base $BaseBranch `
  --head $CurrentBranch `
  --title $Title `
  --body $Body
  
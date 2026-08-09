param(
    [string]$BaseBranch = "develop"
)

$ErrorActionPreference = "Stop"

# Delegate to the smart Python-based pr-sync tool (installed as pr.exe)
pr.exe --base $BaseBranch

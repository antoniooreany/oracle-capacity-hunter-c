param(
    [string]$BaseBranch = "develop",
    [string]$Model = $null
)

$ErrorActionPreference = "Stop"

# Build arguments for pr.exe
$argsList = @("--base", $BaseBranch)
if ($Model) {
    $argsList += @("--model", $Model)
}

# Delegate to the smart Python-based pr-sync tool (installed as pr.exe)
pr.exe $argsList

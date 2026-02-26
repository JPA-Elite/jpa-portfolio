$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel)
Set-Location $repoRoot

$pythonBin = $null
if (Test-Path ".venv\\Scripts\\python.exe") {
    $pythonBin = ".venv\\Scripts\\python.exe"
} elseif (Test-Path ".venv\\bin\\python") {
    $pythonBin = ".venv\\bin\\python"
} else {
    $pythonBin = "python"
}

Write-Host "pre-commit: running unit tests..."
Remove-Item Env:FLASK_ENV -ErrorAction SilentlyContinue
& $pythonBin -W ignore::DeprecationWarning -m unittest discover -s tests -p "test_*.py"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

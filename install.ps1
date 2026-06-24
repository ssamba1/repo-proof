# RepoProof installer (Windows).
# Writes ONLY inside ~/.claude/skills. No network calls, no credentials.
$ErrorActionPreference = "Stop"

$src = Split-Path -Parent $MyInvocation.MyCommand.Definition
$dest = Join-Path $env:USERPROFILE ".claude\skills"

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Error "Python 3.10+ is required but was not found on PATH."
    exit 1
}

New-Item -ItemType Directory -Force -Path $dest | Out-Null

# Orchestrator skill (carries the Python package the sub-skills invoke).
$proofDest = Join-Path $dest "proof"
if (Test-Path $proofDest) { Remove-Item -Recurse -Force $proofDest }
Copy-Item -Recurse -Force (Join-Path $src "proof") $proofDest

# Sub-skills.
foreach ($skill in @("proof-verify", "proof-demo")) {
    $skillDest = Join-Path $dest $skill
    if (Test-Path $skillDest) { Remove-Item -Recurse -Force $skillDest }
    Copy-Item -Recurse -Force (Join-Path $src "skills\$skill") $skillDest
}

# Drop any compiled caches that may have come along.
Get-ChildItem -Path $proofDest -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "RepoProof installed to $dest"
Write-Host "  - proof, proof-verify, proof-demo"
Write-Host "No credentials stored, no network calls, nothing written outside ~/.claude."
Write-Host "Try it:  python `"$proofDest\run.py`" verify <path-to-a-repo>"

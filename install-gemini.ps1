# RepoProof installer for Gemini CLI (Windows, PowerShell).
# Writes ONLY inside ~/.gemini (or $env:GEMINI_HOME). No network calls, no credentials.
$ErrorActionPreference = "Stop"

$Src = Split-Path -Parent $MyInvocation.MyCommand.Path
$HomeDir = if ($env:GEMINI_HOME) { $env:GEMINI_HOME } else { Join-Path $HOME ".gemini" }
$Pkg = Join-Path $HomeDir "repo-proof"
# Forward slashes: Python accepts them on Windows, and they avoid invalid TOML escape sequences
# (e.g. `\U` in C:\Users...) when the path is written into the command's """ basic string.
$Run = (Join-Path $Pkg "proof\run.py").Replace("\", "/")

if (-not (Get-Command python -ErrorAction SilentlyContinue) -and
    -not (Get-Command python3 -ErrorAction SilentlyContinue)) {
  Write-Error "Python 3.10+ is required but was not found on PATH."
  exit 1
}

$CmdDir = Join-Path $HomeDir "commands\proof"
New-Item -ItemType Directory -Force -Path $Pkg, $CmdDir | Out-Null

# Carry the Python package the commands invoke.
$PkgProof = Join-Path $Pkg "proof"
if (Test-Path $PkgProof) { Remove-Item -Recurse -Force $PkgProof }
Copy-Item -Recurse (Join-Path $Src "proof") $PkgProof
Get-ChildItem -Path $PkgProof -Recurse -Directory -Filter "__pycache__" |
  Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Install the custom commands, rewriting the run.py path placeholder.
foreach ($f in @("verify", "demo")) {
  $tpl = Join-Path $Src "packaging\gemini\commands\proof\$f.toml"
  (Get-Content -Raw $tpl).Replace("@@PROOF_RUN@@", $Run) |
    Set-Content -Encoding utf8 (Join-Path $CmdDir "$f.toml")
}

Write-Host "RepoProof installed for Gemini CLI in $HomeDir"
Write-Host "  - /proof:verify  and  /proof:demo"
Write-Host "No credentials stored, no network calls, nothing written outside $HomeDir."
Write-Host "Try it in Gemini CLI:  /proof:verify <path-to-a-repo>"

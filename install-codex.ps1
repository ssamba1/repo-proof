# RepoProof installer for OpenAI Codex CLI (Windows, PowerShell).
# Writes ONLY inside ~/.codex (or $env:CODEX_HOME). No network calls, no credentials.
$ErrorActionPreference = "Stop"

$Src = Split-Path -Parent $MyInvocation.MyCommand.Path
$HomeDir = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$Pkg = Join-Path $HomeDir "repo-proof"
# Forward slashes work for `python` on Windows and keep the path clean inside the prompt file.
$Run = (Join-Path $Pkg "proof\run.py").Replace("\", "/")

if (-not (Get-Command python -ErrorAction SilentlyContinue) -and
    -not (Get-Command python3 -ErrorAction SilentlyContinue)) {
  Write-Error "Python 3.10+ is required but was not found on PATH."
  exit 1
}

$PromptDir = Join-Path $HomeDir "prompts"
New-Item -ItemType Directory -Force -Path $Pkg, $PromptDir | Out-Null

# Carry the Python package the prompts invoke.
$PkgProof = Join-Path $Pkg "proof"
if (Test-Path $PkgProof) { Remove-Item -Recurse -Force $PkgProof }
Copy-Item -Recurse (Join-Path $Src "proof") $PkgProof
Get-ChildItem -Path $PkgProof -Recurse -Directory -Filter "__pycache__" |
  Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Install the custom prompts (-> /proof-verify, /proof-demo), rewriting the run.py path.
foreach ($f in @("proof-verify", "proof-demo")) {
  $tpl = Join-Path $Src "packaging\codex\prompts\$f.md"
  (Get-Content -Raw $tpl).Replace("@@PROOF_RUN@@", $Run) |
    Set-Content -Encoding utf8 (Join-Path $PromptDir "$f.md")
}

Write-Host "RepoProof installed for Codex CLI in $HomeDir"
Write-Host "  - /proof-verify  and  /proof-demo"
Write-Host "No credentials stored, no network calls, nothing written outside $HomeDir."
Write-Host "Try it in Codex:  /proof-verify <path-to-a-repo>"

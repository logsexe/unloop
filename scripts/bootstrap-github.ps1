param(
  [Parameter(Mandatory=$true)]
  [string]$RepositoryUrl
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path ".\pyproject.toml")) {
  throw "Run this script from the UNLOOP project root (where pyproject.toml lives)."
}

if (-not (Test-Path ".git")) {
  git init
}

git branch -M main
if (git remote get-url origin 2>$null) {
  git remote set-url origin $RepositoryUrl
} else {
  git remote add origin $RepositoryUrl
}

git add .
git commit -m "feat: publish UNLOOP v0.8 guided discovery" 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host "No new commit created (working tree may already be committed)."
}
git push -u origin main

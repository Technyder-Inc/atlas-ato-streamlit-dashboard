# Creates a public GitHub repository and pushes the Atlas dashboard to main.
# Requires GitHub CLI (gh), Git, and a prior `gh auth login` on your machine.
param([string]$RepoName = "atlas-ato-streamlit-dashboard")
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Install Git first." }
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw "Install GitHub CLI (gh) first." }
gh auth status | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Run: gh auth login" }
if (-not (Test-Path ".git")) { git init }
if ((git remote) -contains "origin") { throw "Remote 'origin' already exists. Check it before publishing." }
git add .
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) { git commit -m "Build Atlas ATO Streamlit dashboard with CI/CD" }
git branch -M main
gh repo create $RepoName --public --source . --remote origin --push --description "Atlas ATO Streamlit dashboard - synthetic data demo with CI and CSV refresh"
if ($LASTEXITCODE -ne 0) { throw "GitHub repository creation or push failed." }
Write-Host "Public GitHub repository created and code pushed. Connect it in Streamlit Community Cloud." -ForegroundColor Green

#!/bin/sh
# Requires `gh auth login`, git and gh CLI. Creates a public GitHub repo and pushes main.
set -eu
cd "$(dirname "$0")/.."
repo_name="${1:-atlas-ato-streamlit-dashboard}"
command -v git >/dev/null 2>&1 || { echo 'Git is not installed.' >&2; exit 1; }
command -v gh >/dev/null 2>&1 || { echo 'GitHub CLI (gh) is not installed.' >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo 'First run: gh auth login' >&2; exit 1; }
[ -d .git ] || git init
if git remote get-url origin >/dev/null 2>&1; then
  echo 'An origin remote already exists; check it before publishing.' >&2
  exit 1
fi
git add .
if ! git diff --cached --quiet; then
  git commit -m 'Build Atlas ATO Streamlit dashboard with CI/CD'
fi
git branch -M main
gh repo create "$repo_name" --public --source=. --remote=origin --push \
  --description='Atlas ATO Streamlit dashboard - synthetic data demo with CI and CSV refresh'
printf 'Repository created and pushed. Connect it in Streamlit Community Cloud.\n'

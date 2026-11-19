# Atlas ATO Dashboard

[![CI](https://github.com/Technyder-Inc/atlas-ato-streamlit-dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/Technyder-Inc/atlas-ato-streamlit-dashboard/actions/workflows/ci.yml)

A Streamlit dashboard that tracks the Authority to Operate (ATO) status of a system in one place: assessments, NIST SP 800-53 control progress, ATO documents, POA&M risk items, GitHub delivery, and RHEL 9 remediation guides.

Every number and table on the page is read from CSV files in `data/`. To change what the dashboard shows, edit a CSV and reload.

> **The data in this repository is fictional.** Do not commit real findings, evidence, logs, credentials, or internal hostnames. See [Data and security boundaries](#data-and-security-boundaries).

## Tabs

| Tab | Shows |
| --- | --- |
| Executive Overview | Application summary, authorization status, headline counts |
| Assessments | Assessment schedule, owners, and counts |
| NIST Controls | Control families with progress bars |
| ATO Documents | Document list with approval status |
| POA&M / Risk | Risk register with severity totals |
| GitHub Delivery | Linked issues, pull requests, and validation status |
| Linux Guides | Select a control (for example AU-12) to see its read-only validation commands |

## Run locally

Requires Python 3.12 or later.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

The app opens at <http://localhost:8501>.

## Updating the data

| File | Controls |
| --- | --- |
| `data/applications.csv` | Application name, OS, framework, ATO status |
| `data/assessments.csv` | Assessment counts, schedule, owners |
| `data/control_families.csv` | Control family totals and progress |
| `data/ato_documents.csv` | ATO document approvals |
| `data/poams.csv` | Risk register |
| `data/github_activity.csv` | Issues, pull requests, validation status |
| `data/linux_guides.csv` | Linux control guide list and status |

Keep the existing column headers. Check your changes before committing:

```bash
python scripts/validate_data.py
python -m pytest -q -m "not browser"
```

On Streamlit Community Cloud, pushing a CSV change to `main` redeploys the app.

Other options:

- **Different data folder:** set `ATLAS_DATA_DIR` to an absolute path containing the seven CSV files.
- **Multiple applications:** if `applications.csv` has more than one row, a sidebar selector appears.
- **Linux guides:** each row in `linux_guides.csv` points to a Markdown file under `linux/rhel9/remediation/`. Only the code block under `## Validation procedure` is displayed, and paths outside that folder are rejected.

## Project layout

```
app.py                  Streamlit entrypoint
atlas/data.py           CSV loading, validation, and dashboard model
atlas/renderer.py       HTML rendering for the dashboard
atlas/templates/        HTML and CSS template
data/                   Editable CSV data
linux/rhel9/remediation/  Control guides (Markdown)
scripts/                Data validation, smoke test, preview build, publish helpers
tests/                  Unit, regression, and browser tests
site/reference.html     Static design reference the UI is tested against
```

The dashboard body is rendered as HTML inside a Streamlit iframe (`st.iframe`). It is not built from native Streamlit widgets, so tab switching and the Linux guide panel run in the browser, while Python rebuilds the page from the CSVs on each load.

## Continuous integration

`.github/workflows/ci.yml` runs on every push and pull request to `main`:

- **quality:** Ruff lint, CSV schema and relationship validation, unit tests, compile check, and a headless Streamlit HTTP smoke test.
- **ui-regression:** renders all seven tabs and the AU-12 interaction in Chromium and compares them with `site/reference.html` using fixture data in `tests/fixtures/`.

Dependabot opens monthly update PRs for Python packages and GitHub Actions. No secrets are required.

To require the checks before merging, enable branch protection on `main` and mark `quality` as a required status check.

## Deploy to Streamlit Community Cloud

1. Sign in at <https://share.streamlit.io/> with GitHub.
2. Choose **Create app** and select this repository.
3. Set branch to `main` and main file path to `app.py`.
4. Deploy. Dependencies are installed from `requirements.txt`.

After the first deploy, each push to `main` updates the app.

## Data and security boundaries

- The repository and a Community Cloud deployment are public. Use fictional or approved, redacted data only.
- Issue and PR numbers in the sample data are placeholders. The app does not call the GitHub API and needs no token.
- This is a progress-tracking and presentation tool. It is not a risk management framework tool, vulnerability scanner, authorization decision system, or remediation engine.
- A merged pull request does not mean a POA&M item is validated or closed.
- For real security evidence, use private hosting with access control and an approved evidence store.

## Maintainers

Technyder Inc.

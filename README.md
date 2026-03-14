# Bioinformatics Hiring Trend Index

This folder contains the static site for the live bioinformatics jobs dashboard published at GitHub Pages. The page reads the generated files in `output/` and renders:

- the current skill trend index
- weekly history from `bioinformatics-trend-history.csv`
- role-family and work-mode mix
- a filterable live jobs board

## Data files
- `output/bioinformatics-jobs-board.csv`: current live-role snapshot
- `output/bioinformatics-jobs-board.md`: markdown board export
- `output/bioinformatics-skill-trends.md`: narrative summary
- `output/bioinformatics-trend-history.csv`: weekly history for the dashboard chart

## CI refresh
Two workflows are included:

- `.github/workflows/deploy-pages.yml`: deploys the site on normal pushes to `main`
- `.github/workflows/refresh-data.yml`: runs every Monday at 14:00 UTC and can also be triggered manually

The scheduled refresh workflow runs `automation/refresh_jobs.py`, updates `output/`, commits the refreshed files back to `main`, and deploys Pages from the same workflow run.

## Source coverage
The CI refresh currently uses public job-board APIs from Greenhouse and Lever plus a small direct official-page fallback set for sources without a stable public API. That means the dashboard is automatically refreshed each week from tracked sources, but non-API boards may still require occasional source maintenance.

## Local preview
Serve the folder over HTTP so the browser can fetch the CSV files:

```powershell
cd E:\workdir\bioinformatics-board
python -m http.server 4173
```

Then open `http://127.0.0.1:4173/`.

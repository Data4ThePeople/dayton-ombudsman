# Child care complaints at the Dayton Ombudsman Office, 1997 to 2026

This repo holds the analysis and chart behind a Data 4 The People post on the Dayton and Montgomery County Ombudsman Office. It shows child care as a share of the cases the office investigated each year, from 1997 through June 2026. In the first half of 2026 that share was 18.2 percent, up from 1.9 percent in 2020.

## Live link

- Published post: https://www.data4thepeople.com/p/dayton-ombudsman-child-care
- There is no GitHub Pages site for this repo.

## What's here

- `posts/dayton-ombudsman-child-care/POST.md`: the post text, with its sources listed at the end.
- `posts/dayton-ombudsman-child-care/images/`: the chart (`01-child-care-share.png`) and the hero image.
- `analysis/make_chart.py`: builds the child care share chart and prints a tie-out table of every plotted value.
- `analysis/food_terms.py`: checks the office's topic list for every food assistance category, including misspelled variants.
- `analysis/food_series.py`: food assistance complaints over time, with ranges for withheld counts. This was early exploration and is not used in the post.
- `analysis/make_docx.py`: builds a Word review copy of the post from `POST.md`.

The source data is not in this repo. See the note below.

## Data sources

| Source | Dataset | Used for |
|---|---|---|
| Dayton Ombudsman Office | Office records, January 1997 to June 2026 (`agencies_and_topics_by_year.csv`, `volume_by_month.csv`), shared with permission | Child care counts and yearly totals |
| Child Care Aware of America | The price of child care in 2025; Affordability Analysis state tables | Ohio infant center price and the single-parent income comparison |
| Policy Matters Ohio | How Ohio's publicly funded child care measures up | The 2023 change in Ohio's eligibility limit |

The full list of references, including the history of ombudsman offices and the federal budget law, is at the end of `POST.md`.

**Data note:** the office's CSV files are not yet cleared for public release. They are kept out of this repo (the `data/` folder is listed in `.gitignore`), so the scripts will not run from a fresh clone.

## How to rebuild

Requirements: Python 3 with `matplotlib`, plus `python-docx` for the Word review copy. No API keys are needed.

With the office's CSV files placed in `data/` at the repo root:

```bash
python -m venv .venv
.venv/bin/pip install matplotlib python-docx

# The chart, plus a tie-out table of every plotted value
.venv/bin/python analysis/make_chart.py

# Optional: food assistance exploration
.venv/bin/python analysis/food_terms.py
.venv/bin/python analysis/food_series.py

# Optional: Word review copy of the post
.venv/bin/python analysis/make_docx.py
```

`make_chart.py` writes `posts/dayton-ombudsman-child-care/images/01-child-care-share.png`.

## Method notes

- The chart tracks one category from the office's own controlled topic list: "Job & Family Services - Daycare," filed against Montgomery County.
- Each yearly share divides by the office's published monthly totals, not by a sum of category rows. Summing category rows would drop every count the office withheld.
- The office withholds any count under three. A blank means unknown, not zero, so in years with a withheld count the true share may be slightly higher than shown.
- Two lines are shown: the share of cases the office investigated, and the share of everything that came in, cases and referral calls together.
- 2026 covers January to June only.

---

Data 4 The People

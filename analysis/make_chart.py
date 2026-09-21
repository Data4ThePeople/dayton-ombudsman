"""Child care share of the Dayton Ombudsman Office's incoming work, 1997-2026.

Nothing is hardcoded: every value is recomputed from the published CSVs at
render time. Denominators are the office's own published totals from
volume_by_month.csv, not a sum of category rows, because summing category rows
silently drops every count the office withheld for being under 3.
"""
import csv, collections, os, sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
OUT = os.path.join(HERE, "..", "charts")

BG, FG = "#181A1B", "#BBBDC0"
CASES, ALL = "#3f80c2", "#c2872c"          # validated against BG for CVD + contrast
CATEGORY = "Job & Family Services - Daycare"
PARTIAL_YEAR = 2026                         # January to June only


def read(name):
    with open(os.path.join(DATA, name), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def published_totals():
    """Records opened per year from volume_by_month.csv, split Case vs everything."""
    cases, every = collections.Counter(), collections.Counter()
    seen = set()
    for r in read("volume_by_month.csv"):
        if r["measure"] != "Opened" or not r["count"]:
            continue
        key = (r["month"], r["record_type"], r["measure"])
        if key in seen:
            sys.exit(f"duplicate key in volume_by_month.csv: {key}")
        seen.add(key)
        year, n = int(r["month"][:4]), int(r["count"])
        every[year] += n
        if r["record_type"] == "Case":
            cases[year] += n
    return cases, every


def child_care():
    """Child care records per year. Blank counts are withheld, never zero."""
    cases, every, withheld = collections.Counter(), collections.Counter(), collections.Counter()
    for r in read("agencies_and_topics_by_year.csv"):
        if r["agency_or_topic"] != CATEGORY:
            continue
        year = int(r["year"])
        if not r["count"]:
            withheld[year] += 1
            continue
        n = int(r["count"])
        every[year] += n
        if r["record_type"] == "Case":
            cases[year] += n
    return cases, every, withheld


def main():
    tot_cases, tot_all = published_totals()
    cc_cases, cc_all, withheld = child_care()
    years = sorted(y for y in tot_all if tot_all[y])

    s_cases = [100 * cc_cases.get(y, 0) / tot_cases[y] if tot_cases.get(y) else 0 for y in years]
    s_all = [100 * cc_all.get(y, 0) / tot_all[y] for y in years]

    fig, ax = plt.subplots(figsize=(11, 7.4), dpi=160)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    ax.plot(years, s_cases, color=CASES, lw=2.4, zorder=3)
    ax.plot(years, s_all, color=ALL, lw=2.4, zorder=3)
    ax.plot([years[-1]], [s_cases[-1]], "o", color=CASES, ms=7, zorder=4)
    ax.plot([years[-1]], [s_all[-1]], "o", color=ALL, ms=7, zorder=4)

    ax.set_title("Child care is now about one in five of the complaints the Dayton\n"
                 "ombudsman investigates, up from one in fifty in 2020",
                 color="#E8E9EA", fontsize=15.5, loc="left", pad=54, linespacing=1.45)
    # legend as colored words, not dots
    ax.text(0, 1.085, "Share of cases the office investigated", transform=ax.transAxes,
            color=CASES, fontsize=11.5, fontweight="bold", va="bottom")
    ax.text(0, 1.025, "Share of everything that came in, cases and referral calls",
            transform=ax.transAxes, color=ALL, fontsize=11.5, fontweight="bold", va="bottom")

    ax.annotate(f"{s_cases[-1]:.1f}%", (years[-1], s_cases[-1]), xytext=(9, 0),
                textcoords="offset points", color=CASES, fontsize=12,
                fontweight="bold", va="center")
    ax.annotate(f"{s_all[-1]:.1f}%", (years[-1], s_all[-1]), xytext=(9, 0),
                textcoords="offset points", color=ALL, fontsize=12,
                fontweight="bold", va="center")

    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    top = 5 * (int(max(s_cases) // 5) + 1)
    ax.set_ylim(0, top + 1.5)
    ax.set_yticks(range(0, top + 1, 5))
    ax.set_xlim(years[0] - 0.5, years[-1] + 2.6)
    ax.grid(axis="y", color="#2C2F31", lw=0.9)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#3A3D3F")
    ax.tick_params(colors=FG, labelsize=10.5, length=0)
    # 2026 carries its own end-of-line label, so no tick for it
    ax.set_xticks([y for y in years if y % 5 == 0 and y < years[-1]])

    n_withheld = sum(1 for y in years if withheld.get(y))
    fig.text(0.125, 0.155,
             f"Dayton Ombudsman Office open data, 1997 to June 2026. Category\n"
             f"“{CATEGORY}”, filed against Montgomery County.\n"
             f"{PARTIAL_YEAR} covers January to June only. Shares use the office’s\n"
             f"published monthly totals as the denominator. The office withholds any\n"
             f"count under 3; in the {n_withheld} years with a withheld count the true\n"
             f"share may sit up to 2 records higher.",
             color="#8A8D8F", fontsize=8.4, va="top", linespacing=1.8)
    fig.text(0.955, 0.155, "Built by Data 4 The People",
             color="#8A8D8F", fontsize=8.4, va="top", ha="right")

    fig.subplots_adjust(left=0.125, right=0.955, top=0.815, bottom=0.275)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "01-child-care-share.png")
    fig.savefig(path, facecolor=BG)
    print(f"wrote {os.path.relpath(path)}")

    print("\nTIE-OUT  (every plotted value, recomputed)")
    print(f"{'year':>5}{'cc cases':>10}{'cases':>8}{'% cases':>9}"
          f"{'cc all':>8}{'all recs':>10}{'% all':>8}{'withheld':>10}")
    for i, y in enumerate(years):
        print(f"{y:>5}{cc_cases.get(y,0):>10}{tot_cases.get(y,0):>8}{s_cases[i]:>8.1f}%"
              f"{cc_all.get(y,0):>8}{tot_all[y]:>10}{s_all[i]:>7.1f}%"
              f"{withheld.get(y,0) or '-':>10}")


if __name__ == "__main__":
    main()

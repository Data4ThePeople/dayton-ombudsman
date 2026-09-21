"""Food-assistance complaints over time, with explicit uncertainty from suppression."""
import csv, collections, os

D = os.path.join(os.path.dirname(__file__), "..", "data")

SNAP_CORE = [  # tier A: SNAP itself, the office's "Food Stamps" categories
    "Job & Family Services - Food Stamps - Agency Error",
    "Job & Family Services - Food Stamps - Client Error",
    "Job & Family Services - Food Stamps - Delayed",
    "Job & Family Services - Food Stamps - Eligibility",
]
FOOD_OTHER = [  # tier B: food aid that is not SNAP
    "Emergency Assistance - Food",
    "Personal Health Care - Mobil Meals, Prenatal Care, Immunization, TB Clinic, etc...",
]
AMBIGUOUS = [  # tier C: could carry a food complaint, cannot be attributed
    "Job & Family Services - Recertification",
    "Job & Family Services - Misc.",
    "ODJFS",
    "Social Services",
]

rows = list(csv.DictReader(open(os.path.join(D, "agencies_and_topics_by_year.csv"),
                                encoding="utf-8-sig")))


def series(cats, record_type=None):
    """Returns {year: (visible, n_suppressed_rows)}. Suppressed row = 1 or 2 records."""
    out = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        if r["agency_or_topic"] not in cats:
            continue
        if record_type and r["record_type"] != record_type:
            continue
        y = int(r["year"])
        if r["count"]:
            out[y][0] += int(r["count"])
        else:
            out[y][1] += 1
    return {y: tuple(v) for y, v in sorted(out.items())}


def denom(record_type=None):
    out = collections.defaultdict(int)
    for r in rows:
        if record_type and r["record_type"] != record_type:
            continue
        if r["count"]:
            out[int(r["year"])] += int(r["count"])
    return dict(out)


# --- H1 share of the year, from monthly volume, to make 2026 comparable ---
mon = collections.defaultdict(lambda: collections.defaultdict(int))
for r in csv.DictReader(open(os.path.join(D, "volume_by_month.csv"), encoding="utf-8-sig")):
    if r["measure"] != "Opened" or not r["count"]:
        continue
    y, m = r["month"].split("-")
    mon[int(y)]["H1" if int(m) <= 6 else "H2"] += int(r["count"])

recent = [y for y in range(2016, 2026)]
h1 = sum(mon[y]["H1"] for y in recent)
tot = sum(mon[y]["H1"] + mon[y]["H2"] for y in recent)
H1_SHARE = h1 / tot

print(f"H1 (Jan-Jun) share of full-year volume, 2016-2025 pooled: {H1_SHARE:.3f}")
print("  -> 2026 is a half year; a full-year-equivalent estimate divides by this.\n")

for label, cats in (("SNAP / Food Stamps (tier A)", SNAP_CORE),
                    ("Other food assistance (tier B)", FOOD_OTHER),
                    ("Ambiguous, may include food (tier C)", AMBIGUOUS)):
    s = series(cats)
    d = denom()
    print(f"=== {label} ===")
    print(f"{'year':>5}{'visible':>9}{'hidden':>8}{'range':>12}{'all coded':>11}{'share%':>9}{'share hi%':>11}")
    for y in sorted(s):
        v, h = s[y]
        lo, hi = v + h * 1, v + h * 2   # each hidden row is 1 or 2
        tot_y = d.get(y, 0)
        sh = 100 * v / tot_y if tot_y else 0
        shh = 100 * hi / tot_y if tot_y else 0
        rng = f"{lo}-{hi}" if h else str(v)
        print(f"{y:>5}{v:>9}{h:>8}{rng:>12}{tot_y:>11}{sh:>8.2f}%{shh:>10.2f}%")
    print()

# ---------------- confidence checks ----------------
import math
print("=" * 70)
print("CONFIDENCE CHECKS")
print("=" * 70)

print("\n[1] H1 share of full-year volume, year by year (is 0.488 stable?)")
for y in range(2014, 2026):
    t = mon[y]["H1"] + mon[y]["H2"]
    print(f"   {y}: H1={mon[y]['H1']:>5}  H2={mon[y]['H2']:>5}  H1 share={mon[y]['H1']/t:.3f}")

print("\n[2] 2026 SNAP, half-year, vs the same half-year in prior years")
print("    (prior years scaled by H1 share 0.488; band = hidden rows at 1 or 2)")
s = series(SNAP_CORE)
v26, h26 = s[2026]
lo26, hi26 = v26 + h26, v26 + h26 * 2
print(f"    2026 H1 actual:            {lo26}-{hi26}")
for y in (2022, 2023, 2024, 2025):
    v, h = s[y]
    print(f"    {y} H1-equivalent:        {round((v+h)*H1_SHARE)}-{round((v+h*2)*H1_SHARE)}"
          f"   (full year {v+h}-{v+h*2})")

print("\n[3] Poisson check: 2026 H1 count vs 2025 H1-equivalent expectation")
for obs, name in ((lo26, "low end"), (hi26, "high end")):
    for y in (2024, 2025):
        v, h = s[y]
        exp = (v + h) * H1_SHARE
        z = (obs - exp) / math.sqrt(exp)
        print(f"    {name:>8} obs={obs:>3} vs {y} expectation {exp:>5.1f}  z={z:+.2f}"
              f"  {'SPIKE' if z > 2 else 'DROP' if z < -2 else 'no significant change'}")

print("\n[4] Same, as a share of all coded records (controls for falling total volume)")
d = denom()
print(f"    2026: {100*lo26/d[2026]:.2f}%-{100*hi26/d[2026]:.2f}% of {d[2026]} coded records")
for y in (2022, 2023, 2024, 2025):
    v, h = s[y]
    print(f"    {y}: {100*(v+h)/d[y]:.2f}%-{100*(v+h*2)/d[y]:.2f}% of {d[y]}")

print("\n[5] Case vs I&R split for SNAP categories")
for rt in ("Case", "I&R"):
    sr = series(SNAP_CORE, rt)
    print(f"    {rt:>5}: " + "  ".join(f"{y}:{sr.get(y,(0,0))[0]}(+{sr.get(y,(0,0))[1]}h)"
                                        for y in range(2021, 2027)))

print("\n[6] Does the office's own systemic radar flag SNAP recently?")
sp = list(csv.DictReader(open(os.path.join(D, "systemic_patterns.csv"), encoding="utf-8-sig")))
food = [r for r in sp if "Food" in r["agency_or_topic"]]
print(f"    food-related flags, all time: {len(food)}")
print(f"    latest window in whole file:  {max(r['twelve_months_ending'] for r in sp)}")
print(f"    latest food-related window:   {max(r['twelve_months_ending'] for r in food)}")
for r in sorted(food, key=lambda r: r["twelve_months_ending"])[-5:]:
    print(f"      {r['twelve_months_ending']}  {r['agency_or_topic']}  "
          f"n={r['cases_in_those_12_months']}  {r['compared_with_the_3_years_before']}")

print("\n[7] Suppression exposure: how much of 2026 is invisible?")
for y in (2024, 2025, 2026):
    yr = [r for r in rows if r["year"] == str(y)]
    hid = sum(1 for r in yr if not r["count"])
    vis = sum(int(r["count"]) for r in yr if r["count"])
    print(f"    {y}: {hid}/{len(yr)} rows hidden ({100*hid/len(yr):.0f}%), "
          f"{vis} records visible, up to {vis+hid*2} actually coded")

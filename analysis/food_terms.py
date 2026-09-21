"""Term list + fuzzy matcher for food-assistance topics in the Dayton Ombudsman data.

The office records agency_or_topic from a controlled list, not free text, so the
real job here is to prove no food-assistance category was missed -- including any
that a loose, misspelling-tolerant search would catch.
"""
import csv, collections, difflib, re, unicodedata

# Tier A: SNAP itself. "Food Stamps" is the office's own wording for SNAP.
TIER_A = [
    "snap", "supplemental nutrition assistance", "food stamp", "food stamps",
    "foodstamp", "foodstamps", "food assistance", "ebt", "electronic benefit",
    "food share", "foodshare", "p-ebt", "pebt", "summer ebt", "sun bucks",
]
# Tier B: other food aid, not SNAP but part of the food-assistance picture.
TIER_B = [
    "food", "food bank", "food pantry", "pantry", "foodbank", "commodity",
    "wic", "women infants and children", "school lunch", "free lunch",
    "school meal", "meals on wheels", "mobile meals", "mobil meals",
    "congregate meal", "senior nutrition", "hunger", "nutrition",
    "tefap", "csfp", "emergency food", "soup kitchen",
]
# Tier C: programs administered alongside SNAP that can carry a food complaint,
# or umbrella categories a food complaint could be filed under.
TIER_C = [
    "job & family services", "jfs", "odjfs", "recertification", "redetermination",
    "owf", "ohio works first", "tanf", "cash assistance", "public assistance",
    "social services", "emergency assistance", "benefits", "eligibility",
    "disability assistance", "prc", "heap",
]
# Common misspellings / OCR-ish variants worth catching explicitly.
MISSPELLINGS = [
    "foodstamps", "food stampts", "food stanps", "fodo stamps", "food stmaps",
    "snpa", "sanp", "snap benifits", "food benifits", "food benefits",
    "nutriton", "nutritional assistance", "foood", "fod stamps", "stamps",
]

ALL_TERMS = {"A": TIER_A, "B": TIER_B, "C": TIER_C, "MISSPELL": MISSPELLINGS}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = s.lower().replace("&", "and")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def fuzzy_hits(vocab, threshold=0.78):
    """Every vocabulary entry a term matches: substring, token overlap, or close ratio."""
    out = collections.defaultdict(list)
    for tier, terms in ALL_TERMS.items():
        for t in terms:
            nt = norm(t)
            for v in vocab:
                nv = norm(v)
                why = None
                if nt in nv:
                    why = "substring"
                else:
                    vt = nv.split()
                    for w in vt:
                        if difflib.SequenceMatcher(None, nt, w).ratio() >= threshold:
                            why = f"fuzzy~{w}"
                            break
                    else:
                        if difflib.SequenceMatcher(None, nt, nv).ratio() >= threshold:
                            why = "fuzzy~whole"
                if why:
                    out[v].append((tier, t, why))
    return out


if __name__ == "__main__":
    import sys, os
    d = os.path.join(os.path.dirname(__file__), "..", "data")
    rows = list(csv.DictReader(open(os.path.join(d, "agencies_and_topics_by_year.csv"),
                                    encoding="utf-8-sig")))
    totals = collections.Counter()
    for r in rows:
        totals[r["agency_or_topic"]] += int(r["count"]) if r["count"] else 0
    vocab = sorted(totals)
    hits = fuzzy_hits(vocab)
    print(f"vocabulary size: {len(vocab)}   terms tested: {sum(len(v) for v in ALL_TERMS.values())}")
    print(f"categories matched by at least one term: {len(hits)}\n")
    for tier in ("A", "MISSPELL", "B", "C"):
        print(f"--- tier {tier} ---")
        for v in vocab:
            ws = [h for h in hits.get(v, []) if h[0] == tier]
            if ws:
                print(f"  {totals[v]:7d}  {v}")
                print(f"           via: {', '.join(sorted({f'{t}[{w}]' for _, t, w in ws}))}")
        print()
    print("--- categories with NO match from any tier ---")
    unmatched = [v for v in vocab if v not in hits]
    print(f"  {len(unmatched)} of {len(vocab)}")

#!/usr/bin/env python3
"""Consistency check of the OzFlux/JapanFlux recommended PFT input tables (read only, standard library).

Checks every primary and sensitivity row: host PCT_NAT_PFT + bare = 100; host -> FATES through the DEFAULT14
one-to-one rows; FATES pct_natland = mapped host; pct_vegetated_only = pct_natland / (100 - bare); at most four
live PFTs; the text vector ("EBT 43 / C4 22 / bare 35") equals the numbers; the three matrices agree with the
JSON columns of the master CSV; the final vectors in OZ_JP_PFT_REVIEW equal the master primaries, and every revised
site keeps its v1 primary as the v1_primary_20261102 sensitivity row.

    python3 scripts/check_recommended_inputs.py [directory]
"""
import csv, json, re, sys
from collections import Counter
from pathlib import Path

D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
TAG = "20261102"
# DEFAULT14 one-to-one rows (host natpft -> FATES PFT, 1-based); host 11 is split and must not be used here
HOST2FATES = {1: 2, 2: 2, 3: 3, 4: 1, 5: 4, 6: 5, 7: 6, 8: 6, 9: 7, 10: 9, 12: 12, 13: 13, 14: 14}
ABBR = {"TropEBT": 1, "ENF": 2, "DNF": 3, "EBT": 4, "HydrodecidTropTree": 5, "DBF": 6, "EvergreenShrub": 7,
        "ColdDecidShrub": 9, "CoolC3": 13, "C4": 14}
issues = []


def rd(name): return list(csv.DictReader((D / f"OZ_JP_{name}_{TAG}.csv").open(encoding="utf-8-sig")))


def check_row(tag, text, bare, natland, clm, veg):
    natland = {int(k): float(v) for k, v in natland.items()}
    clm = {int(k): float(v) for k, v in clm.items()}
    veg = {int(k): float(v) for k, v in veg.items()}
    if abs(sum(clm.values()) + bare - 100) > 1e-6: issues.append(f"{tag}: host + bare = {sum(clm.values()) + bare}")
    mapped = {}
    for h, v in clm.items():
        if h not in HOST2FATES: issues.append(f"{tag}: host {h} has no one-to-one DEFAULT14 row"); continue
        mapped[HOST2FATES[h]] = mapped.get(HOST2FATES[h], 0) + v
    if mapped != natland: issues.append(f"{tag}: FATES natland {natland} != mapped host {mapped}")
    for f, v in natland.items():
        if abs(veg.get(f, 0) - v / (100 - bare) * 100) > 1e-3: issues.append(f"{tag}: vegetated-only FATES{f}")
    if len(natland) > 4: issues.append(f"{tag}: {len(natland)} live PFTs")
    got = {}
    for part in text.split("/"):
        m = re.match(r"\s*([A-Za-z0-9]+)\s+([\d.]+)\s*$", part)
        if not m or (m.group(1) != "bare" and m.group(1) not in ABBR): issues.append(f"{tag}: cannot parse '{part}'"); continue
        k = 0 if m.group(1) == "bare" else ABBR[m.group(1)]
        got[k] = got.get(k, 0) + float(m.group(2))
    want = {**natland, **({0: bare} if bare else {})}
    if {k: round(v, 4) for k, v in got.items()} != {k: round(v, 4) for k, v in want.items()}:
        issues.append(f"{tag}: text '{text}' != numbers {want}")


main = rd("RECOMMENDED_CLM_FATES_INPUT_PFT")
pct = {r["site"]: r for r in rd("RECOMMENDED_CLM_PCT_NAT_PFT")}
fat = {r["site"]: r for r in rd("RECOMMENDED_FATES_PFT_PERCENT")}
sens = rd("PFT_INPUT_SENSITIVITY_SCENARIOS")
led = rd("PFT_EVIDENCE_LEDGER")
for r in main:
    s, bare = r["site"], float(r["bare_percent"])
    nat, clm, veg = (json.loads(r[k]) for k in ("fates_natland_percent_json", "clm_pct_nat_pft_json", "fates_vegetated_only_percent_json"))
    check_row(s + " PRIMARY", r["recommended_percent"], bare, nat, clm, veg)
    vec = {i: float(pct[s][f"PCT_NAT_PFT_{i}"]) for i in range(15)}
    if abs(vec[0] - bare) > 1e-6: issues.append(f"{s}: PCT_NAT_PFT_0 != bare")
    if {i: v for i, v in vec.items() if i and v} != {int(k): float(v) for k, v in clm.items()}: issues.append(f"{s}: host matrix != JSON")
    if abs(float(fat[s]["bare_pct_natland"]) - bare) > 1e-6: issues.append(f"{s}: FATES matrix bare")
    for i in range(1, 15):
        a, b = float(fat[s][f"FATES_PFT_{i:02d}_pct_natland"]), float(fat[s][f"FATES_PFT_{i:02d}_pct_vegetated_only"])
        if abs(a - float(nat.get(str(i), 0))) > 1e-6 or abs(b - float(veg.get(str(i), 0))) > 1e-3: issues.append(f"{s}: FATES matrix PFT{i}")
for r in sens:
    check_row(f"{r['site']} {r['scenario']}", r["recommended_percent"], float(r["bare_percent"]),
              json.loads(r["fates_natland_percent_json"]), json.loads(r["clm_pct_nat_pft_json"]), json.loads(r["fates_vegetated_only_percent_json"]))
if (D / f"OZ_JP_PFT_REVIEW_{TAG}.csv").is_file():   # 2 Nov 2026 review: final vectors must be the master primaries
    review = rd("PFT_REVIEW")
    if {r["site"] for r in review} != {r["site"] for r in main}: issues.append("review site set differs from master")
    by = {r["site"]: r for r in main}
    v1 = {}
    for r in sens:
        if r["scenario"] == "v1_primary_20261102": v1[r["site"]] = r["recommended_percent"]
    for r in review:
        s, m = r["site"], by.get(r["site"])
        if m is None: continue
        if r["final_primary"] != m["recommended_percent"]: issues.append(f"{s} REVIEW: final_primary differs from master")
        if json.loads(r["final_clm_pct_nat_pft_json"]) != json.loads(m["clm_pct_nat_pft_json"]) or \
                abs(float(r["final_bare_percent"]) - float(m["bare_percent"])) > 1e-9:
            issues.append(f"{s} REVIEW: final vector differs from master")
        changed = r["final_primary"] != r["v1_primary"]
        if changed and v1.get(s) != r["v1_primary"]: issues.append(f"{s} REVIEW: revised but v1 primary not kept as v1_primary_20261102")
        if not changed and s in v1: issues.append(f"{s} REVIEW: unchanged but has a v1_primary_20261102 scenario")
if set(pct) != {r["site"] for r in main} or set(fat) != set(pct): issues.append("site sets differ between tables")
if not {r["site"] for r in sens} <= set(pct) or not {r["site"] for r in led} <= set(pct): issues.append("unknown site in scenarios/ledger")

print(f"sites {len(main)} | scenarios {len(sens)} | ledger rows {len(led)} "
      f"| verification {dict(Counter(r['verification'].split(' ')[0] for r in led))}")
for i in issues: print("  ISSUE", i)
print("CHECK", "PASS" if not issues else f"FAIL {len(issues)}")
sys.exit(1 if issues else 0)

#!/usr/bin/env python3
"""Reconstructed Stage56 ten-site MET screen (strictly READ ONLY).

Reads (does not create or update) Stage56 CA-Man risk JSON.
Site selection for 8 non-explicit paths is provisional and based on
the available local CSVs; this is NOT scientific sign-off or an approval.
"""
import csv
import hashlib
import json
import math
from datetime import datetime, timedelta
from pathlib import Path

E = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10")
SITES = ("BR-Ma2", "CA-Ca3", "CA-Cbo", "CA-LP1", "CA-Man",
         "CA-TP1", "CA-TP3", "CA-TP4", "US-Aud", "US-Bar")
MAN = E / ("stage54_era_vapour_2_candidate/CA-Man/forcing/"
           "processed_v7_era_vapour2/CA-Man_CLM_forcing_1994_2008.csv")
LP1 = E / ("stage51_scoped_era_rh7_candidate/CA-LP1/forcing/"
           "processed_v6_era_rh7/CA-LP1_CLM_forcing_2007_2024.csv")
RISK = E / "stage56_batch01_met_triage/CA-Man_2007_accepted_risk.json"
EXPECTED_MAN = "fac0bc4a82050a087e462c3af1b05ec16e1f3f803a66bde7bf87c0b3a39d3705"
HOLD = datetime(2007, 7, 3, 20)

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def number(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None

def parse(value):
    value = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
                "%Y%m%d%H%M", "%Y%m%d%H"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None

def humidity(row):
    t, q, p = (number(row.get(k)) for k in ("TBOT", "QBOT", "PSRF"))
    if None in (t, q, p):
        return None
    if p < 200:
        p *= 1000
    elif p < 2000:
        p *= 100
    if not (180 < t < 340 and 0 < q < 0.05 and 50000 < p < 120000):
        return None
    temp = t - 273.15
    es = 6.112 * math.exp(17.67 * temp / (temp + 243.5))
    e = q * (p / 100) / (0.622 + 0.378 * q)
    return 100 * e / es, es - e, temp

def find_candidates():
    found = {site: [] for site in SITES}
    for path in E.rglob("*_CLM_forcing_*.csv"):
        for site in SITES:
            if path.name.startswith(site + "_CLM_forcing_"):
                found[site].append(path)
                break
    return found

def choose(site, found):
    if site == "CA-Man":
        return MAN, "EXPLICIT_STAGE54"
    if site == "CA-LP1" and LP1.is_file():
        return LP1, "EXPLICIT_STAGE51"
    options = found[site]
    if not options:
        return None, "MISSING"
    preferred = [p for p in options if
                 "qc_v5" in p.parts
                 or any(x.startswith("processed_v") for x in p.parts)]
    pool = preferred if preferred else options
    selected = max(pool, key=lambda p: (p.stat().st_mtime, str(p)))
    label = "SINGLE_DISCOVERED" if len(options) == 1 else (
        "PROVISIONAL_%d_CANDIDATES" % len(options))
    return selected, label

def scan(site, path):
    stats = dict(rows=0, bad_core=0, low_rh=0, rh_over100=0,
                 vpd_mismatch=0, ta_jumps=0, accepted_risk=0,
                 noleap_violations=0)
    flags = []
    previous = None
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not {"time", "TBOT", "QBOT", "PSRF"}.issubset(reader.fieldnames or ()):
            raise RuntimeError("missing forcing columns")
        for row in reader:
            stats["rows"] += 1
            t = parse(row["time"])
            if t and t.month == 2 and t.day == 29:
                stats["noleap_violations"] += 1
            result = humidity(row)
            if result is None:
                stats["bad_core"] += 1
                previous = None
                continue
            rh, vpd, ta = result
            risk = site == "CA-Man" and t == HOLD
            if risk:
                stats["accepted_risk"] += 1
            if rh < 1 and not risk:
                stats["low_rh"] += 1
                if len(flags) < 5:
                    flags.append("LOW_RH %s %.4f%%" % (t, rh))
            if rh > 100.1:
                stats["rh_over100"] += 1
            reported = number(row.get("VPD_USE"))
            if reported is not None and abs(reported - vpd) > 0.2:
                stats["vpd_mismatch"] += 1
            if previous and t and t - previous[0] == timedelta(minutes=30):
                delta = ta - previous[1]
                if abs(delta) > 10:
                    stats["ta_jumps"] += 1
                    if len(flags) < 5:
                        flags.append("TA_JUMP %s %.2fC" % (t, delta))
            previous = (t, ta) if t else None
    return stats, flags

def main():
    print("STAGE56 BATCH01 MET TRIAGE - READ ONLY RECONSTRUCTION")
    if not MAN.is_file() or sha256(MAN) != EXPECTED_MAN:
        raise SystemExit("STOP: CA-Man Stage54 candidate SHA mismatch")
    if not RISK.is_file():
        raise SystemExit("STOP: missing Stage56 risk ledger; do not invent acceptance")
    decision = json.loads(RISK.read_text(encoding="utf-8"))
    if decision.get("site") != "CA-Man" or \
       decision.get("timestamp") != str(HOLD) or \
       decision.get("decision") != "ACCEPTED_RISK" or \
       decision.get("candidate_sha256") != EXPECTED_MAN:
        raise SystemExit("STOP: accepted-risk evidence differs")
    print("Confirmed risk:", RISK, "RH", decision.get("RH_pct"),
          "decision", decision["decision"])
    found = find_candidates()
    for site in SITES:
        path, status = choose(site, found)
        print("\n", site, status, path)
        if not path or not path.is_file():
            print("  REVIEW: no forcing candidate found")
            continue
        summary, examples = scan(site, path)
        print(" ", summary)
        for line in examples:
            print("  FLAG:", line)
    print("\nREAD ONLY. Source selection is not an approval.")
    print("QC0, tower clock offsets and BIF/ZBOT still need independent review.")

if __name__ == "__main__":
    main()

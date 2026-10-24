#!/usr/bin/env python3
"""Reconstructed read-only Stage55 verification of two CA-Man candidate edits.

Checks exactly two changed rows/columns, 262800 no-leap rows, unchanged
2007 accepted-risk record, physical closure, and source checksums.
"""
import csv
import hashlib
import math
from datetime import datetime, timedelta
from itertools import zip_longest
from pathlib import Path

E = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10")
OLD = E / ("stage51_scoped_era_rh7_candidate/CA-Man/forcing/"
           "processed_v6_era_rh7/CA-Man_CLM_forcing_1994_2008.csv")
NEW = E / ("stage54_era_vapour_2_candidate/CA-Man/forcing/"
           "processed_v7_era_vapour2/CA-Man_CLM_forcing_1994_2008.csv")
EXPECTED_OLD = "c87c8d44381e29f17bf3ccee074afb27ff526b4dd5b92b951e0a990ba4a5ee3e"
EXPECTED_NEW = "fac0bc4a82050a087e462c3af1b05ec16e1f3f803a66bde7bf87c0b3a39d3705"
TARGETS = {datetime(1999, 5, 9, 13), datetime(2005, 5, 9, 14)}
HOLD = datetime(2007, 7, 3, 20)

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def parse(value):
    value = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y%m%d%H%M", "%Y%m%d%H"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return datetime.fromisoformat(value)

def value(x):
    try:
        result = float(x)
        return result if math.isfinite(result) else float("nan")
    except (ValueError, TypeError):
        return float("nan")

def state(row):
    t, q, p = (value(row.get(k)) for k in ("TBOT", "QBOT", "PSRF"))
    if p < 200:
        p *= 1000
    elif p < 2000:
        p *= 100
    if not (200 < t < 340 and 0 < q < 0.05 and 60000 < p < 110000):
        return None
    temp = t - 273.15
    es = 6.112 * math.exp(17.67 * temp / (temp + 243.5))
    e = q * (p / 100) / (0.622 + 0.378 * q)
    return temp, 100 * e / es, es - e, e

def main():
    print("STAGE55 CA-MAN AUDIT - READ ONLY")
    if not OLD.is_file() or not NEW.is_file():
        raise SystemExit("STOP: missing source or candidate")
    old_sha, new_sha = sha256(OLD), sha256(NEW)
    print("Stage51 SHA256:", old_sha)
    print("Stage54 SHA256:", new_sha)
    if old_sha != EXPECTED_OLD or new_sha != EXPECTED_NEW:
        raise SystemExit("STOP: SHA256 unexpected - do not approve")
    count = 0
    changes = {}
    low = [0, 0]
    context = []
    leap = 0
    hold_rows = []
    with OLD.open(newline="", encoding="utf-8-sig") as left, \
         NEW.open(newline="", encoding="utf-8-sig") as right:
        a, b = csv.DictReader(left), csv.DictReader(right)
        if a.fieldnames != b.fieldnames:
            raise RuntimeError("headers differ")
        required = {"time", "TBOT", "QBOT", "PSRF", "VPD_USE"}
        if not required.issubset(a.fieldnames or []):
            raise RuntimeError("required columns missing")
        for r1, r2 in zip_longest(a, b):
            if r1 is None or r2 is None or r1["time"] != r2["time"]:
                raise RuntimeError("row count or time sequence mismatch")
            t = parse(r1["time"])
            count += 1
            if t.month == 2 and t.day == 29:
                leap += 1
            s1, s2 = state(r1), state(r2)
            if s1 is not None and s1[1] < 1:
                low[0] += 1
            if s2 is not None and s2[1] < 1:
                low[1] += 1
            diff = [k for k in a.fieldnames if r1.get(k) != r2.get(k)]
            if diff:
                if t not in TARGETS or set(diff) != {"QBOT", "VPD_USE"}:
                    raise RuntimeError("unexpected candidate modification " + str(t))
                if t in changes:
                    raise RuntimeError("duplicate candidate modification")
                if s2 is None or abs(s2[2] - value(r2["VPD_USE"])) >= 0.02:
                    raise RuntimeError("physical closure mismatch " + str(t))
                changes[t] = diff
                print("CHANGED:", t, diff, "before:", s1, "after:", s2)
            if abs(t - HOLD) <= timedelta(hours=4):
                context.append((t, s2, r2.get("VPD_USE"), r2.get("TA_USE")))
            if t == HOLD:
                hold_rows.append((r1, r2, s1, s2))
    if count != 262800 or leap != 0 or set(changes) != TARGETS:
        raise RuntimeError("row count / NO_LEAP / target edit mismatch")
    if len(hold_rows) != 1 or hold_rows[0][0] != hold_rows[0][1]:
        raise RuntimeError("2007 HOLD record changed")
    hold_rh = hold_rows[0][3][1] if hold_rows[0][3] else float("nan")
    if not abs(hold_rh - 0.36726) < 0.02:
        raise RuntimeError("2007 accepted risk RH unexpectedly changed")
    print("\n2007 HOLD +/- 4 hours")
    for record in context:
        print(*record)
    print("\nPASS: rows", count, "changed rows", len(changes),
          "RH<1% before/after", low, "NO_LEAP", leap)
    print("PASS: physical closure, accepted-risk record unchanged.")
    print("READ ONLY: no files written or model jobs submitted.")

if __name__ == "__main__":
    main()

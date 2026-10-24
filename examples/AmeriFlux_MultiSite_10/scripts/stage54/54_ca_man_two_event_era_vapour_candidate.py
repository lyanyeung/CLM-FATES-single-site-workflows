#!/usr/bin/env python3
"""Reconstructed Stage54 CA-Man two-event sensitivity candidate.

Source: operator-shared Stage54 procedure on 2026-10-24.
CAUTION: sensitivity only, not scientific forcing approval.
Writes ONLY a new candidate path and new ledger, never overwrites them.
No production forcing, DATM, case, surface, or Slurm operations.
"""
import csv
import hashlib
import math
import os
import re
from datetime import datetime
from pathlib import Path

E = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10")
SRC = E / ("stage51_scoped_era_rh7_candidate/CA-Man/forcing/"
           "processed_v6_era_rh7/CA-Man_CLM_forcing_1994_2008.csv")
DST = E / ("stage54_era_vapour_2_candidate/CA-Man/forcing/"
           "processed_v7_era_vapour2/CA-Man_CLM_forcing_1994_2008.csv")
LEDGER = E / ("stage54_era_vapour_2_candidate/"
              "stage54_two_humidity_corrections.csv")
EXPECTED_SHA = "c87c8d44381e29f17bf3ccee074afb27ff526b4dd5b92b951e0a990ba4a5ee3e"
EVENTS = {
    datetime(1999, 5, 9, 13): dict(ta=5.624, qbot=1.7224425e-5,
                                   era_ta=7.007, era_rh=22.6488,
                                   base_pa_kpa=97.600),
    datetime(2005, 5, 9, 14): dict(ta=12.432, qbot=1.2901717e-5,
                                   era_ta=17.425, era_rh=27.6118,
                                   base_pa_kpa=98.830),
}

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def timestamp(value):
    value = re.sub(r"\.0$", "", str(value).strip())
    if re.fullmatch(r"\d{12}", value):
        return datetime.strptime(value, "%Y%m%d%H%M")
    if re.fullmatch(r"\d{10}", value):
        return datetime.strptime(value, "%Y%m%d%H")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None

def saturation_hpa(celsius):
    return 6.112 * math.exp(17.67 * celsius / (celsius + 243.5))

def pressure_pa(row, fallback_kpa):
    original = row.get("PSRF", "")
    if original in ("", None):
        return fallback_kpa * 1000, "BASE_PA"
    p = float(original)
    if p < 200:
        p *= 1000
    elif p < 2000:
        p *= 100
    if not 70000 <= p <= 110000:
        raise RuntimeError("Invalid pressure")
    if abs(p - fallback_kpa * 1000) > 5000:
        raise RuntimeError("PSRF differs substantially from BASE pressure")
    return p, "PSRF"

def main():
    print("STAGE54 RECONSTRUCTED CA-MAN SENSITIVITY - NEW CANDIDATE ONLY")
    if not SRC.is_file():
        raise SystemExit("STOP: missing Stage51 input")
    if DST.exists() or LEDGER.exists():
        raise SystemExit("STOP: Stage54 output exists; never overwrite")
    source_sha = sha256(SRC)
    if source_sha != EXPECTED_SHA:
        raise SystemExit("STOP: unexpected Stage51 SHA256 " + source_sha)
    with SRC.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        time_col = next((x for x in
                         ("TIMESTAMP_START", "timestamp_start", "TIMESTAMP",
                          "timestamp", "datetime", "DateTime", "time",
                          "TIME", "date_time", "DATE_TIME") if x in fields), None)
        ta_col = next((x for x in ("TBOT", "TA_USE", "TA_F", "TA")
                       if x in fields), None)
        if not time_col or not ta_col or "QBOT" not in fields:
            raise SystemExit("STOP: unknown forcing schema")
        targets = {}
        for row in reader:
            t = timestamp(row[time_col])
            if t in EVENTS:
                if t in targets:
                    raise SystemExit("STOP: duplicate target")
                targets[t] = dict(row)
    if set(targets) != set(EVENTS):
        raise SystemExit("STOP: missing expected timestamps")

    updates = {}
    ledger_rows = []
    for t, x in EVENTS.items():
        row = targets[t]
        raw_ta = float(row[ta_col])
        ta = raw_ta - 273.15 if raw_ta > 150 else raw_ta
        old_q = float(row["QBOT"])
        if abs(ta - x["ta"]) > 0.05:
            raise SystemExit("STOP: tower TA mismatch at " + str(t))
        if abs(old_q - x["qbot"]) > max(1e-7, 0.02 * x["qbot"]):
            raise SystemExit("STOP: source QBOT mismatch at " + str(t))
        pressure, pressure_source = pressure_pa(row, x["base_pa_kpa"])
        e = saturation_hpa(x["era_ta"]) * x["era_rh"] / 100
        es_tower = saturation_hpa(ta)
        new_rh = 100 * e / es_tower
        new_vpd = es_tower - e
        new_q = 0.622 * e / (pressure / 100 - 0.378 * e)
        if not (0 < new_rh < 100 and new_vpd >= 0 and 0 < new_q < 0.03):
            raise SystemExit("STOP: physical bound failure at " + str(t))
        changed = {"QBOT": f"{new_q:.12g}"}
        if "VPD_USE" in fields:
            changed["VPD_USE"] = f"{new_vpd:.10g}"
        if "RH_USE" in fields:
            changed["RH_USE"] = f"{new_rh:.10g}"
        if "RH_IMPLIED_PCT" in fields:
            changed["RH_IMPLIED_PCT"] = f"{new_rh:.10g}"
        updates[t] = changed
        ledger_rows.append(dict(
            timestamp=t.isoformat(sep=" "), candidate_TA_C=ta,
            ERA5_TA_C=x["era_ta"], ERA5_RH_pct=x["era_rh"],
            pressure_source=pressure_source, pressure_Pa=pressure,
            old_QBOT=old_q, new_QBOT=new_q, new_RH_pct=new_rh,
            new_VPD_hPa=new_vpd, status="SENSITIVITY_ONLY_NOT_APPROVED"))
        print(t, "RH %.4f%%, QBOT %.10g, VPD %.5f hPa" %
              (new_rh, new_q, new_vpd))
    DST.parent.mkdir(parents=True, exist_ok=True)
    temporary = DST.with_suffix(".csv.tmp")
    written = set()
    try:
        with SRC.open(newline="", encoding="utf-8-sig") as inp, \
             temporary.open("w", newline="", encoding="utf-8") as out:
            reader = csv.DictReader(inp)
            writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            for row in reader:
                t = timestamp(row[time_col])
                if t in updates:
                    if t in written:
                        raise RuntimeError("duplicate modified timestamp")
                    row.update(updates[t])
                    written.add(t)
                writer.writerow(row)
        if written != set(EVENTS):
            raise RuntimeError("incomplete updates")
        if sha256(SRC) != source_sha:
            raise RuntimeError("source changed while processing")
        os.replace(temporary, DST)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    with LEDGER.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(ledger_rows[0]))
        writer.writeheader()
        writer.writerows(ledger_rows)
    print("NEW CANDIDATE:", DST)
    print("LEDGER:", LEDGER)
    print("SOURCE UNCHANGED:", sha256(SRC) == source_sha)
    print("RECORDED MODIFICATIONS:", len(written))
    print("No model jobs submitted. Scientific approval remains HOLD.")

if __name__ == "__main__":
    main()

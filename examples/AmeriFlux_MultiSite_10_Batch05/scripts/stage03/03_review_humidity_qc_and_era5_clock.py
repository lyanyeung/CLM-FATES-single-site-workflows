#!/usr/bin/env python3
"""Batch05 Stage03: READ-ONLY humidity-event provenance + ERA5 clock/schema scout.

Does not select a clock, approve ERA5, repair meteorology, convert calendars,
overwrite originals, assign PFT/ZBOT, or submit jobs. Python standard library.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta
import hashlib
import json
import math
import os
from pathlib import Path
import re

SITES = {
    "US-UiD": "2008-2024_v1.3_r1",
    "US-UMB": "FULLSET_2007-2021_3-5",
    "US-UMd": "2007-2025_v1.3_r1",
    "US-Var": "2000-2025_v1.3_r1",
    "US-Vcm": "2007-2025_v1.3_r1",
    "US-Vcp": "2007-2025_v1.3_r1",
    "US-WCr": "1999-2025_v1.3_r1",
    "US-Whs": "2007-2025_v1.3_r1",
    "US-Wjs": "2007-2025_v1.3_r1",
    "US-Wkg": "2004-2025_v1.3_r1",
}
ROOT = Path(os.environ.get(
    "FLUXNET_SITES_ROOT", "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
CANDIDATES = {
    "TA": ("TA_F", "TA_F_MDS", "TA"),
    "VPD": ("VPD_F", "VPD_F_MDS", "VPD"),
    "RH": ("RH_F", "RH"),
}
ERA_CANDIDATES = {
    "TA": ("TA_ERA", "TA_ERA5", "TA_F", "TA"),
    "VPD": ("VPD_ERA", "VPD_ERA5", "VPD_F", "VPD"),
    "RH": ("RH_ERA", "RH_ERA5", "RH_F", "RH"),
    "PA": ("PA_ERA", "PA_ERA5", "PA_F", "PA"),
}


def number(value):
    try:
        f = float(value)
        return f if math.isfinite(f) and f not in (-9999, -6999) else None
    except (ValueError, TypeError):
        return None


def stamp(label):
    if not re.fullmatch(r"\d{12}", label):
        raise ValueError("timestamp is not YYYYMMDDHHMM: " + repr(label))
    return datetime.strptime(label, "%Y%m%d%H%M")


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def original_events(stream, sample_max=12):
    reader = csv.DictReader(stream)
    headers = reader.fieldnames or []
    if len(set(headers)) != len(headers) or "TIMESTAMP_START" not in headers:
        raise ValueError("source missing/duplicate timestamp field")
    cols = {k: next((c for c in vs if c in headers), None) for k,vs in CANDIDATES.items()}
    if cols["TA"] is None or cols["VPD"] is None:
        raise ValueError("source TA/VPD column missing; no guessing allowed")
    counted, qc, years = Counter(), defaultdict(Counter), defaultdict(Counter)
    examples, anchors = [], []
    n = 0
    for n, row in enumerate(reader, 1):
        if None in row or any(v is None for v in row.values()):
            raise ValueError("malformed native row " + str(n))
        when = stamp(row["TIMESTAMP_START"])
        v = {k: number(row[c]) if c else None for k,c in cols.items()}
        q = {k: row.get(c + "_QC", "NO_QC_COLUMN") if c else None
             for k,c in cols.items()}
        ta, vpd, native_rh = v["TA"], v["VPD"], v["RH"]
        kinds = []
        if vpd is not None and vpd < 0:
            kinds.append("native_VPD_negative")
        if native_rh is not None:
            if native_rh < 0:
                kinds.append("native_RH_negative")
            if native_rh < 1:
                kinds.append("native_RH_lt1")
            if native_rh > 100:
                kinds.append("native_RH_gt100")
        if ta is not None and vpd is not None and -80 <= ta <= 60:
            es = 6.112 * math.exp(17.67 * ta / (ta + 243.5))
            rh_water = 100 * (1 - vpd / es)
            if rh_water < 0:
                kinds.append("derived_water_RH_negative")
            if rh_water < 1:
                kinds.append("derived_water_RH_lt1")
        else:
            rh_water = None
        if n % 3000 == 1 and ta is not None and q["TA"] == "0":
            if len(anchors) < 160:
                anchors.append((when, ta))
        if kinds:
            for kind in kinds:
                counted[kind] += 1
                qc[kind][str(q["TA"]) + "/" + str(q["VPD"]) + "/" + str(q["RH"])] += 1
                years[kind][when.year] += 1
            if len(examples) < sample_max:
                examples.append(dict(time=when.strftime("%Y%m%d%H%M"),
                                     flags=kinds, TA=ta, VPD=vpd, RH=native_rh,
                                     derived_RH_water=rh_water, QC=q))
    return dict(source_columns=cols, rows=n, counts=dict(counted),
                qc_by_kind={k: dict(c) for k,c in qc.items()},
                years_by_kind={k: dict(c) for k,c in years.items()},
                examples=examples), anchors


def validate_file(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("source is not a regular file: " + str(path))
    return path


def inspect_era(path, anchors, event_examples):
    """Return source-comparison diagnostics, never an inferred clock or repair."""
    candidates = list(range(-12, 13))  # test integer-hour offsets, not approval
    anchor_by_stamp = defaultdict(list)
    for when, ta in anchors:
        for shift in candidates:
            key = (when + timedelta(hours=shift)).strftime("%Y%m%d%H%M")
            anchor_by_stamp[key].append((shift, ta))
    event_by_stamp = defaultdict(list)
    for event in event_examples:
        when = stamp(event["time"])
        for shift in candidates:
            key = (when + timedelta(hours=shift)).strftime("%Y%m%d%H%M")
            event_by_stamp[key].append((shift, event["time"]))
    total, first, last = 0, None, None
    samples = defaultdict(list)
    scored = defaultdict(lambda: [0, 0.0])
    exact = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames or []
        if len(set(headers)) != len(headers) or "TIMESTAMP_START" not in headers:
            raise ValueError("ERA companion has no unique TIMESTAMP_START")
        cols = {k: next((c for c in vs if c in headers), None)
                for k,vs in ERA_CANDIDATES.items()}
        for row in reader:
            total += 1
            if None in row or any(v is None for v in row.values()):
                raise ValueError("ERA companion row width mismatch: " + str(total))
            label = row["TIMESTAMP_START"]
            stamp(label)
            if first is None:
                first = label
            last = label
            if label not in anchor_by_stamp and label not in event_by_stamp:
                continue
            ta = number(row[cols["TA"]]) if cols["TA"] else None
            for shift, orig_ta in anchor_by_stamp.get(label, []):
                if ta is not None:
                    scored[shift][0] += 1
                    scored[shift][1] += abs(ta - orig_ta)
            if label in event_by_stamp:
                v = {k: number(row[c]) if c else None for k,c in cols.items()}
                for shift, source_time in event_by_stamp[label]:
                    if len(samples[shift]) < 12:
                        samples[shift].append(dict(source_time=source_time,
                                                   era_time=label, era=v))
                    if shift == 0 and len(exact) < 12:
                        exact.append(dict(source_time=source_time,
                                          era_time=label, era=v))
    ranking = sorted(
        (dict(shift_hours=s, matched_anchor_count=n,
              mean_abs_TA_difference_C=round(err/n, 4))
         for s, (n, err) in scored.items() if n >= 5),
        key=lambda x: (-x["matched_anchor_count"],
                       x["mean_abs_TA_difference_C"], abs(x["shift_hours"])))
    # Coverage first; an individual "best" candidate is NOT a clock decision.
    by_error = sorted(ranking, key=lambda x: (
        x["mean_abs_TA_difference_C"], -x["matched_anchor_count"],
        abs(x["shift_hours"])))
    return dict(file=path.name, sha256=digest(path), rows=total,
                first=first, last=last, columns=cols,
                anchor_offsets_by_lowest_TA_MAE=by_error[:8],
                event_same_timestamp_samples=exact,
                event_offset_examples={str(k): v[:3] for k,v in samples.items()
                                       if k in (-8, -7, -6, -5, 0, 5, 6, 7, 8)})


def inspect_site(site, root):
    pkg = "AMF_" + site + "_FLUXNET_" + SITES[site]
    folder = root / site / "forcing" / "raw" / pkg
    if not folder.is_dir() or folder.is_symlink():
        raise ValueError("missing original release extraction: " + str(folder))
    product = "FULLSET" if site == "US-UMB" else "FLUXMET"
    native = sorted(p for p in folder.iterdir()
                    if re.fullmatch("AMF_" + re.escape(site) +
                    "_FLUXNET_" + product + "_(HH|HR)_.+[.]csv", p.name, re.I))
    era = sorted(p for p in folder.iterdir()
                 if re.fullmatch("AMF_" + re.escape(site) +
                 "_FLUXNET_ERA5_(HH|HR)_.+[.]csv", p.name, re.I))
    if not native:
        raise ValueError("no original native HH/HR CSV")
    print("SOURCE_FILES", [p.name for p in native])
    print("ERA_FILES", [p.name for p in era])
    if len(native) != 1 or len(era) != 1:
        print("SOURCE_SELECTION_REVIEW: expected 1 native + 1 ERA companion;"
              " inspect all choices before comparison")
    for file in native:
        validate_file(file)
        with file.open(encoding="utf-8-sig", newline="") as stream:
            result, anchors = original_events(stream)
        print("ORIGINAL_SHA256", digest(file))
        print("ORIGINAL_AUDIT", json.dumps(result, sort_keys=True))
        if len(era) == 1:
            validate_file(era[0])
            print("ERA_SCOUT", json.dumps(
                inspect_era(era[0], anchors, result["examples"]), sort_keys=True))
        else:
            print("ERA_SCOUT_SKIPPED: ERA file missing/ambiguous; no guessed source")


def self_test():
    source = (
        "TIMESTAMP_START,TIMESTAMP_END,TA_F,VPD_F,RH,TA_F_QC,VPD_F_QC\n"
        "202001010000,202001010030,10,20,-0.1,0,1\n"
        "202001010030,202001010100,10,1,101,0,0\n")
    import io
    r, anchors = original_events(io.StringIO(source))
    assert r["rows"] == 2 and r["counts"]["derived_water_RH_negative"] == 1
    assert r["counts"]["native_RH_negative"] == 1
    assert r["counts"]["native_RH_gt100"] == 1
    assert len(anchors) == 1
    assert number("-9999") is None and number("nan") is None
    print("STAGE03 SELF-TEST PASS | humidity QC, source clock, missing sentinels;"
          " NO ORIGINAL WRITES")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sites-root", type=Path, default=ROOT)
    parser.add_argument("--sites", nargs="+", choices=list(SITES))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    selected = args.sites or list(SITES)
    if len(set(selected)) != len(selected):
        parser.error("site names must be unique")
    print("BATCH05 STAGE03 | READ-ONLY humidity QC and ERA5 clock/schema scout")
    print("Formula screening assumes TA degC/VPD hPa; water es(T) only.")
    print("Offset testing uses integer hours -12..+12; NO automatic clock selection.")
    failed = []
    for site in selected:
        print("\n========== " + site + " ==========", flush=True)
        try:
            inspect_site(site, args.sites_root.expanduser())
            print("SITE_AUDIT_DONE " + site, flush=True)
        except (OSError, ValueError, KeyError, csv.Error, OverflowError) as e:
            failed.append(site)
            print("SITE_AUDIT_FAILED", site, str(e), flush=True)
    print("STAGE03 SUMMARY: audited={}/{} failed={}".format(
        len(selected)-len(failed), len(selected), ",".join(failed) or "none"))
    print("NO WRITES; NO ERA APPROVAL; NO REPAIRS; NO DATM; NO SLURM")
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())

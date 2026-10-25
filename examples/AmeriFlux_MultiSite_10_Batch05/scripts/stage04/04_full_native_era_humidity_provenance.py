#!/usr/bin/env python3
"""Batch05 Stage04: FULL event-by-event native/ERA humidity provenance shadow.

Read-only. Uses exact, unchanged CSV labels for a diagnostic join, NEVER as
approved clock alignment. No ERA5-Land download, repairs, forcing or jobs.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re

ROOT = Path(os.environ.get(
    "FLUXNET_SITES_ROOT", "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"))
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
FIELD = {"TA": ("TA_F", "TA_F_MDS", "TA"),
         "VPD": ("VPD_F", "VPD_F_MDS", "VPD"),
         "RH": ("RH_F", "RH")}
ERA_FIELD = {"TA": ("TA_ERA",), "VPD": ("VPD_ERA",),
             "PA": ("PA_ERA",)}
EVENT_KEYS = (
    "native_VPD_negative", "native_RH_negative", "native_RH_lt1",
    "native_RH_gt100", "derived_water_RH_lt1", "derived_water_RH_negative")
# Float tolerance matches published three-decimal source fields, not uncertainty.
NUMERIC_EQUAL_ABS_TOL = 0.000001


def number(value):
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) and f not in (-9999.0, -6999.0) else None


def es_water(temp):
    if temp is None or not -80 <= temp <= 60:
        return None
    return 6.112 * math.exp(17.67 * temp / (temp + 243.5))


def stamp(label):
    if not re.fullmatch(r"\d{12}", label or ""):
        raise ValueError("bad timestamp: " + repr(label))
    datetime.strptime(label, "%Y%m%d%H%M")
    return label


def regular(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("missing/nonregular source: " + str(path))
    return path


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as fd:
        for block in iter(lambda: fd.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def reader_csv(stream):
    reader = csv.DictReader(stream)
    names = reader.fieldnames or []
    if len(names) != len(set(names)) or "TIMESTAMP_START" not in names:
        raise ValueError("CSV needs unique TIMESTAMP_START header")
    return reader, names


def choose(names, mapping):
    return {k: next((v for v in candidates if v in names), None)
            for k, candidates in mapping.items()}


def native_scan(stream):
    r, cols = reader_csv(stream)
    selected = choose(cols, FIELD)
    if selected["TA"] is None or selected["VPD"] is None:
        raise ValueError("native TA/VPD fields unavailable")
    events = {}
    counts = Counter()
    categories = defaultdict(Counter)
    years = defaultdict(Counter)
    missing = Counter()
    total = 0
    for total, row in enumerate(r, 1):
        if None in row or any(v is None for v in row.values()):
            raise ValueError("native CSV malformed row " + str(total))
        t = stamp(row["TIMESTAMP_START"])
        v = {k: number(row[c]) if c else None for k, c in selected.items()}
        qc = {k: row.get(c + "_QC", "NO_QC_COLUMN") if c else "NO_COLUMN"
              for k, c in selected.items()}
        for kind, value in v.items():
            if value is None:
                missing[kind] += 1
        es = es_water(v["TA"])
        rh = 100.0 * (1.0 - v["VPD"] / es) if (
            es is not None and v["VPD"] is not None) else None
        flags = []
        if v["VPD"] is not None and v["VPD"] < 0:
            flags.append("native_VPD_negative")
        if v["RH"] is not None:
            if v["RH"] < 0:
                flags.append("native_RH_negative")
            if v["RH"] < 1:
                flags.append("native_RH_lt1")
            if v["RH"] > 100:
                flags.append("native_RH_gt100")
                counts["native_RH_gt100_strong_gt101"] += int(v["RH"] > 101)
                counts["native_RH_gt100_minor_le100p5"] += int(
                    v["RH"] <= 100.5)
        if rh is not None:
            if rh < 0:
                flags.append("derived_water_RH_negative")
            if rh < 1:
                flags.append("derived_water_RH_lt1")
        if not flags:
            continue
        if t in events:
            raise ValueError("duplicate flagged native TIMESTAMP_START " + t)
        events[t] = dict(TA=v["TA"], VPD=v["VPD"], RH=v["RH"],
                         QC=qc, RH_water=rh, flags=flags)
        for key in flags:
            counts[key] += 1
            categories[key][str(qc["TA"]) + "/" + str(qc["VPD"])] += 1
            years[key][t[:4]] += 1
    return events, dict(rows=total, source_fields=selected,
        event_unique=len(events), missing=dict(missing),
        counts=dict(counts),
        by_year={k: dict(v) for k, v in years.items()},
        by_TA_VPD_QC={k: dict(v) for k, v in categories.items()})


def classify(native, era):
    """Exact-label hypothetical pairing, not permission to use ERA."""
    ta, vp = native["TA"], native["VPD"]
    et, ev = era["TA"], era["VPD"]
    flags = []
    if vp is not None and ev is not None and abs(vp - ev) <= NUMERIC_EQUAL_ABS_TOL:
        flags.append("same_native_ERA_VPD")
        if ta is not None and et is not None and abs(ta-et) >= 0.5:
            flags.append("same_VPD_different_TA_ge0p5C")
    if ta is not None and et is not None and abs(ta-et) <= NUMERIC_EQUAL_ABS_TOL:
        flags.append("same_native_ERA_TA")
    es_era, es_tower = es_water(et), es_water(ta)
    paired = None
    if es_era is None or ev is None:
        flags.append("ERA_TA_or_VPD_missing_or_unusable")
    else:
        e_era = es_era - ev
        # ERA humidity is represented by the ERA VPD at its own ERA T.
        if not (0 <= e_era <= es_era):
            flags.append("ERA_moisture_nonphysical_at_ERA_T")
        elif es_tower is None:
            flags.append("tower_T_missing_or_unusable")
        else:
            paired = es_tower - e_era
            if 0 <= paired <= es_tower:
                flags.append("paired_ERA_e_with_tower_T_math_feasible")
            else:
                flags.append("paired_ERA_e_with_tower_T_not_feasible")
    return flags, paired


def era_join(stream, events, sample_limit=6):
    r, cols = reader_csv(stream)
    selected = choose(cols, ERA_FIELD)
    if not selected["TA"] or not selected["VPD"]:
        raise ValueError("ERA companion missing TA_ERA or VPD_ERA")
    counts, by_source_flag = Counter(), defaultdict(Counter)
    examples = defaultdict(list)
    seen = set()
    total = 0
    for total, row in enumerate(r, 1):
        if None in row or any(v is None for v in row.values()):
            raise ValueError("ERA CSV malformed row " + str(total))
        label = stamp(row["TIMESTAMP_START"])
        if label not in events:
            continue
        if label in seen:
            raise ValueError("duplicate ERA timestamp for event: " + label)
        seen.add(label)
        e = {k: number(row[c]) if c else None for k, c in selected.items()}
        n = events[label]
        kinds, paired = classify(n, e)
        counts["events_exact_label_matched"] += 1
        for key in kinds:
            counts[key] += 1
        for f in n["flags"]:
            by_source_flag[f]["events_exact_label_matched"] += 1
            for key in kinds:
                by_source_flag[f][key] += 1
            if len(examples[f]) < sample_limit:
                examples[f].append(dict(time=label, native=n, era=e,
                                        classification=kinds,
                                        paired_hypothetical_VPD_hPa=paired))
    counts["events_exact_label_unmatched"] = len(events) - len(seen)
    return dict(era_rows=total, era_fields=selected,
                event_comparison_counts=dict(counts),
                by_source_flag={k: dict(v) for k, v in by_source_flag.items()},
                examples={k: v for k, v in examples.items()})


def inspect(site, root):
    pkg = "AMF_" + site + "_FLUXNET_" + SITES[site]
    folder = root / site / "forcing" / "raw" / pkg
    if not folder.is_dir() or folder.is_symlink():
        raise ValueError("missing source extraction " + str(folder))
    kind = "FULLSET" if site == "US-UMB" else "FLUXMET"
    prefix = "AMF_" + re.escape(site) + "_FLUXNET_"
    files = [p for p in folder.iterdir() if p.name.endswith(".csv")]
    native = sorted(p for p in files if re.fullmatch(
        prefix + kind + r"_(HH|HR)_.+\.csv", p.name, re.I))
    era = sorted(p for p in files if re.fullmatch(
        prefix + r"ERA5_(HH|HR)_.+\.csv", p.name, re.I))
    if len(native) != 1 or len(era) != 1:
        raise ValueError("expected 1 native and 1 ERA HH/HR; got " +
                         str((len(native), len(era))) + " — manual review")
    a, b = regular(native[0]), regular(era[0])
    initial = ((a.stat().st_size, a.stat().st_mtime_ns),
               (b.stat().st_size, b.stat().st_mtime_ns))
    with a.open(encoding="utf-8-sig", newline="") as fd:
        events, original = native_scan(fd)
    with b.open(encoding="utf-8-sig", newline="") as fd:
        joined = era_join(fd, events)
    final = ((a.stat().st_size, a.stat().st_mtime_ns),
             (b.stat().st_size, b.stat().st_mtime_ns))
    if initial != final:
        raise ValueError("original CSV changed during read-only scan")
    print("SOURCE_PROVENANCE", json.dumps({
        "native": a.name, "native_sha256": sha256(a),
        "ERA_companion": b.name, "ERA_sha256": sha256(b)}, sort_keys=True))
    print("ORIGINAL_FULL_EVENT_COUNTS", json.dumps(original, sort_keys=True))
    print("EXACT_LABEL_ERA_COMPARISON", json.dumps(joined, sort_keys=True))
    print("SITE_STAGE04_DONE", site)


def self_test():
    import io
    raw = ("TIMESTAMP_START,TA_F,VPD_F,RH,TA_F_QC,VPD_F_QC\n"
           "200701170400,-14.254,2.387,89.08,2,2\n"
           "200804091100,-3.424,6.643,-9999,0,2\n"
           "200708091330,18.079,25.275,-9999,0,2\n"
           "200806010000,16,2,55,0,0\n")
    er = ("TIMESTAMP_START,TA_ERA,VPD_ERA,PA_ERA\n"
          "200701170400,-14.254,2.387,70.379\n"
          "200804091100,7.022,6.643,74.194\n"
          "200708091330,27.708,25.275,81.066\n"
          "200806010000,16,2,90\n")
    events, native = native_scan(io.StringIO(raw))
    joined = era_join(io.StringIO(er), events)
    assert native["event_unique"] == 3
    assert native["counts"]["derived_water_RH_negative"] == 3
    c = joined["event_comparison_counts"]
    assert c["same_native_ERA_VPD"] == 3
    assert c["ERA_moisture_nonphysical_at_ERA_T"] == 1
    assert c["paired_ERA_e_with_tower_T_math_feasible"] == 2
    assert c["same_VPD_different_TA_ge0p5C"] == 2
    assert c["events_exact_label_unmatched"] == 0
    # No silently positive "fix" for Vcm; a native-RH >100 minor edge remains an event.
    assert number("-9999.00") is None
    print("STAGE04 SELF-TEST PASS: Vcm ERA-internal unphysical,"
          " Vcp/Wjs ERA-VPD inherited + differing tower T; exact-label join;"
          " NO WRITES")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sites-root", type=Path, default=ROOT)
    ap.add_argument("--sites", nargs="+", choices=list(SITES))
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    sites = args.sites or list(SITES)
    if len(set(sites)) != len(sites):
        ap.error("duplicate sites are not allowed")
    print("BATCH05 STAGE04 | FULL native abnormal-events exact-label ERA shadow")
    print("UNIT ASSUMPTIONS: TA degC; VPD hPa; water es(T) diagnostic ONLY.")
    print("CLOCK NOT APPROVED: source/ERA timestamp strings matched without shifts.")
    print("ERA e = es_water(T_ERA)-VPD_ERA. Paired screen uses es_water(T_tower)-e_ERA.")
    failed = []
    for site in sites:
        print("========== " + site + " ==========", flush=True)
        try:
            inspect(site, args.sites_root.expanduser())
        except (OSError, ValueError, KeyError, csv.Error) as exc:
            print("SITE_STAGE04_FAILED", site, repr(exc), flush=True)
            failed.append(site)
    print("STAGE04 SUMMARY audited={}/{} failed={}".format(
        len(sites)-len(failed), len(sites), ",".join(failed) or "none"))
    print("NO WRITES; NO CLOCK APPROVAL; NO FORCING REPAIR; NO SLURM")
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())

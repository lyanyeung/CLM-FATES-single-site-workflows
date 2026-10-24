#!/usr/bin/env python3
"""Batch04 Stage03: read-only extreme-meteorology and same-timestamp ERA5 audit.

Report native outlier timestamps, directly associated native QC fields, and
same-label ERA5 comparison values (if actually present). Do NOT replace data,
invent observation heights, infer timezones, or blend ERA and tower variables.
This is candidate-level SCIENCE REVIEW, not model forcing approval.
"""
import argparse
import csv
import heapq
import math
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
MAX_EXAMPLES = 8
SRC_FIELDS = ("TA_F", "VPD_F", "PA_F", "RH")
ERA_ALIASES = {
    "TA": ("TA_ERA", "TA", "TA_F"),
    "VPD": ("VPD_ERA", "VPD", "VPD_F"),
    "PA": ("PA_ERA", "PA", "PA_F"),
    "RH": ("RH_ERA", "RH", "RH_F"),
}
MISSING = {"", "NA", "NAN", "-9999", "-9999.0", "-6999", "-6999.0"}


def number(s):
    s = (s or "").strip()
    if s.upper() in MISSING:
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return v if math.isfinite(v) and v not in (-9999, -6999) else None


def read_manifest():
    with (BASE / "sites.tsv").open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    if len(rows) != 10 or len({r["site"] for r in rows}) != 10:
        raise ValueError("Manifest requires 10 unique Batch04 sites")
    return rows


def source_csv(folder, site, product):
    files = sorted(folder.glob("AMF_" + site + "_FLUXNET_" + product + "_HH_*.csv"))
    if len(files) != 1 or files[0].is_symlink() or not files[0].is_file():
        raise ValueError("Expected one original regular " + product + "_HH file")
    return files[0]


def detect(row):
    """All calculations are screening only; do not infer source unit conversions."""
    ta, vpd, pa, rh = (row.get(n) for n in SRC_FIELDS)
    out = {}
    if ta is not None:
        if ta < -80:
            out["TA_LT_NEG80_C"] = -80 - ta
        if ta > 60:
            out["TA_GT60_C"] = ta - 60
    if pa is not None:
        if pa <= 0:
            out["PA_NONPOSITIVE"] = 1 - pa
        if pa < 50:
            out["PA_LT50_KPA"] = 50 - pa
        if pa > 115:
            out["PA_GT115_KPA"] = pa - 115
    if vpd is not None and vpd < 0:
        out["VPD_NEGATIVE"] = -vpd
    if rh is not None:
        if rh < 1:
            out["RH_LT1_PCT"] = 1 - rh
        elif rh < 5:
            out["RH_1TO5_PCT"] = 5 - rh
        if rh > 100:
            out["RH_GT100_PCT"] = rh - 100
    return out


def rh_from_ta_vpd(ta, vpd):
    # TA_F in C and VPD_F in hPa per FLUXNET variable convention.
    # Pure tower-to-tower internal comparison, not a replacement QBOT.
    if ta is None or vpd is None or not (-80 <= ta <= 60):
        return None
    es = 6.112 * math.exp(17.67 * ta / (ta + 243.5))
    return 100 * (es - vpd) / es if es > 0 else None


def short_value(x):
    return "MISSING" if x is None else "{:.6g}".format(x)


def audit_site(site, package, sites_root):
    folder = sites_root / site / "forcing" / "raw" / package
    if not folder.is_dir() or folder.is_symlink():
        raise ValueError("Raw release folder unavailable or symlink: " + str(folder))
    native = source_csv(folder, site, "FLUXMET")
    era = source_csv(folder, site, "ERA5")
    print("\n" + "=" * 74)
    print("SITE:", site, "| NATIVE:", native.name, "| ERA5:", era.name, flush=True)
    flags = Counter()
    years = defaultdict(Counter)
    heaps = defaultdict(list)
    count = 0
    used_native_headers = set()
    with native.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or not {"TIMESTAMP_START", "TIMESTAMP_END"}.issubset(reader.fieldnames):
            raise ValueError("Missing native timestamp headers")
        if any(field not in reader.fieldnames for field in SRC_FIELDS):
            raise ValueError("Missing required native field from " + repr(SRC_FIELDS))
        qc_headers = [
            col for col in reader.fieldnames
            if (col.endswith("_QC") and
                (col in {"TA_F_QC", "VPD_F_QC", "PA_F_QC", "RH_QC"} or
                 any(col.startswith(prefix) for prefix in ("TA_F_", "VPD_F_", "PA_F_", "RH_"))))
        ]
        used_native_headers = set(reader.fieldnames)
        print("NATIVE FLAGS AVAILABLE:", qc_headers or "NO MATCHING QC COLUMNS")
        for item in reader:
            count += 1
            ts0, ts1 = item["TIMESTAMP_START"], item["TIMESTAMP_END"]
            values = {key: number(item.get(key)) for key in SRC_FIELDS}
            hits = detect(values)
            for category, severity in hits.items():
                flags[category] += 1
                years[category][ts0[:4]] += 1
                event = {
                    "start": ts0, "end": ts1, "values": values,
                    "native_qc": {k: item[k] for k in qc_headers},
                    "rh_from_ta_vpd": rh_from_ta_vpd(values["TA_F"], values["VPD_F"])
                }
                slot = heaps[category]
                # Event ordinal breaks ties; avoid comparing dictionaries.
                entry = (severity, count, event)
                if len(slot) < MAX_EXAMPLES:
                    heapq.heappush(slot, entry)
                elif entry[:2] > slot[0][:2]:
                    heapq.heapreplace(slot, entry)
    print("ORIGINAL ROWS:", count)
    if not flags:
        print("EXPLICIT EXTREME FLAGS: 0; no repair authorised")
        return False
    all_events = []
    for category in sorted(flags):
        entries = sorted(heaps[category], reverse=True)
        print("FLAG {} COUNT={} YEARS={} TOP_EXAMPLES={}".format(
            category, flags[category], dict(sorted(years[category].items())),
            len(entries)))
        for severity, ordinal, event in entries:
            all_events.append((category, severity, event))
    targets = {(e["start"], e["end"]) for _, _, e in all_events}
    era_rows = {}
    with era.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or not {"TIMESTAMP_START", "TIMESTAMP_END"}.issubset(reader.fieldnames):
            print("ERA5_TIMESTAMP_LABELS_MISSING: no same-label comparison possible")
        else:
            chosen = {
                var: next((c for c in aliases if c in reader.fieldnames), None)
                for var, aliases in ERA_ALIASES.items()
            }
            print("ERA5 COLUMNS FOUND:", chosen)
            # No timezone offset assumed; compare only EXACT raw string labels.
            for row in reader:
                key = (row["TIMESTAMP_START"], row["TIMESTAMP_END"])
                if key in targets:
                    era_rows[key] = {
                        var: number(row.get(column)) if column else None
                        for var, column in chosen.items()
                    }
            print("EXACT ERA5 TIME-LABEL MATCHES: {}/{}".format(len(era_rows), len(targets)))
    for category, severity, e in sorted(all_events, key=lambda x: (x[0], -x[1], x[2]["start"])):
        key = (e["start"], e["end"])
        tower = " ".join("{}={}".format(k, short_value(v)) for k, v in e["values"].items())
        eravals = era_rows.get(key)
        era_txt = (" ".join("{}={}".format(k, short_value(v)) for k, v in eravals.items())
                   if eravals is not None else "NOT_MATCHED")
        qc_txt = ",".join("{}={}".format(k, v) for k, v in e["native_qc"].items()) or "UNAVAILABLE"
        print("EVENT {} {}-{} TOWER[{}] RH_TA_VPD={} QC[{}] ERA5_SAME_LABEL[{}]".format(
            category, e["start"], e["end"], tower,
            short_value(e["rh_from_ta_vpd"]), qc_txt, era_txt))
    print("No native or ERA5 files altered; ERA5 label agreement is not scientific alignment approval.")
    return True


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sites-root", type=Path, default=ROOT)
    p.add_argument("--sites", nargs="+")
    args = p.parse_args()
    manifest = {row["site"]: row for row in read_manifest()}
    requested = args.sites or list(manifest)
    if len(set(requested)) != len(requested) or set(requested) - set(manifest):
        p.error("Unknown/duplicate site ID")
    flagged, unflagged, failed = [], [], []
    print("BATCH04 STAGE03 READ-ONLY SOURCE ANOMALIES AND ERA5 REFERENCE DIAGNOSTIC")
    print("PROVENANCE WARNING: packaged TA_ERA/PA_ERA are calibrated/downscaled")
    print("FLUXNET-derived ERA columns, NOT independent raw ECMWF ERA5 validation.")
    print("TA_F/PA_F may consolidate these columns where *_F_QC=2.")
    print("ERA5_SAME_LABEL is a raw timestamp match only; no source substitution.")
    for site in requested:
        try:
            has_issues = audit_site(site, manifest[site]["package"], args.sites_root)
            (flagged if has_issues else unflagged).append(site)
        except (OSError, ValueError, csv.Error) as exc:
            failed.append(site)
            print("ERROR {}: {}".format(site, exc), flush=True)
    print("\nSTAGE03 SUMMARY: flagged={} none_of_selected_flags={} failed={}".format(
        ",".join(flagged) or "none",
        ",".join(unflagged) or "none",
        ",".join(failed) or "none"))
    print("READ ONLY. All candidate events require scientific review before ERA5 substitution, forcing, or spin-up.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

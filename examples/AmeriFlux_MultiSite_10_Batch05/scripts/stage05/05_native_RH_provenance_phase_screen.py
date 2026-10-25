#!/usr/bin/env python3
"""Batch05 Stage05: immutable original RH/TA/VPD consistency and phase-aware shadow.

READ ONLY. Never repairs, time-shifts, infers measurement provenance, invents
RH quality flags, selects ERA, writes forcing, or submits Slurm work.
Full native HH/HR sources; no external libraries. Original-RH is NOT assumed
to be an independent tower measurement just because it is populated.
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
RELEASES = {
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
# Fingerprints from operator Stage04 SOURCE_PROVENANCE, NOT downloaded again.
EXPECTED_SHA = {
    "US-UiD": "130142a3b19b11115a058b45129c3ffbeec685b3e5a4e30232701cc149daf318",
    "US-UMB": "ff2d5144e270e3a629d449e26a7796440d91c780c5c6f29ef4d74d84cea24bd6",
    "US-UMd": "e84f61649a1da11b29799d5ad066898d513c0a93da964cd23bb2b48a676ab2f2",
    "US-Var": "664ffeb53419d5ea7f618b0a4d3bebbd767c2b8406e1d167a7881a256287eed2",
    "US-Vcm": "c12437170ddb54630f87859bb33398994d9eb3f1c84686336e18a26d457e841c",
    "US-Vcp": "eece5582523be1f875799751cef9d6b55a4635bfde2ebb008afba31a9a208a42",
    "US-WCr": "f20fbb064ff68668693f8dc04eb72034d98fc4e6e25d4dfb64c7f201a30bb506",
    "US-Whs": "653f757b7037aa3a6a125ab1160430366b9ffc8c84c8cf0e1eca60652b079cca",
    "US-Wjs": "9b23ab803b719dcb55d2525e4c084c53659e9dea42164fe2382507c97f28bdd6",
    "US-Wkg": "f0359fe0a40a413c15e79a30d1e6264e6e2d36717d7d394db40e818c4e684829",
}
COLUMNS = {
    "TA": ("TA_F", "TA_F_MDS", "TA"),
    "VPD": ("VPD_F", "VPD_F_MDS", "VPD"),
    "RH": ("RH_F", "RH"),
}


def number(raw):
    try:
        value = float(raw)
    except (ValueError, TypeError):
        return None
    return value if math.isfinite(value) and value not in (-9999., -6999.) else None


def es_water(t):
    if t is None or not (-80 <= t <= 60):
        return None
    return 6.112 * math.exp(17.67 * t / (t + 243.5))


def es_ice(t):
    if t is None or not (-80 <= t < 0):
        return None
    # Buck-style ice screen (hPa); only an alternative diagnostic.
    return 6.1115 * math.exp((23.036 - t / 333.7) * t / (279.82 + t))


def checksum(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def audit(stream, sample_size=5):
    rows = csv.DictReader(stream)
    headers = rows.fieldnames or []
    if len(headers) != len(set(headers)) or "TIMESTAMP_START" not in headers:
        raise ValueError("No unique TIMESTAMP_START header")
    col = {k: next((c for c in options if c in headers), None)
           for k, options in COLUMNS.items()}
    if not all(col.values()):
        raise ValueError("TA/VPD/RH not present, require manual source review")
    counts, qc = Counter(), defaultdict(Counter)
    examples = defaultdict(list)
    year = defaultdict(Counter)
    total, first, last = 0, None, None
    for total, row in enumerate(rows, 1):
        if None in row or any(v is None for v in row.values()):
            raise ValueError("native CSV row-width mismatch at " + str(total))
        label = row["TIMESTAMP_START"]
        if not re.fullmatch(r"\d{12}", label):
            raise ValueError("invalid timestamp width " + repr(label))
        datetime.strptime(label, "%Y%m%d%H%M")
        if first is None:
            first = label
        last = label
        ta, vpd, rh = (number(row[col[k]]) for k in ("TA", "VPD", "RH"))
        qta = row.get(col["TA"] + "_QC", "NO_QC_COLUMN")
        qvpd = row.get(col["VPD"] + "_QC", "NO_QC_COLUMN")
        qc_key = str(qta) + "/" + str(qvpd)
        ew = es_water(ta)
        ei = es_ice(ta)
        derived_w = (100 * (1 - vpd / ew)
                     if ew is not None and vpd is not None else None)
        derived_i = (100 * (1 - vpd / ei)
                     if ei is not None and vpd is not None else None)
        kinds = []
        if rh is None:
            counts["RH_missing"] += 1
        else:
            counts["RH_present"] += 1
            if rh < 0:
                kinds.append("native_RH_negative")
            if rh < 1:
                kinds.append("native_RH_lt1")
            if rh > 100:
                kinds.append("native_RH_gt100")
                if rh <= 100.5:
                    kinds.append("native_RH_gt100_le100p5")
                elif rh <= 101:
                    kinds.append("native_RH_gt100p5_le101")
                else:
                    kinds.append("native_RH_gt101")
        if vpd is not None and vpd < 0:
            kinds.append("native_VPD_negative")
        if derived_w is not None:
            counts["native_T_VPD_comparable"] += 1
            if derived_w < 0:
                kinds.append("derived_water_RH_negative")
            if derived_w < 1:
                kinds.append("derived_water_RH_lt1")
            if ta is not None and ta < 0:
                counts["subzero_T_VPD_comparable"] += 1
                if derived_w < 1 and derived_i is not None:
                    counts["subzero_derived_water_RH_lt1"] += 1
                    if derived_i < 1:
                        counts["subzero_derived_ice_RH_lt1"] += 1
        if rh is not None and 0 <= rh <= 100 and derived_w is not None:
            counts["native_RH_plausible_and_derived_available"] += 1
            delta = abs(rh - derived_w)
            bin_name = ("within_0p1pp" if delta <= 0.1 else
                        "within_1pp" if delta <= 1 else
                        "within_5pp" if delta <= 5 else "over_5pp")
            counts["RH_vs_derived_water_" + bin_name] += 1
            qc["RH_water_agreement_bins"][qc_key + ":" + bin_name] += 1
            if derived_w < 1 and rh >= 5:
                kinds.append("derived_lt1_native_RH_ge5")
                if ta is not None and ta < 0:
                    kinds.append("derived_lt1_native_RH_ge5_subzero")
            if rh < 1 and derived_w >= 5:
                kinds.append("native_RH_lt1_derived_ge5")
            if delta > 10:
                kinds.append("RH_derived_disagreement_gt10pp")
        if kinds:
            counts["unique_screen_flagged_rows"] += 1
            for kind in set(kinds):
                counts[kind] += 1
                qc[kind][qc_key] += 1
                year[kind][label[:4]] += 1
                if len(examples[kind]) < sample_size:
                    examples[kind].append(dict(time=label, TA=ta, VPD=vpd,
                        RH_original=rh, RH_water=derived_w, RH_ice_screen=derived_i,
                        TA_QC=qta, VPD_QC=qvpd))
    if total == 0:
        raise ValueError("empty native source")
    return dict(rows=total, first=first, last=last, columns=col,
        counts=dict(counts),
        qc_by_category={k: dict(v) for k,v in sorted(qc.items())},
        year_by_category={k: dict(v) for k,v in sorted(year.items())},
        examples={k: v for k,v in sorted(examples.items())})


def inspect_site(site, root):
    package = "AMF_" + site + "_FLUXNET_" + RELEASES[site]
    path = root / site / "forcing" / "raw" / package
    if not path.is_dir() or path.is_symlink():
        raise ValueError("missing source folder " + str(path))
    product = "FULLSET" if site == "US-UMB" else "FLUXMET"
    pattern = re.compile("AMF_" + re.escape(site) +
                         "_FLUXNET_" + product + r"_(HH|HR)_.+[.]csv", re.I)
    candidates = sorted(x for x in path.iterdir() if pattern.fullmatch(x.name))
    if len(candidates) != 1:
        raise ValueError("ambiguous/missing native file " + str(len(candidates)))
    raw = candidates[0]
    if not raw.is_file() or raw.is_symlink():
        raise ValueError("expected regular, non-symlink CSV")
    before = (raw.stat().st_size, raw.stat().st_mtime_ns)
    actual = checksum(raw)
    if actual != EXPECTED_SHA[site]:
        raise ValueError("Stage04 SHA256 source mismatch; STOP; expected=" +
                         EXPECTED_SHA[site] + " actual=" + actual)
    with raw.open(encoding="utf-8-sig", newline="") as stream:
        report = audit(stream)
    after = (raw.stat().st_size, raw.stat().st_mtime_ns)
    if after != before:
        raise ValueError("source changed during audit")
    print("SOURCE_VERIFIED", site, actual, raw.name, flush=True)
    print("NATIVE_RH_PROVENANCE_SCREEN", json.dumps(report, sort_keys=True),
          flush=True)
    print("SITE_STAGE05_DONE", site, flush=True)


def self_test():
    import io
    raw = ("TIMESTAMP_START,TA_F,VPD_F,RH,TA_F_QC,VPD_F_QC\n"
           "200701170400,-14.254,2.387,89.08,2,2\n"
           "200804091100,-3.424,6.643,50,0,2\n"
           "200708091330,18.079,25.275,-9999,0,2\n"
           "200806010000,16,2,55,0,0\n"
           "200806010030,16,2,0,0,0\n"
           "200806010100,16,0,100.1,0,0\n")
    r = audit(io.StringIO(raw))
    c = r["counts"]
    assert r["rows"] == 6
    assert c["derived_water_RH_negative"] == 3
    assert c["derived_lt1_native_RH_ge5"] == 2
    assert c["native_RH_lt1_derived_ge5"] == 1
    assert c["native_RH_gt100_le100p5"] == 1
    assert c["RH_missing"] == 1
    assert c["subzero_derived_water_RH_lt1"] == 2
    print("STAGE05 SELF-TEST PASS | native RH conflict, phase diagnostic,"
          " QC provenance, missing values, original-only read; NO WRITES")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sites-root", type=Path, default=ROOT)
    ap.add_argument("--sites", nargs="+", choices=list(RELEASES))
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    sites = args.sites or list(RELEASES)
    if len(set(sites)) != len(sites):
        ap.error("duplicate sites")
    print("BATCH05 STAGE05 | native RH source/identity screen | READ ONLY")
    print("Assumptions TA degC, VPD hPa, RH percent; RH is NOT treated as independent observation.")
    print("Ice comparison is a separate sensitivity screen; no assumed native RH/VPD phase convention.")
    failed = []
    for s in sites:
        print("========== " + s + " ==========", flush=True)
        try:
            inspect_site(s, args.sites_root.expanduser())
        except (OSError, ValueError, KeyError, csv.Error) as exc:
            failed.append(s)
            print("SITE_STAGE05_FAILED", s, str(exc), flush=True)
    print("STAGE05 SUMMARY audited={}/{} failed={}".format(
        len(sites) - len(failed), len(sites), ",".join(failed) or "none"))
    print("NO WRITES; NO MEASUREMENT PROVENANCE INFERRED; NO SOURCE REPLACED; NO CLOCK SHIFT; NO SLURM")
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())

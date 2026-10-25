#!/usr/bin/env python3
"""Batch05 Stage06: source-RH/processed-VPD lineage and >10pp episodes (READ ONLY).

This examines *all* native source rows, comparing RH with TA_F/VPD_F, under
explicit unit/water-formula assumptions. An RH observation is never inferred to
be independent based on its column name, presence, or agreement alone. This
stage does not repair, time-shift, modify archives, or submit Slurm jobs.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta
import hashlib
import io
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
# Exact fingerprints confirmed by operator's Stage05 SOURCE_VERIFIED lines.
EXPECTED_SHA256 = {
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
TA_FIELD = ("TA_F", "TA_F_MDS", "TA")
VPD_FIELD = ("VPD_F", "VPD_F_MDS", "VPD")
RH_FIELD = ("RH_F", "RH")
CADENCE = timedelta(minutes=30)


def number(value):
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) and x not in (-9999, -6999) else None


def first(names, options):
    return next((name for name in options if name in names), None)


def eswater(t):
    if t is None or not -80 <= t <= 60:
        return None
    return 6.112 * math.exp(17.67 * t / (243.5 + t))


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as fd:
        for chunk in iter(lambda: fd.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def audit(stream):
    reader = csv.DictReader(stream)
    names = reader.fieldnames or []
    if len(set(names)) != len(names) or "TIMESTAMP_START" not in names:
        raise ValueError("missing/duplicate timestamp header")
    t_col, v_col, r_col = (first(names, TA_FIELD),
                           first(names, VPD_FIELD),
                           first(names, RH_FIELD))
    if not all((t_col, v_col, r_col)):
        raise ValueError("TA_F/VPD_F/RH unavailable; no invented source")
    raw_ta = "TA" if "TA" in names and t_col != "TA" else None
    raw_vpd = "VPD" if "VPD" in names and v_col != "VPD" else None
    counts, by_qc, by_year = Counter(), defaultdict(Counter), defaultdict(Counter)
    examples = defaultdict(list)
    long_events, episode = [], None
    previous_time, previous_disagreement = None, False
    rows = 0

    def close_episode():
        nonlocal episode
        if episode:
            long_events.append(episode)
            episode = None

    for rows, row in enumerate(reader, 1):
        if None in row or any(val is None for val in row.values()):
            raise ValueError("malformed CSV row " + str(rows))
        label = row["TIMESTAMP_START"]
        if not re.fullmatch(r"\d{12}", label):
            raise ValueError("bad native timestamp " + repr(label))
        when = datetime.strptime(label, "%Y%m%d%H%M")
        if previous_time is not None and when - previous_time != CADENCE:
            raise ValueError("native non-30min chronology; Stage02 must be rechecked")
        vals = {key: number(row[col]) for key, col in
                (("TA", t_col), ("VPD", v_col), ("RH", r_col))}
        qc = row.get(t_col + "_QC", "NO_QC_COLUMN") + "/" + row.get(
            v_col + "_QC", "NO_QC_COLUMN")
        ta, vp, rh = vals["TA"], vals["VPD"], vals["RH"]
        es = eswater(ta)
        derived = 100.0 * (1.0 - vp / es) if es is not None and vp is not None else None
        native_rh_valid = rh is not None and 0 <= rh <= 100
        if native_rh_valid and derived is not None:
            delta = abs(rh - derived)
            counts["RH_valid_compared"] += 1
            if delta <= 0.1:
                counts["RH_difference_le0p1pp"] += 1
                by_qc["RH_difference_le0p1pp"][qc] += 1
            if delta > 10:
                counts["RH_difference_gt10pp"] += 1
                by_qc["RH_difference_gt10pp"][qc] += 1
                by_year["RH_difference_gt10pp"][label[:4]] += 1
                if len(examples["RH_difference_gt10pp"]) < 6:
                    examples["RH_difference_gt10pp"].append({
                        "time": label, "QC_TA_VPD": qc, "TA": ta,
                        "VPD_F": vp, "RH_original": rh, "RH_derived_water": derived})
        else:
            delta = None
        bad = delta is not None and delta > 10
        if bad:
            if previous_disagreement and episode is not None:
                episode["length_half_hours"] += 1
                episode["last_timestamp"] = label
                episode["qc_pairs"][qc] = episode["qc_pairs"].get(qc, 0) + 1
            else:
                close_episode()
                episode = dict(first_timestamp=label, last_timestamp=label,
                               length_half_hours=1, qc_pairs={qc: 1})
        else:
            close_episode()
        if vp is not None and vp < 0:
            counts["VPD_negative"] += 1
        if derived is not None and derived < 1:
            counts["derived_RH_lt1"] += 1
            if native_rh_valid and rh >= 5:
                counts["derived_lt1_native_RH_ge5"] += 1
                by_qc["derived_lt1_native_RH_ge5"][qc] += 1
                if len(examples["derived_lt1_native_RH_ge5"]) < 6:
                    examples["derived_lt1_native_RH_ge5"].append({
                        "time": label, "QC_TA_VPD": qc, "RH_original": rh,
                        "RH_derived_water": derived, "TA": ta, "VPD_F": vp})
            elif rh is None:
                counts["derived_lt1_native_RH_missing"] += 1
        if rh is None:
            counts["RH_missing"] += 1
        elif rh > 100:
            counts["native_RH_gt100"] += 1
        elif rh < 1:
            counts["native_RH_lt1"] += 1
        if native_rh_valid and ta is not None and qc.split("/")[0] == "0" and qc.split("/")[1] != "0":
            counts["RH_valid_tower_T_QC0_VPD_non0_shadow_only"] += 1
            if derived is not None and derived < 1:
                counts["RH_valid_T_QC0_VPD_non0_derived_lt1_shadow_only"] += 1
        if raw_ta is not None:
            rt = number(row[raw_ta])
            if rt is not None and ta is not None:
                counts["raw_TA_and_processed_TA_comparable"] += 1
                if abs(rt - ta) < 0.000001:
                    counts["raw_TA_equals_processed_TA"] += 1
        if raw_vpd is not None:
            rv = number(row[raw_vpd])
            if rv is not None and vp is not None:
                counts["raw_VPD_and_processed_VPD_comparable"] += 1
                if abs(rv - vp) < 0.000001:
                    counts["raw_VPD_equals_processed_VPD"] += 1
                if bad:
                    counts["raw_VPD_available_at_RH_conflict"] += 1
                    if abs(rv - vp) < 0.000001:
                        counts["raw_VPD_equals_processed_at_RH_conflict"] += 1
        previous_disagreement = bad
        previous_time = when
    close_episode()
    if rows == 0:
        raise ValueError("empty source CSV")
    long_events.sort(key=lambda e: (-e["length_half_hours"], e["first_timestamp"]))
    return dict(rows=rows,
                selected_fields={"TA_processed":t_col, "VPD_processed":v_col,
                                 "RH_original_unverified":r_col,
                                 "TA_unsuffixed_candidate":raw_ta,
                                 "VPD_unsuffixed_candidate":raw_vpd},
                counts=dict(counts),
                qc_pairs={k:dict(v) for k,v in by_qc.items()},
                annual={k:dict(v) for k,v in by_year.items()},
                severe_RH_disagreement_episode_count=len(long_events),
                top_episodes=long_events[:10],
                examples=dict(examples))


def one_site(site, root):
    package = "AMF_" + site + "_FLUXNET_" + RELEASES[site]
    folder = root / site / "forcing" / "raw" / package
    if not folder.is_dir() or folder.is_symlink():
        raise ValueError("source folder missing/ambiguous " + str(folder))
    kind = "FULLSET" if site == "US-UMB" else "FLUXMET"
    pattern = re.compile("AMF_" + re.escape(site) +
                         "_FLUXNET_" + kind + r"_(HH|HR)_.+[.]csv", re.I)
    candidates = sorted(p for p in folder.iterdir() if pattern.fullmatch(p.name))
    if len(candidates) != 1:
        raise ValueError("expected exactly one native HH source")
    f = candidates[0]
    if not f.is_file() or f.is_symlink():
        raise ValueError("non-regular/symlink original source")
    before = (f.stat().st_size, f.stat().st_mtime_ns)
    actual = sha(f)
    if actual != EXPECTED_SHA256[site]:
        raise ValueError("Stage05 SHA256 mismatch " + site + ": " + actual)
    with f.open(encoding="utf-8-sig", newline="") as fd:
        summary = audit(fd)
    if before != (f.stat().st_size, f.stat().st_mtime_ns):
        raise ValueError("original source changed during audit")
    print("STAGE06_SOURCE_SHA256", site, actual)
    print("STAGE06_SITE_REPORT", site, json.dumps(summary, sort_keys=True))
    print("SITE_STAGE06_DONE", site, flush=True)


def self_test():
    data = (
        "TIMESTAMP_START,TA_F,VPD_F,RH,TA_F_QC,VPD_F_QC,TA,VPD\n"
        "202001010000,10,2,83.71,0,0,10,2\n"
        "202001010030,10,4,90,1,1,10,3\n"
        "202001010100,10,4,90,1,1,10,4\n"
        "202001010130,10,2,-9999,0,1,10,2\n"
        "202001010200,10,4,10,2,2,10,4\n"
        "202001010230,-14,2,88,2,2,-14,2\n")
    r = audit(io.StringIO(data))
    assert r["rows"] == 6
    assert r["counts"]["RH_difference_gt10pp"] == 4
    assert r["severe_RH_disagreement_episode_count"] == 2
    assert r["top_episodes"][0]["length_half_hours"] == 2
    assert r["counts"]["RH_missing"] == 1
    assert r["counts"]["raw_VPD_available_at_RH_conflict"] == 4
    assert r["counts"]["derived_lt1_native_RH_ge5"] == 1
    print("STAGE06 SELF-TEST PASS | source/processed alternatives; episode breaks;"
          " RH identity and QC shadow; NO WRITES")


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
        ap.error("sites must be unique")
    print("BATCH05 STAGE06 | READ-ONLY native RH disagreement episode & source candidates")
    print("TA degC, VPD hPa, RH percent assumed; water saturation screening ONLY.")
    print("RH is NOT presumed measured/independent. Same-label/clock issues remain open.")
    failed = []
    for site in sites:
        print("========== " + site + " ==========", flush=True)
        try:
            one_site(site, args.sites_root.expanduser())
        except (OSError, ValueError, KeyError, csv.Error) as e:
            failed.append(site)
            print("SITE_STAGE06_FAILED", site, str(e), flush=True)
    print("STAGE06 SUMMARY audited={}/{} failed={}".format(
        len(sites)-len(failed), len(sites), ",".join(failed) or "none"))
    print("NO WRITES; NO RH ADOPTION; NO SOURCE REPAIRS; NO CLOCK SHIFT; NO SLURM")
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())

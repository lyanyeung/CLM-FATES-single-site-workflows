#!/usr/bin/env python3
"""Batch04 Stage06: independent, SHA-gated Stage05 sparse overlay scientific audit.

--self-test: formula and calendar tests, no file writes.
--check: exact input/patch SHA, source-by-timestamp verification, VPD/RH
         physical closure, held-case counts and new jump review, no writes.
--run: same checks then a NEW report-only directory with CSV and JSON receipts.

NEVER applies overlays to native forcing. A candidate is NOT a Post-v5 or
CIME/DATM/simulation approval. Some humidity repairs are user-selected
research candidates relying on *packaged downscaled FLUXNET ERA*, not
separately downloaded independent raw ERA5-Land measurements.
"""
import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
from uuid import uuid4

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04")
CANDIDATE = ROOT / "qcv5_stage05_candidates/candidate_20261024T103113Z"
EXPECTED = {
    "US-SP1": {"rows": 368208, "patches": 87, "holds": 147, "humidity": 39},
    "US-Syv": {"rows": 438288, "patches": 534, "holds": 606, "humidity": 265},
    "US-Ton": {"rows": 438288, "patches": 4715, "holds": 1, "humidity": 2356},
}
FIELDS = ("site", "TIMESTAMP_START", "TIMESTAMP_END", "variable",
          "original", "candidate", "method", "science_status")
HOLD_FIELDS = ("site", "TIMESTAMP_START", "TIMESTAMP_END", "reason")
NATIVE_FIELDS = ("TIMESTAMP_START", "TIMESTAMP_END",
                 "TA_F", "PA_F", "VPD_F", "RH",
                 "TA_F_QC", "PA_F_QC", "VPD_F_QC")
MISSING = {"", "-9999", "-9999.0", "NA", "NAN"}


def sha(path):
    h = hashlib.sha256()
    with regular(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def regular(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("Missing or symlink source " + str(path))
    return path


def val(x):
    s = str(x if x is not None else "").strip()
    if s.upper() in MISSING:
        return None
    v = float(s)
    if not math.isfinite(v):
        return None
    return v


def sat(t):
    if t is None or not -80 <= t <= 65:
        return None
    return 6.112 * math.exp(17.67 * t / (t + 243.5))


def stamp_shift(key, minutes):
    return (datetime.strptime(key, "%Y%m%d%H%M") +
            timedelta(minutes=minutes)).strftime("%Y%m%d%H%M")


def assert_approx(a, b, label, tol=1e-5):
    if a is None or b is None or abs(a-b) > tol*max(1.0, abs(a), abs(b)):
        raise ValueError("Numerical mismatch {}: {} versus {}".format(label, a, b))


def read_csv(path, required):
    with regular(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError("Missing/duplicate CSV header " + str(path))
        if not set(required).issubset(reader.fieldnames):
            raise ValueError("Missing fields from " + str(path))
        return list(reader)


def read_meta(folder):
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("Candidate output is absent or unsafe")
    meta = json.loads(regular(folder / "report.json").read_text(encoding="utf-8"))
    if (meta.get("mode") != "BUILD_CANDIDATE_OVERLAY" or
            meta.get("scientific_status") != "POST_QCV5_REVIEW_REQUIRED" or
            set(meta.get("sites", {})) != set(EXPECTED)):
        raise ValueError("Candidate mode/sites mismatch")
    if sha(folder / "candidate_patch.csv") != meta.get("candidate_patch_sha256"):
        raise ValueError("Candidate patch SHA256 mismatch")
    for site, target in EXPECTED.items():
        info = meta["sites"][site]
        if (info.get("rows") != target["rows"] or
                info.get("patch_rows") != target["patches"] or
                info.get("hold_rows") != target["holds"]):
            raise ValueError("Stage05 result count mismatch for " + site)
        for role in ("native", "era"):
            source = Path(info["paths"][role])
            fingerprint = info["source_provenance"][role]
            if (sha(source) != fingerprint["sha256"] or
                    source.stat().st_size != fingerprint["size"]):
                raise ValueError(site + " original " + role + " SHA/size mismatch")
            if "/AmeriFlux_MultiSite_10_Batch04/" in str(source):
                raise ValueError("Expected immutable original raw source, not experiment overlay")
    return meta


def context_needed(patches, holds):
    wanted = defaultdict(set)
    for item in patches + holds:
        wanted[item["site"]].add(item["TIMESTAMP_START"])
    for item in patches:
        if item["variable"] == "VPD_F":
            ts = item["TIMESTAMP_START"]
            wanted[item["site"]].update((stamp_shift(ts,-30), stamp_shift(ts,30)))
    return wanted


def read_source_context(meta, wanted):
    source = {}
    for site, timestamps in wanted.items():
        path = Path(meta["sites"][site]["paths"]["native"])
        source[site] = {}
        scanned = 0
        with regular(path).open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or not set(NATIVE_FIELDS).issubset(reader.fieldnames):
                raise ValueError("Missing original source fields for " + site)
            for item in reader:
                scanned += 1
                key = item["TIMESTAMP_START"]
                if key in timestamps:
                    if key in source[site]:
                        raise ValueError("Duplicate native timestamp " + site + " " + key)
                    source[site][key] = {k: item[k] for k in NATIVE_FIELDS}
        if scanned != EXPECTED[site]["rows"]:
            raise ValueError("Full original row count changed for " + site)
        missing = timestamps - set(source[site])
        # Context adjacent to exact source limits may be missing.
        required = {
            x["TIMESTAMP_START"] for x in patches + holds if x["site"] == site
        }
        if missing & required:
            raise ValueError("Missing native target(s): " + repr(sorted(missing & required)[:8]))
        print("SOURCE VERIFIED", site, "total_rows", scanned,
              "required_event_keys", len(required), "context_keys", len(source[site]))
    return source


def original_matches(item, raw):
    var = item["variable"]
    base = raw.get(var)
    if base is None:
        raise ValueError("No corresponding source " + var)
    a, b = val(item["original"]), val(base)
    if a is None and b is None:
        return
    assert_approx(a,b,"original "+var)


def audit(patches, holds, source):
    per_site = defaultdict(Counter)
    patch_index = {}
    pair_groups = defaultdict(dict)
    adverse = []
    boundary_rows = []
    hold_groups = Counter()
    cold_humidity = Counter()
    large_delta = Counter()
    original_qc0 = Counter()
    times = defaultdict(set)
    for item in patches:
        site = item["site"]
        if site not in EXPECTED or item["science_status"] != "CANDIDATE_NOT_POSTV5_APPROVED":
            raise ValueError("Unexpected patched site/science status")
        ts, var = item["TIMESTAMP_START"], item["variable"]
        if item["TIMESTAMP_END"] != stamp_shift(ts,30):
            raise ValueError("Patch not native 30 minute time")
        key = (site, ts, var)
        if key in patch_index:
            raise ValueError("Duplicate sparse patch key " + repr(key))
        patch_index[key] = item
        times[site].add(ts)
        raw = source[site][ts]
        if item["TIMESTAMP_END"] != raw["TIMESTAMP_END"]:
            raise ValueError("Patch original interval mismatch")
        original_matches(item, raw)
        new = val(item["candidate"])
        if new is None:
            raise ValueError("Invalid candidate value")
        per_site[site]["patch_rows"] += 1
        if var == "RH":
            pair_groups[site,ts]["RH"] = item
        if var == "VPD_F" and item["method"] == "QCv5_ERA_RH_AT_RETAINED_TOWER_TA":
            pair_groups[site,ts]["VPD_F"] = item
        if item["method"] == "QCv5_SHORT_LINEAR":
            if var not in ("TA_F","PA_F"):
                raise ValueError("Unexpected interpolation variable")
            if var == "TA_F" and not -80 <= new <= 65:
                raise ValueError("Unphysical interpolated temperature")
            if var == "PA_F" and not 65 <= new <= 110:
                raise ValueError("Unphysical interpolated pressure")
            per_site[site]["local_interpolation"] += 1
        elif item["method"] == "QCv5_ERA_RH_AT_RETAINED_TOWER_TA":
            if var not in ("RH","VPD_F"):
                raise ValueError("Unexpected ERA humidity target")
            per_site[site]["ERA_RH_variable_rows"] += 1
            if var == "VPD_F":
                before = val(raw["VPD_F"])
                if before is not None and abs(new-before)>5:
                    large_delta[site] += 1
                if raw["VPD_F_QC"].strip()=="0":
                    original_qc0[site] += 1
        else:
            raise ValueError("Unexpected patch method " + item["method"])

    for (site,ts), duo in pair_groups.items():
        if set(duo) != {"RH","VPD_F"}:
            raise ValueError("ERA humidity time missing paired RH/VPD " + site+" "+ts)
        a,b = duo["RH"],duo["VPD_F"]
        for field in ("ERA_TA_C","ERA_VPD_hPa","ERA_PA_kPa",
                      "ERA_RH_liquid_pct","tower_TA_candidate_C"):
            assert_approx(val(a[field]),val(b[field]),field)
        e_t,e_v,e_p = (val(a[field]) for field in
                       ("ERA_TA_C","ERA_VPD_hPa","ERA_PA_kPa"))
        rh = val(a["ERA_RH_liquid_pct"])
        new_rh,new_vpd = val(a["candidate"]),val(b["candidate"])
        tower_t = val(a["tower_TA_candidate_C"])
        raw = source[site][ts]
        selected_t = (patch_index.get((site,ts,"TA_F")) or {}).get("candidate",raw["TA_F"])
        assert_approx(tower_t,val(selected_t),"retained tower temperature")
        if not (-55 <= e_t <= 52 and 65 <= e_p <= 110 and 0 <= e_v and
                abs(tower_t-e_t) <= 8):
            raise ValueError("ERA source physical screen should have rejected candidate")
        es_e = sat(e_t)
        es_t = sat(tower_t)
        if es_e is None or es_t is None:
            raise ValueError("Unusable saturation value")
        assert_approx(rh,100*(1-e_v/es_e),"source ERA RH")
        assert_approx(new_rh,rh,"patch RH equals ERA RH")
        assert_approx(new_vpd,es_t*(1-rh/100),"paired VPD closure")
        if not (1 <= rh <= 100.05 and 0 <= new_vpd <= es_t):
            raise ValueError("Candidate new RH/VPD outside physical bounds")
        per_site[site]["humidity_times"] += 1
        if tower_t < 0:
            cold_humidity[site] += 1
        raw_rh = val(raw["RH"])
        raw_v = val(raw["VPD_F"])
        implied = None if raw_v is None else 100*(1-raw_v/es_t)
        if (raw_rh is None or 5 <= raw_rh <= 100) and (
                implied is not None and -0.05 <= implied <= 100.05):
            raise ValueError("ERA humidity patch has no original scientific flag")
    for hold in holds:
        site,ts = hold["site"],hold["TIMESTAMP_START"]
        if site not in EXPECTED or hold["TIMESTAMP_END"] != stamp_shift(ts,30):
            raise ValueError("Unexpected HOLD site/interval")
        if ts not in source[site] or not hold["reason"]:
            raise ValueError("HOLD original source/time or reason absent")
        hold_groups[site,hold["reason"]] += 1
        per_site[site]["hold_rows"] += 1
        adverse.append({
            "site":site, "TIMESTAMP_START":ts,
            "reason":hold["reason"], "tower_TA_C":hold.get("tower_TA_C",""),
            "tower_VPD_hPa":hold.get("tower_VPD_hPa",""),
            "raw_RH_pct":hold.get("raw_RH_pct","")})
    # Scan each neighbour edge once (new vs original) near patched VPD.
    edges = set()
    for site,ts,var in patch_index:
        if var != "VPD_F":
            continue
        edges.add((site,stamp_shift(ts,-30),ts))
        edges.add((site,ts,stamp_shift(ts,30)))
    for site,left,right in sorted(edges):
        data = source[site]
        if left not in data or right not in data:
            continue
        a_old,b_old = val(data[left]["VPD_F"]),val(data[right]["VPD_F"])
        a = val(patch_index[(site,left,"VPD_F")]["candidate"]) if (site,left,"VPD_F") in patch_index else a_old
        b = val(patch_index[(site,right,"VPD_F")]["candidate"]) if (site,right,"VPD_F") in patch_index else b_old
        if any(x is None for x in (a_old,b_old,a,b)):
            continue
        oldjump,newjump=abs(b_old-a_old),abs(b-a)
        if newjump>4 or newjump-oldjump>2:
            boundary_rows.append({
                "site":site,"left_time":left,"right_time":right,
                "original_jump_hPa":"%.6f"%oldjump,
                "candidate_jump_hPa":"%.6f"%newjump,
                "added_jump_hPa":"%.6f"%(newjump-oldjump),
                "new_over4":str(newjump>4),
                "added_over2":str(newjump-oldjump>2),
                "new_left_VPD_hPa":"%.6f"%a,
                "new_right_VPD_hPa":"%.6f"%b,
                "science_status":"REVIEW_ONLY_NO_AUTOMATIC_SMOOTHING"})
    for site,x in EXPECTED.items():
        if (per_site[site]["patch_rows"]!=x["patches"] or
                per_site[site]["hold_rows"]!=x["holds"] or
                per_site[site]["humidity_times"]!=x["humidity"]):
            raise ValueError("Expected per-site patch/HOLD/paired humidity counts not observed "+site)
    return {
        "per_site":per_site, "hold_reasons":hold_groups, "cold_humidity":cold_humidity,
        "large_delta":large_delta, "source_qc0_humidity_changes":original_qc0,
        "unique_candidate_times":{site:len(stamps) for site,stamps in times.items()},
        "boundaries":boundary_rows,"holds":adverse,
    }


def self_test():
    assert stamp_shift("202503181800",30)=="202503181830"
    assert abs(sat(0)-6.112)<1e-10
    assert_approx(100*(1-2/sat(10)),100*(1-2/sat(10)),"es closure")
    print("STAGE06 SELF-TEST PASS: source timestamps, saturation physics, direct pair checks")


def write_csv(path,rows,headers):
    with path.open("x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--run",action="store_true")
    ap.add_argument("--candidate-dir",type=Path,default=CANDIDATE)
    args=ap.parse_args()
    self_test()
    if args.self_test:
        return
    folder=args.candidate_dir
    meta=read_meta(folder)
    patches=read_csv(folder/"candidate_patch.csv",FIELDS)
    holds=read_csv(folder/"unresolved_hold.csv",HOLD_FIELDS)
    if len(patches)!=5336 or len(holds)!=754:
        raise ValueError("Stage05 unique candidate/HOLD counts mismatch")
    source=read_source_context(meta,context_needed(patches,holds))
    result=audit(patches,holds,source)
    print("\nSTAGE06 EXACT SHA-VERIFIED QCv5 CANDIDATE EFFECTS:")
    allsites=sorted(EXPECTED)
    for site in allsites:
        a=result["per_site"][site]
        groups={why:n for (s,why),n in result["hold_reasons"].items() if s==site}
        edge=[z for z in result["boundaries"] if z["site"]==site]
        print("SITE",site,"patch_rows",a["patch_rows"],
              "unique_candidate_times",result["unique_candidate_times"][site],
              "humidity_reconstructed_times",a["humidity_times"],
              "short_interpolated",a["local_interpolation"],
              "holds",a["hold_rows"],"hold_reasons",groups,
              "cold_ERA_RH_reconstructions",result["cold_humidity"][site],
              "VPD_ERA_RH_delta_over5hPa",result["large_delta"][site],
              "native_VPD_QC0_changed",result["source_qc0_humidity_changes"][site],
              "new_high_jump_boundaries",len(edge))
    print("STAGE06 ALL SITES: patch_rows={} hold_rows={} boundary_review_rows={}".format(
        len(patches),len(holds),len(result["boundaries"])))
    for event in sorted(result["boundaries"],
                        key=lambda x:float(x["added_jump_hPa"]),reverse=True)[:15]:
        print("HIGH_JUMP",event)
    print("STAGE06 SCIENCE HOLD: ALL 754 HOLD rows remain unresolved; no Post-v5 approval")
    if args.check:
        print("CHECK ONLY: NO REPORTS OR FORCING WRITTEN")
        return
    out=ROOT/"reports"/(
        "stage06_qcv5_candidate_effects_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
        "_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    write_csv(out/"754_original_holds.csv",result["holds"],
              ["site","TIMESTAMP_START","reason","tower_TA_C","tower_VPD_hPa","raw_RH_pct"])
    write_csv(out/"candidate_VPD_jumps_for_review.csv",result["boundaries"],
              ["site","left_time","right_time","original_jump_hPa",
               "candidate_jump_hPa","added_jump_hPa","new_over4",
               "added_over2","new_left_VPD_hPa","new_right_VPD_hPa","science_status"])
    receipt={
        "source_stage05_dir":str(folder),
        "stage05_patch_sha256":sha(folder/"candidate_patch.csv"),
        "stage05_holds_sha256":sha(folder/"unresolved_hold.csv"),
        "stage05_report_sha256":sha(folder/"report.json"),
        "patch_records":len(patches), "hold_records":len(holds),
        "scientific_status":"HOLD_DO_NOT_APPLY_SPARSE_PATCH_TO_PRODUCTION",
        "unique_target_times":result["unique_candidate_times"],
        "per_site":{site:dict(result["per_site"][site]) for site in EXPECTED},
        "hold_reason_counts":{site:{k[1]:v for k,v in result["hold_reasons"].items() if k[0]==site}
                              for site in EXPECTED},
        "boundary_review_rows":len(result["boundaries"]),
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "source_native_and_ERA_unchanged":True,
        "Postv5_approved":False,"DATM_ready":False,"spinup":False,
    }
    receipt["output_sha256"]={p.name:sha(p) for p in
                              (out/"754_original_holds.csv",out/"candidate_VPD_jumps_for_review.csv")}
    (out/"stage06_readonly_science_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print("STAGE06 NEW REPORT ONLY:",out)
    print("NO ORIGINAL, STAGE05 SPARSE PATCH, DATM, CIME OR SLURM MODIFICATIONS")


if __name__=="__main__":
    main()

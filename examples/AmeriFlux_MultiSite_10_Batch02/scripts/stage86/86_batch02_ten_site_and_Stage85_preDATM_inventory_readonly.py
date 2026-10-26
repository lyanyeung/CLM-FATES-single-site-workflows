#!/usr/bin/env python3
"""Stage86: existing Batch02 ten-site PRE-DATM inventory (READ ONLY).

Purpose: distinguish actual completed ten-site Stage08 selection+Stage09
Post-v5 on IRIDIS from historical Stage07/Stage64 numerical candidates,
and verify the operator's manual Ho1 2000 Stage85 source preservation.
Do NOT rerun old Stage08 automatically: it does not include Stage85 overlay.
This tool never writes data, forcing, NetCDF, cases, GitHub or Slurm.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
STAGE85=ROOT/"reports/stage85_Ho1_2000_MANUAL_KEEP_TOWER_T_humidity_candidate_20261025T235555Z_12086954"
STAGE07=ROOT/"qcv5_native_trial_20261022T010124Z_dfae01c2"
SITES=("US-BZS","US-CMW","US-EML","US-GLE","US-Ha1",
       "US-Ho1","US-Ho2","US-Ho3","US-ICh","US-ICt")
OLD_BLOCKERS={"US-EML":1327,"US-GLE":295,"US-Ho1":937,
              "US-ICh":169,"US-ICt":2176}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):
            h.update(b)
    return h.hexdigest()

def stage85():
    mfile=STAGE85/"stage85_source_decision_manifest.json"
    if not mfile.is_file() or (STAGE85/"INCOMPLETE_DO_NOT_USE").exists():
        raise ValueError("Stage85 operator PASS report missing or incomplete: "+str(STAGE85))
    m=json.loads(mfile.read_text())
    required={
        "schema":"STAGE85_MANUAL_TOWER_TEMP_PRESERVED_HO1_2000_HUMIDITY_CANDIDATE_v1",
        "original_native_halfhour_count":17568,
        "original_measured_T_QC0_preserved_count":17294,
        "original_tower_temperature_changed_count":0,
        "VPD_modified_humidity_only_count":1068,
        "VPD_original_unchanged_ERA_self_32_count":32,
        "nonQC0_original_T_retained_but_science_HOLD_count":274,
        "qbot_source_pressure_available_QC0":17294,
        "qbot_source_pressure_missing_QC0":0,
        "active_forcing_or_DATM_approved":False,
        "other_years_or_sites_unaffected":True
    }
    for key,expect in required.items():
        if m.get(key)!=expect:
            raise ValueError("Stage85 manual decision/physical source count changed: "+key)
    expected_names={
        "17568_Ho1_2000_tower_T_preserved_humidity_candidate.csv",
        "1068_Ho1_2000_VPD_adjusted_no_temperature_change.csv",
        "32_Ho1_2000_manual_T_keep_original_VPD_unchanged.csv",
        "274_Ho1_2000_nonQC0_temperature_source_HOLD.csv"}
    if set(m["outputs_SHA256"])!=expected_names:
        raise ValueError("Stage85 output census changed")
    for name,digest in m["outputs_SHA256"].items():
        if sha(STAGE85/name)!=digest:
            raise ValueError("Stage85 approved source output SHA mismatch: "+name)
    return m

def stage08_candidates():
    roots=[]
    for p in sorted(ROOT.glob("raw_RH_sensitivity_*")):
        if not p.is_dir():continue
        entry={"folder":str(p),"marker_complete":(p/"COMPLETE_TEN_SELECTED_CANDIDATES_REVIEW_REQUIRED").is_file(),
               "complete":False,"sites":[],"input_unchanged":None,"input_report":"unknown"}
        try:
            s=json.loads((p/"selected_candidates.json").read_text())
            entry["sites"]=sorted({r["site"] for r in s.get("candidates",[])})
            entry["complete"]=bool(s.get("complete") and entry["marker_complete"]
                and len(entry["sites"])==len(SITES) and set(entry["sites"])==set(SITES))
            preservation=json.loads((p/"input_preservation_check.json").read_text())
            entry["input_unchanged"]=preservation.get("unchanged")
            if entry["complete"]:
                # Important: a completed Stage08 selection is PRE-Stage85,
                # NOT automatically an adopted Stage85 Ho1-2000 candidate.
                output=json.loads((p/"output_sha256.json").read_text())
                for r in s["candidates"]:
                    f=Path(r["forcing_csv"])
                    if not f.is_file():
                        entry["input_report"]="SOURCE_CANDIDATE_MISSING: "+str(f)
                        entry["complete"]=False;break
                    if sha(f)!=r["forcing_sha256"]:
                        entry["input_report"]="SOURCE_CANDIDATE_SHA_FAILED: "+str(f)
                        entry["complete"]=False;break
                else:
                    entry["input_report"]="TEN_SOURCE_CANDIDATE_SHA_PASS"
                if not output:raise ValueError("Empty Stage08 output digest file")
        except Exception as ex:
            entry["error"]=str(ex)
            entry["complete"]=False
        roots.append(entry)
    return roots

def postv5():
    reports=[]
    for p in sorted((ROOT/"reports").glob("stage09_postqcv5_*")):
        f=p/"postv5_summary.json"
        if not f.is_file():continue
        try:
            m=json.loads(f.read_text())
            reports.append({"folder":str(p),"numeric_pass":m.get("numeric_pass"),
              "failed":m.get("failed"),"inputs_unchanged":m.get("inputs_unchanged"),
              "science_status":m.get("science_status"),
              "QC0_edits":m.get("QC0_edits")})
        except Exception as ex:
            reports.append({"folder":str(p),"error":str(ex)})
    return reports

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test",action="store_true")
    parser.add_argument("--check",action="store_true")
    args=parser.parse_args()
    if not (args.self_test or args.check):
        parser.error("Use --self-test or --check")
    if args.self_test:
        assert len(SITES)==len(set(SITES))==10
        assert sum(OLD_BLOCKERS.values())==4904
        assert set(OLD_BLOCKERS)<set(SITES)
        print("STAGE86 SELF-TEST PASS | exact ten Batch02 sites; historical 5-site Stage07 blockers; no writes")
        return
    m=stage85()
    entries=stage08_candidates()
    posts=postv5()
    print("STAGE86 HO1 2000 STAGE85 SHA VERIFIED | measured T QC0",m["original_measured_T_QC0_preserved_count"],
       "humidity-only edits",m["VPD_modified_humidity_only_count"],"non-QC0 HOLD",m["nonQC0_original_T_retained_but_science_HOLD_count"])
    print("STAGE86 STAGE07 historical trial present",STAGE07.is_dir(), "| 5 previous numeric candidate sites, 5 humidity blockers; do not treat historical status as latest")
    print("STAGE86 EXISTING STAGE08 SELECTION ROOTS",len(entries))
    for e in entries:
        print("STAGE08",e["folder"],"complete",e["complete"],"sites",",".join(e["sites"]),
              "preserved",e["input_unchanged"],"file_status",e["input_report"],"error",e.get("error",""))
    print("STAGE86 EXISTING POST-V5 REPORTS",len(posts))
    for p in posts:
        print("POSTV5",json.dumps(p,ensure_ascii=False))
    ready=[e for e in entries if e["complete"] and e["input_unchanged"] is True]
    finished=[p for p in posts if p.get("numeric_pass")==10 and p.get("failed")==0 and p.get("inputs_unchanged") is True]
    print("STAGE86 TEN-SITE STAGE08 CANDIDATE SET VERIFIED:",len(ready))
    print("STAGE86 TEN-SITE POST-V5 EXISTING REPORTS NUMERIC PASS:",len(finished))
    print("STAGE86 WARNING: Even if Stage08/Post-v5 numeric PASS, they may predate Stage85 Ho1 2000, and are NOT a formal ten-site science/DATM approval.")
    print("STAGE86 HO1 2000 STAGE85 OVERLAY NOT YET INSERTED IN TEN-SITE FORCING.")
    if not ready:
        print("STAGE86 NEXT ACTION: complete ten-site selection without overwriting Stage85 Ho1 2000; investigate missing sites or previous Stage08 blockers.")
    elif not finished:
        print("STAGE86 NEXT ACTION: integrate Stage85 into an ISOLATED copy of the selected forcing, then run new Post-v5 on the combined selection.")
    else:
        print("STAGE86 NEXT ACTION: integrate Stage85 into isolated ten-site selected forcing, rerun combined-source Post-v5 and prepare NOLEAP DATM technical NetCDF.")
    print("STAGE86 CHECK PASS | original Stage85 output SHA verified; actual saved ten-site artifacts inventoried, NO WRITES/JOBS")

if __name__=="__main__":
    main()

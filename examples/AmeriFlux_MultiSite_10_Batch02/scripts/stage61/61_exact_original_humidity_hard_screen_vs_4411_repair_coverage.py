#!/usr/bin/env python3
"""Batch02 Stage61: exact ORIGINAL Stage49 vs unified Stage60/Ho1 coverage.

Identify what fraction of original 26,332 hard physical screens and 100
additional positive RH<1% review events is covered by the Stage60 4,411
same-CDS ERA5 humidity substitutions, with ORIGINAL (site, tower-local
TIMESTAMP_START) identity. Stage60 coverage never licenses an unapproved
DATM write. Independently inventory Stage58's 917 Ho1 UTC-offset HOLDs.
Stage61 emits exact remaining source events by site/year/physics flag.
It does not invent external ERA5 candidate values for uncovered times.
No source, existing stage, NetCDF, CIME, Slurm or model changes.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import hashlib, json
import pandas as pd
import numpy as np

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
R=ROOT/"reports"
S60=R/"stage60_4411_ERA5_water_RH_VPD_QBOT_unified_20261024T112137Z_950f7adf"
S58=R/"stage58_63_manual_T_approved_3967_T_total_20261024T110141Z_e65bde6c"
F60="4411_unique_original_tower_time_ERA5_water_humidity_patch.csv"
F49="original_humidity_event_review.csv"
SITES=("US-BZS","US-CMW","US-EML","US-GLE","US-Ha1","US-Ho1",
       "US-Ho2","US-Ho3","US-ICh","US-ICt")
ORIGINAL_HARD_PER_SITE={"US-BZS":86,"US-CMW":42,"US-EML":4311,
  "US-GLE":1125,"US-Ha1":421,"US-Ho1":16788,"US-Ho2":724,
  "US-Ho3":39,"US-ICh":226,"US-ICt":2570}
PATCH_PER_SITE={"US-EML":1327,"US-GLE":295,"US-Ha1":398,
  "US-Ho2":7,"US-ICh":178,"US-ICt":2206}
HARD_FLAGS=set(("WATER_NEG_VPD_SEVERE","RH_RAW_NEGATIVE",
   "RH_RAW_ZERO","RH_RAW_GT100","RH_INFERRED_LT0","RH_INFERRED_GT101",
   "ACTUAL_VAPOR_NONPOSITIVE"))
SOURCE_HO1="HOLD_HO1_LOCAL_UTC_OFFSET_PROVISIONAL"
DEFAULT_STAGE49_PREFIX="stage49_original_humidity_review_"

def sha(path):
    digest=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):
            digest.update(block)
    return digest.hexdigest()

def get_stage49(user_path):
    if user_path is not None:
        p=user_path.resolve(strict=True)
        return p
    found=[]
    for p in sorted(R.glob(DEFAULT_STAGE49_PREFIX+"*/provenance_and_hold.json")):
        try:
            m=json.loads(p.read_text())
            t=m.get("totals",{})
            if (m.get("status")=="REVIEW_ONLY_NO_DATM_APPROVAL"
                and m.get("approved_for_DATM") is False
                and int(t.get("HARD_PHYSICS_UNION",-1))==26332
                and int(t.get("ROW_LEVEL_REVIEW",-1))==26432):
                found.append(p.parent)
        except (OSError,ValueError,TypeError,KeyError):
            continue
    if not found:
        raise FileNotFoundError(
           "No existing completed Stage49 26432-row report under "+str(R)+
           ". Supply --stage49 /path/to/stage49_original_humidity_review_<id>; "
           "do NOT run new CDS downloads.")
    for path in found:print("MATCHING_STAGE49",path)
    return found[-1]

def to_native(series):
    raw=series.astype(str).str.strip().str.replace(r"\.0$","",regex=True)
    t=pd.to_datetime(raw,format="%Y%m%d%H%M",errors="raise")
    if t.isna().any() or t.dt.tz is not None:
        raise ValueError("Source timestamp contains NaT or timezone")
    return t.dt.strftime("%Y%m%d%H%M")

def load(s49):
    for p in (s49,S58,S60):
        if (not p.is_dir()) or (p/"INCOMPLETE_DO_NOT_USE").exists():
            raise ValueError("Incomplete/missing report "+str(p))
    m49=json.loads((s49/"provenance_and_hold.json").read_text())
    m58=json.loads((S58/"manual_temperature_decision_manifest.json").read_text())
    m60=json.loads((S60/"unified_science_policy_manifest.json").read_text())
    if (m49.get("status")!="REVIEW_ONLY_NO_DATM_APPROVAL" or
        m49.get("stage48_blob_sha1")!="8856b568d413e3d27c40fd6c6a014a4e755ecfb3" or
        m49.get("approved_for_DATM") is not False or
        int(m49.get("totals",{}).get("HARD_PHYSICS_UNION",0))!=26332 or
        int(m49.get("totals",{}).get("ROW_LEVEL_REVIEW",0))!=26432 or
        int(m49.get("totals",{}).get("EXTREME_DRY_REVIEW_UNION",0))!=102):
        raise ValueError("Wrong Stage49 original physics-census manifest")
    inventory=Path(m49["inventory"]).resolve(strict=True)
    if sha(inventory)!=m49["inventory_sha256"]:
        raise ValueError("Original stage04b source inventory changed")
    if (m58.get("schema")!="STAGE58_USER_MANUAL_EXTREME_COLD_TA_APPROVAL_ONLY_v1" or
        m58.get("n_total_original_T_retained")!=3967 or
        m58.get("n_Ho1_provisional_offset_hold")!=917 or
        m58.get("approved_for_DATM") is not False):
        raise ValueError("Stage58 held temperature provenance changed")
    for name,d in m58.get("report_sha256",{}).items():
        if sha(S58/name)!=d:
            raise ValueError("Stage58 checksum mismatch: "+name)
    if (m60.get("schema")!="STAGE60_UNIFIED_4411_ERA5_WATER_HUMIDITY_SELECTION_v1" or
        m60.get("total_unique_rows")!=4411 or
        m60.get("n_stage53_444")!=444 or
        m60.get("n_stage59_3967")!=3967 or
        m60.get("n_Ho1_UTC_HOLD_not_included")!=917 or
        m60.get("approved_for_DATM") is not False or
        m60.get("approved_for_spinup") is not False or
        m60.get("forcing_modified") is not False or
        m60.get("output_sha256",{}).get(F60)!=sha(S60/F60)):
        raise ValueError("Stage60 immutable candidate manifest changed")
    for name,d in m60.get("output_sha256",{}).items():
        if sha(S60/name)!=d:
            raise ValueError("Stage60 output checksum mismatch "+name)
    a=pd.read_csv(s49/F49,dtype={"site":str,"timestamp_start":str,
                                 "source_sha256":str})
    b=pd.read_csv(S60/F60,dtype={"site":str,"tower_local_start":str})
    h=pd.read_csv(S58/"4884_final_original_tower_temperature_policy.csv",
                  dtype={"site":str,"local_key":str})
    if len(a)!=26432 or len(b)!=4411 or len(h)!=4884:
        raise ValueError("Stage49/60/58 exact record counts differ")
    if Counter(b.site)!=Counter(PATCH_PER_SITE) or set(a.site)!=set(SITES):
        raise ValueError("Unexpected Stage60/Stage49 site population")
    for c in ("flags","source_sha256","source_csv_row","timestamp_start",
              "RH_raw_pct","VPD_hPa","TA_C","PA_kPa"):
        if c not in a:raise ValueError("Stage49 mandatory source field missing: "+c)
    if not {"site","tower_local_start","candidate_cohort",
            "replacement_RH_water_pct","replacement_VPD_water_hPa",
            "replacement_QBOT_kgkg"}.issubset(b.columns):
        raise ValueError("Stage60 patch has unexpected schema")
    a["local_key"]=to_native(a.timestamp_start)
    b["local_key"]=to_native(b.tower_local_start)
    h["local_key"]=pd.to_datetime(h.local_key,errors="raise").dt.strftime("%Y%m%d%H%M")
    for name,df in (("Stage49",a),("Stage60",b),("Stage58",h)):
        if df.local_key.isna().any() or df.duplicated(["site","local_key"]).any():
            raise ValueError(name+" contains invalid/duplicate source identity")
    if not h.loc[h.site=="US-Ho1","final_temperature_decision"].eq(SOURCE_HO1).sum()==917:
        raise ValueError("Stage58 917 Ho1 HOLD not preserved")
    if "US-Ho1" in set(b.site):
        raise ValueError("Ho1 appeared in selected Stage60 patch unexpectedly")
    f=a["flags"].fillna("").astype(str).str.split("|")
    a["hard_original"]=f.apply(lambda vals:bool(set(vals)&HARD_FLAGS))
    a["positive_RH_lt1_review"]=f.apply(lambda vals:"RH_RAW_LT1_POS" in vals)
    a["raw_RH_zero_or_over100"]=f.apply(lambda vals:"RH_RAW_ZERO" in vals or "RH_RAW_GT100" in vals)
    a["inferred_nonphysical_RH"]=f.apply(lambda vals:"RH_INFERRED_LT0" in vals)
    if (int(a.hard_original.sum())!=26332 or
        int(a.positive_RH_lt1_review.sum())!=102 or
        Counter(a.loc[a.hard_original,"site"])!=Counter(ORIGINAL_HARD_PER_SITE)):
        raise ValueError("Original source hard physics flags do not match Stage48 per-site totals")
    exactpatch=set(zip(b.site,b.local_key))
    a["selected_in_Stage60_4411"]=[
         (site,timestamp) in exactpatch
         for site,timestamp in zip(a.site,a.local_key)]
    originals=set(zip(a.site,a.local_key))
    b["is_in_Stage49_original_hard_or_dry_review"]=[
         (site,timestamp) in originals
         for site,timestamp in zip(b.site,b.local_key)]
    ho1=set(zip(h.loc[h.final_temperature_decision.eq(SOURCE_HO1),"site"],
                h.loc[h.final_temperature_decision.eq(SOURCE_HO1),"local_key"]))
    a["is_Stage58_Ho1_UTC_HOLD"]= [
         (site,timestamp) in ho1
         for site,timestamp in zip(a.site,a.local_key)]
    return a,b,h,{"stage49_report_sha256":sha(s49/F49),
       "stage49_manifest_sha256":sha(s49/"provenance_and_hold.json"),
       "stage49_inventory_sha256":sha(inventory),
       "stage58_report_sha256":sha(S58/"4884_final_original_tower_temperature_policy.csv"),
       "stage60_patch_sha256":sha(S60/F60),
       "stage60_manifest_sha256":sha(S60/"unified_science_policy_manifest.json")}

def classify(a,b):
    a["coverage_class"]=np.select([
       a.selected_in_Stage60_4411,
       a.is_Stage58_Ho1_UTC_HOLD,
       a.hard_original,
       a.positive_RH_lt1_review],
       ["STAGE60_SELECTED_WATER_HUMIDITY_CANDIDATE",
        "HO1_STAGE58_UTC_PROVENANCE_HOLD",
        "ORIGINAL_HARD_NO_VERIFIED_CDS_REPLACEMENT_YET",
        "EXTREME_POSITIVE_DRYNESS_REVIEW"],default="OTHER_REVIEW")
    summary=[]
    for site in SITES:
        d=a[a.site==site];p=b[b.site==site]
        un=d[d.hard_original&~d.selected_in_Stage60_4411]
        summary.append({"site":site,
          "Stage49_hard_original":int(d.hard_original.sum()),
          "Stage49_extreme_dry_including_overlaps":int(d.positive_RH_lt1_review.sum()),
          "Stage49_unique_total_review":len(d),
          "Stage60_selected_4411":len(p),
          "Stage60_in_Stage49_review":int(p.is_in_Stage49_original_hard_or_dry_review.sum()),
          "Stage60_not_in_Stage49_review":int((~p.is_in_Stage49_original_hard_or_dry_review).sum()),
          "Stage49_hard_exactly_covered_by_Stage60":int((d.hard_original&d.selected_in_Stage60_4411).sum()),
          "Stage49_original_hard_not_covered":len(un),
          "Stage49_remaining_inferred_negative_RH":int(un.inferred_nonphysical_RH.sum()),
          "Stage49_original_uncovered_extreme_positive_dryness":int((d.positive_RH_lt1_review&~d.selected_in_Stage60_4411).sum()),
          "Stage58_Ho1_UTC_HOLD_in_original_review":int(d.is_Stage58_Ho1_UTC_HOLD.sum()),
          "Stage49_hard_intersects_917_Ho1_HOLD":int((d.hard_original&d.is_Stage58_Ho1_UTC_HOLD).sum())})
    return pd.DataFrame(summary)

def self_test():
    t=pd.DataFrame({"flags":["RH_RAW_ZERO|RH_INFERRED_LT0","RH_RAW_LT1_POS",
        "RH_RAW_GT100","RH_INFERRED_LT0|ACTUAL_VAPOR_NONPOSITIVE"]})
    vals=t["flags"].str.split("|")
    assert vals.apply(lambda f:bool(HARD_FLAGS&set(f))).sum()==3
    assert vals.apply(lambda f:"RH_RAW_LT1_POS" in f).sum()==1
    assert sum(ORIGINAL_HARD_PER_SITE.values())==26332
    assert sum(PATCH_PER_SITE.values())==4411
    print("STAGE61 SELF-TEST PASS | 10-site original hard physics flags and site/local-time exact coverage")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--audit",action="store_true")
    parser.add_argument("--stage49",type=Path,default=None)
    args=parser.parse_args()
    if args.self_test:return self_test()
    s49=get_stage49(args.stage49)
    a,b,h,pins=load(s49)
    summ=classify(a,b)
    uncovered=a[a.hard_original&~a.selected_in_Stage60_4411].copy()
    if int((summ.Stage49_hard_original).sum())!=26332:
        raise ValueError("Per-site original hard counts incorrect")
    print("STAGE61 SOURCE CHECK PASS | 26432 original review, 26332 original hard, 4411 patches")
    print("STAGE49_SOURCE",s49)
    print("PATCH_COVERED_ORIGINAL_HARD",int((a.hard_original&a.selected_in_Stage60_4411).sum()))
    print("REMAINING_ORIGINAL_HARD",len(uncovered))
    print("STAGE60_PATCH_NOT_IN_STAGE49_ORIGINAL_REVIEW",int((~b.is_in_Stage49_original_hard_or_dry_review).sum()))
    print("HO1_917_UTC_HOLD_IN_STAGE49_REVIEW",int(a.is_Stage58_Ho1_UTC_HOLD.sum()))
    for x in summ.to_dict("records"):print("SITE",x)
    print("UNCOVERED_TOP_30")
    print(uncovered[["site","timestamp_start","flags","TA_C","VPD_hPa",
         "RH_raw_pct","source_csv_row","science_route"]].head(30).to_string(index=False))
    print("Coverage is a SCIENCE CROSSWALK: Stage60 is NOT yet applied to DATM")
    if args.check:
        print("STAGE61 CHECK PASS | no files written");return
    root=R
    dest=root/("stage61_stage49_vs_stage60_full_hard_coverage_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    marker=dest/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Unfinished original source crosswalk; never model forcing.\n")
    payloads={
        "ten_site_source_hard_coverage_summary.csv":summ,
        "original_hard_events_not_in_Stage60_patch.csv":uncovered,
        "all_26432_original_review_events_stage60_status.csv":a,
        "stage60_patch_source_review_membership.csv":b}
    digests={}
    for name,frame in payloads.items():
        file=dest/name
        frame.to_csv(file,index=False)
        digests[name]=sha(file)
    if (sha(s49/F49)!=pins["stage49_report_sha256"] or
        sha(S60/F60)!=pins["stage60_patch_sha256"] or
        sha(S58/"4884_final_original_tower_temperature_policy.csv")!=pins["stage58_report_sha256"]):
        raise ValueError("Upstream source mutated during Stage61 audit")
    manifest={"schema":"STAGE61_BATCH02_ORIGINAL_STAGE49_HARD_VS_STAGE60_CROSSWALK_v1",
        "stage49_source":str(s49),"stage60_source":str(S60),"stage58_source":str(S58),
        "original_hard_total":26332,"original_unique_review":26432,
        "stage60_total_candidate":4411,"stage60_currently_applied_to_forcing":0,
        "original_hard_covered_by_candidate":int((a.hard_original&a.selected_in_Stage60_4411).sum()),
        "original_hard_not_covered":len(uncovered),
        "stage60_candidate_not_in_stage49_original_review":int((~b.is_in_Stage49_original_hard_or_dry_review).sum()),
        "input_sha256":pins,"output_sha256":digests,
        "no_source_or_model_writes":True,"approved_for_DATM":False}
    (dest/"coverage_manifest.json").write_text(
        json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    marker.unlink()
    print("STAGE61 AUDIT PASS | original hard anomalies reconciled to selected 4411 exact times")
    print("REPORT",dest)
    print("NO RAW, NETCDF, DATM, CIME, SPINUP OR SLURM CHANGES")
if __name__=="__main__":
    main()

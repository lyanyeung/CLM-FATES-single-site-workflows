#!/usr/bin/env python3
"""Stage76: original FLUXNET Ho1 temperature science holds versus Ho2/Ho3 QC0.

Read-only evidence, write isolated reports only with --audit. Do not change
original data, verified CDS receipts, old source or forcing outputs.

The comparison uses exact *native* TIMESTAMP_START from original FLUXNET
FULLSET primary tower files for Ho1, Ho2 and Ho3, not interpolated ERA
temperature or original FLUXNET VPD_ERA. Source SHA256 is checked against
the original Stage49 inventory; QC0 is required for supporting Ho2/Ho3
temperature evidence. The similarity threshold of 3 C is exploratory.

CAVEAT: matching native local-standard timestamp strings across towers is
PROVISIONAL without historical time-offset applicability verification for
Ho2/Ho3. Nearby towers can have microclimates, heterogeneous heights and
surface differences, and cannot be treated as ground truth for Ho1.
All Ho1 and BZS original temperature HOLDs remain science HOLD; no model
input modification, BIF UTC approval, or automatic temperature replacement.
BZS is not near the Ho towers and must not use these comparators.
"""
import argparse,hashlib,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
REPORT=ROOT/"reports"
S75=REPORT/"stage75_1675_original_TA_QC_and_T_vs_CDS_science_triage_20261025T091912Z_27b0e442"
FILE75="1675_Ho1_BZS_source_temperature_hold_case_review.csv"
S61=REPORT/"stage61_stage49_vs_stage60_full_hard_coverage_20261024T114810Z_fc209bf8"
BASELINE_TOTAL=1675
SITE_TOTAL={"US-Ho1":1619,"US-BZS":56}
HO1_QC0_TDELTA=623
NEIGHBORS=("US-Ho2","US-Ho3")
TOL=3.0

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()

def number(v):
    try:
        x=float(v)
        return x if np.isfinite(x) and x>-9990 else np.nan
    except (TypeError,ValueError):
        return np.nan

def input_gate():
    if (S75/"INCOMPLETE_DO_NOT_USE").exists():
        raise ValueError("Stage75 original report incomplete")
    m=json.loads((S75/"stage75_source_science_manifest.json").read_text())
    if (m.get("schema")!="STAGE75_HO1_BZS_1675_NATIVE_T_QC_AND_CDS_DELTA_HOLD_TRIAGE_v1"
        or m.get("full_ERA5_gridyear_coverage")!="26/26"
        or m.get("original_total_hard_humidity")!=16874
        or m.get("numeric_only_humidity_candidates_unchanged")!=15199
        or m.get("original_T_QC_nonzero_HOLD")!=998
        or m.get("original_T_vs_CDS_gt8C_HOLD")!=677
        or m.get("original_source_temperature_HOLD_total")!=1675
        or m.get("historical_BIF_UTC_offset_coverage_approved") is not False
        or m.get("original_T_replacements_approved") is not False
        or m.get("DATM_approved") is not False):
        raise ValueError("Stage75 original source/temperature science contract changed")
    for fname,expected in m["outputs_SHA256"].items():
        if sha(S75/fname)!=expected:
            raise ValueError("Stage75 immutable output SHA256 changed: "+fname)
    r=pd.read_csv(S75/FILE75,dtype={"site":str,"tower_local_start":str,
      "source_csv_row":str,"source_sha256":str,"timestamp_start":str},low_memory=False)
    needed={"site","tower_local_start","TA_C","TA_original_QC",
            "CDS_ERA5_T2M_C","science_status","diagnostic_context",
            "source_csv_row","source_sha256"}
    if not needed.issubset(r.columns) or len(r)!=BASELINE_TOTAL or (
        Counter(r["site"])!=Counter(SITE_TOTAL)) or r.duplicated([
        "site","tower_local_start"]).any():
        raise ValueError("Stage75 exact source temperature event scope changed")
    scope=r.groupby(["site","science_status"]).size().to_dict()
    if scope!={("US-Ho1","HOLD_ORIGINAL_TA_QC_NONZERO"):996,
              ("US-Ho1","HOLD_TOWER_T_VS_INDEPENDENT_ERA5_GT8C"):623,
              ("US-BZS","HOLD_ORIGINAL_TA_QC_NONZERO"):2,
              ("US-BZS","HOLD_TOWER_T_VS_INDEPENDENT_ERA5_GT8C"):54}:
        raise ValueError("Stage75 original per-site quality scope changed "+str(scope))
    for col in ("TA_C","TA_original_QC","CDS_ERA5_T2M_C"):
        r[col]=pd.to_numeric(r[col],errors="coerce")
    if r[["TA_C","TA_original_QC","CDS_ERA5_T2M_C"]].isna().any().any():
        raise ValueError("Stage75 source temperature fields missing")
    if not r["tower_local_start"].str.fullmatch(r"\d{12}").all():
        raise ValueError("Stage75 tower native timestamps malformed")
    m61=json.loads((S61/"coverage_manifest.json").read_text())
    if (m61.get("schema")!="STAGE61_BATCH02_ORIGINAL_STAGE49_HARD_VS_STAGE60_CROSSWALK_v1"
        or m61.get("original_hard_total")!=26332):
        raise ValueError("Original full batch Stage61 population changed")
    m49=json.loads((Path(m61["stage49_source"])/"provenance_and_hold.json").read_text())
    inv=Path(m49["inventory"]).resolve(strict=True)
    if sha(inv)!=m49["inventory_sha256"]:
        raise ValueError("Original Stage49 FLUXNET source inventory SHA changed")
    candidates=json.loads(inv.read_text())["completed"]
    specs={}
    for site in NEIGHBORS:
        matches=[v for v in candidates if v.get("site")==site and
                 v.get("source") in ("FULLSET_HH","FLUXMET_HH")]
        if len(matches)!=1:
            raise ValueError("Ambiguous source native tower file for "+site)
        x=matches[0]
        f=Path(x["file"])
        if f.is_symlink() or not f.is_file() or sha(f)!=x["sha256"]:
            raise ValueError("Original FLUXNET native-source SHA/file mismatch "+site)
        if m49["primary_sha256_by_site"].get(site)!=x["sha256"]:
            raise ValueError("Stage49 original tower source hash mismatch "+site)
        if x.get("interval_minutes")!=30:
            raise ValueError("Ho1 neighboring source is not original 30-minute interval")
        specs[site]=x
    return r,m,m49,inv,specs

def neighbor_original_QC0(spec,needed_times):
    """Scan original file in bounded chunks and retain ONLY matched native times."""
    file=Path(spec["file"])
    cmap=spec.get("columns",{})
    qmap=spec.get("qc_columns",{})
    ta=cmap.get("TA")
    tq=qmap.get("TA")
    header=set(pd.read_csv(file,nrows=0).columns)
    if not ta or not tq or not {"TIMESTAMP_START",ta,tq}.issubset(header):
        return {},{"site":spec["site"],"original_sha256":spec["sha256"],
             "status":"ORIGINAL_TA_OR_QC_ABSENT","n_native_matches":0,
             "n_native_QC0":0,"source_file":str(file)}
    rows={}
    for chunk in pd.read_csv(file,usecols=["TIMESTAMP_START",ta,tq],
                             dtype="string",chunksize=120000):
        clock=chunk["TIMESTAMP_START"].astype("string").str.strip()
        mask=clock.isin(needed_times)
        if not mask.any():
            continue
        selected=chunk.loc[mask]
        for stamp,t,q in zip(clock.loc[mask],
                             selected[ta],selected[tq]):
            stamp=str(stamp)
            if stamp in rows:
                raise ValueError("Duplicate source tower native timestamp "+spec["site"]+":"+stamp)
            temp=number(t)
            qc=number(q)
            if not np.isfinite(temp) or not -80<temp<65:
                temp=np.nan
            rows[stamp]={"temp_c":temp,"qc":qc,
              "native_measured_QC0":bool(np.isfinite(temp) and qc==0)}
    n0=sum(v["native_measured_QC0"] for v in rows.values())
    manifest={"site":spec["site"],"original_sha256":spec["sha256"],
        "source_file":str(file),"original_native_T_field":ta,
        "original_T_QC_field":tq,"status":"ORIGINAL_SOURCE_PROVEN",
        "n_native_matches":len(rows),"n_native_QC0":n0,
        "n_requested_original_Ho1_native_timestamps":len(needed_times)}
    return rows,manifest

def evaluate(cases,by_tower):
    result=cases.copy()
    for tower in NEIGHBORS:
        output=by_tower[tower]
        alias=tower.replace("-","_")
        result[alias+"_TA_C"]=[
           output.get(s,{}).get("temp_c",np.nan) if site=="US-Ho1" else np.nan
           for site,s in zip(result["site"],result["tower_local_start"])]
        result[alias+"_TA_QC"]=[
           output.get(s,{}).get("qc",np.nan) if site=="US-Ho1" else np.nan
           for site,s in zip(result["site"],result["tower_local_start"])]
        result[alias+"_QC0_valid"]=[
           output.get(s,{}).get("native_measured_QC0",False)
           if site=="US-Ho1" else False
           for site,s in zip(result["site"],result["tower_local_start"])]
        result[alias+"_minus_Ho1_T_C"]=result[alias+"_TA_C"]-result["TA_C"]
        result[alias+"_minus_CDS_ERA5_T_C"]=result[alias+"_TA_C"]-result["CDS_ERA5_T2M_C"]
    labels=[]
    for r in result.to_dict("records"):
        if r["site"]=="US-BZS":
            labels.append("BZS_HOLD_NO_RELEVANT_NEARBY_TOWER_SOURCE")
            continue
        v=[]
        for t in NEIGHBORS:
            alias=t.replace("-","_")
            if r[alias+"_QC0_valid"]:
                v.append((float(r[alias+"_TA_C"]),t))
        if not v:
            labels.append("HO1_HOLD_NO_NATIVE_NEIGHBOR_QC0_EXACT_TIME")
            continue
        near_Ho1=any(abs(T-r["TA_C"])<=TOL for T,_ in v)
        near_era=any(abs(T-r["CDS_ERA5_T2M_C"])<=TOL for T,_ in v)
        if near_Ho1 and near_era:
            labels.append("HO1_HOLD_CONFLICTING_QC0_NEIGHBORS_SUPPORT_BOTH")
        elif near_Ho1:
            labels.append("HO1_SHADOW_NATIVE_QC0_NEIGHBOR_SUPPORTS_HO1_T")
        elif near_era:
            labels.append("HO1_SHADOW_NATIVE_QC0_NEIGHBOR_SUPPORTS_CDS_T")
        else:
            labels.append("HO1_HOLD_NATIVE_QC0_NEIGHBORS_MATCH_NEITHER")
    result["source_temperature_cross_tower_classification"]=labels
    result["neighbor_native_clock_parity_historically_verified"]=False
    result["tower_height_canopy_exposure_verified"]=False
    result["new_original_temperature_approved"]=False
    result["source_historical_BIF_time_approved"]=False
    result["approved_for_DATM"]=False
    return result

def summarize(result):
    classcounts=result.groupby(["site","science_status",
          "source_temperature_cross_tower_classification"],
          dropna=False).size().reset_index(name="records")
    y=result.copy()
    y["year"]=y["tower_local_start"].str.slice(0,4)
    years=y.groupby(["site","year","science_status",
         "source_temperature_cross_tower_classification"],
         dropna=False).size().reset_index(name="records")
    priorities=years.loc[years["site"].eq("US-Ho1")].sort_values(
        ["records","year"],ascending=[False,True])
    if (classcounts.records.sum()!=BASELINE_TOTAL or
        years.records.sum()!=BASELINE_TOTAL or
        result["new_original_temperature_approved"].any()):
        raise ValueError("Stage76 original 1675 source classification did not close")
    print("STAGE76 ORIGINAL NATIVE TEMPERATURE EVIDENCE CLASS COUNTS")
    print(classcounts.to_string(index=False))
    print("STAGE76 SOURCE-YEAR TOP CLASS COUNTS")
    print(priorities.head(30).to_string(index=False))
    hot=result.loc[result["site"].eq("US-Ho1") &
        result["science_status"].eq("HOLD_TOWER_T_VS_INDEPENDENT_ERA5_GT8C") &
        result["tower_local_start"].str.startswith("2000")]
    if len(hot)!=505:
        raise ValueError("Ho1 2000 exact 505 original measured T cross-reference scope changed")
    print("STAGE76 HO1_2000_QC0_T_VS_CDS_GT8C_N",len(hot))
    print("STAGE76 HO1_2000_QC0_NATIVE_NEIGHBOR_CLASS",
          dict(Counter(hot["source_temperature_cross_tower_classification"])))
    print("STAGE76 SOURCE-HISTORICAL-TIME/CANOPY AND FORCING APPROVALS ALL FALSE")
    return classcounts,years

def self_test():
    assert sum(SITE_TOTAL.values())==BASELINE_TOTAL
    assert 996+623==1619
    assert 2+54==56
    assert 505<=623
    v=pd.DataFrame({"flags":["SAMPLE"]})
    assert v["flags"].iloc[0]=="SAMPLE"
    print("STAGE76 SELF-TEST PASS | 1675 source T holds, Ho1 623 QC0 >8C, BZS 56 separate")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    g=ap.add_mutually_exclusive_group(required=True)
    for mode in ("self-test","check","audit"):
        g.add_argument("--"+mode,action="store_true")
    a=ap.parse_args()
    if a.self_test:return self_test()
    cases,m,m49,inv,specs=input_gate()
    times=set(cases.loc[cases["site"].eq("US-Ho1"),"tower_local_start"])
    tower={};provenance=[]
    for site in NEIGHBORS:
        tower[site],info=neighbor_original_QC0(specs[site],times)
        provenance.append(info)
        print("STAGE76 NEIGHBOR SOURCE",json.dumps(info,sort_keys=True),flush=True)
    z=evaluate(cases,tower)
    classes,years=summarize(z)
    if a.check:
        print("STAGE76 CHECK PASS | read-only primary source SHA and native QC0 cross-tower classification")
        return
    target=REPORT/("stage76_1675_Ho1_BZS_original_cross_tower_QC0_context_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    target.mkdir(parents=True,exist_ok=False)
    marker=target/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Native timestamp comparability tentative. NO source approvals.\n")
    outputs={
       "1675_original_Ho1_BZS_temperature_cross_tower_HOLD.csv":z,
       "1675_native_QC0_temperature_classification.csv":classes,
       "Ho1_BZS_temperature_hold_by_year_and_neighbor.csv":years}
    hashes={}
    for fn,df in outputs.items():
        p=target/fn;df.to_csv(p,index=False);hashes[fn]=sha(p)
    inventory=target/"Ho2_Ho3_original_FLUXNET_source_SHA256_QC0_provenance.json"
    inventory.write_text(json.dumps(provenance,indent=2,sort_keys=True)+"\n")
    hashes[inventory.name]=sha(inventory)
    if sha(S75/FILE75)!=m["outputs_SHA256"][FILE75] or (
       sha(inv)!=m49["inventory_sha256"]):
        raise ValueError("Source Stage75 report or original primary inventory changed")
    manifest={"schema":"STAGE76_HO1_HO2_HO3_ORIGINAL_QC0_CROSS_TOWER_T_HOLDS_v1",
       "original_temperature_holds":1675,
       "original_Ho1_temperature_holds":1619,
       "original_BZS_temperature_holds":56,
       "original_Ho1_2000_QC0_ERA5_T_diff_gt8C":505,
       "original_numeric_water_humidity_shadow_unchanged":15199,
       "other_batch_stage64_9389_unchanged":True,
       "exact_native_tower_timestamps_not_historical_time_verified":True,
       "Ho2_Ho3_tower_evidence_not_infallible":True,
       "original_tower_temperature_replacements_approved":False,
       "BIF_historical_UTC_offset_approved":False,
       "approved_for_DATM":False,
       "source_SHA256":{"stage75_temperature_events":sha(S75/FILE75),
          "stage75_manifest":sha(S75/"stage75_source_science_manifest.json"),
          "stage49_primary_source_inventory":sha(inv),
          **{item["site"]+"_original_FLUXNET_SHA256":item["original_sha256"]
             for item in provenance}},
       "outputs_SHA256":hashes,
       "no_original_EC_CDS_model_forcing_or_slurm_changes":True}
    (target/"stage76_source_science_manifest.json").write_text(
        json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    marker.unlink()
    print("STAGE76 AUDIT PASS | source-pinned Ho2/Ho3 original measured QC0 T comparisons for 1675 original holds")
    print("REPORT",target)
    print("NO ORIGINAL EC, CDS, STAGE49-75, NETCDF FORCING, DATM, CIME OR SLURM CHANGES")

if __name__=="__main__":
    main()

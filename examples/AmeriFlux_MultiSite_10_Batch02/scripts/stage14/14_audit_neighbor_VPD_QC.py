#!/usr/bin/env python3
"""Stage14: READ-ONLY source-quality audit for 14 Stage11 humidity HOLD rows.

Check nearby source VPD-derived RH separately by original VPD_F_QC:
0 measured, 1 high-quality gapfilled, 2 downscaled ERA.
No model/forcing input modification or Slurm jobs. Output optional, under HOME.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

BASE=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
STAGE11=BASE/"stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
STAGE13F=Path.home()/"AmeriFlux_Batch02_stage13f_provenance_20261022T031222Z_3c5c163d"
EXPECTED={"US-EML":1,"US-GLE":3,"US-ICt":10}
CLASSES={0:"MEASURED_QC0",1:"GAPFILLED_QC1",2:"ERA_DOWNSCALED_QC2"}

def digest(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()

def parse_time(s):
    return pd.to_datetime(s.astype(str).str.strip().str.replace(r"\.0$","",regex=True),format="%Y%m%d%H%M")

def normal(s):
    v=pd.to_numeric(s,errors="coerce")
    return v.mask((v<=-9990) | ~np.isfinite(v))

def inspect(site,path,times):
    head=set(pd.read_csv(path,nrows=0).columns)
    if not {"TIMESTAMP_START","TA_F","VPD_F"}.issubset(head):
        raise ValueError("Missing required source columns: "+site)
    fields=["TIMESTAMP_START","TA_F","VPD_F"]+[v for v in
            ("VPD_F_QC","TA_F_QC","RH","RH_QC") if v in head]
    a=pd.read_csv(path,usecols=fields,dtype={"TIMESTAMP_START":str})
    a["time"]=parse_time(a.TIMESTAMP_START)
    if a.time.duplicated().any():raise ValueError("Duplicated source time: "+site)
    for col in fields[1:]:a[col]=normal(a[col])
    if "VPD_F_QC" not in a:a["VPD_F_QC"]=np.nan
    if "RH" not in a:a["RH"]=np.nan
    with np.errstate(all="ignore"):
        es=6.112*np.exp(17.67*a.TA_F/(a.TA_F+243.5))
        a["RH_from_VPD_pct"]=100*(1-a.VPD_F/es)
    a["physical"]=a.RH_from_VPD_pct.gt(0)&a.RH_from_VPD_pct.le(100.05)
    a["raw_RH_ok"]=a.RH.gt(0)&a.RH.le(100)
    a["QC_class"]=a.VPD_F_QC.map(CLASSES).fillna("UNKNOWN_QC")
    events=[]
    near_all=pd.Series(False,index=a.index)
    for time in times:
        time=pd.Timestamp(time)
        ix=a.time.eq(time)
        if ix.sum()!=1:raise ValueError("Missing original hold time: "+site+" "+str(time))
        sel=a.time.between(time-pd.Timedelta("24h"),time+pd.Timedelta("24h"))
        near_all|=sel
        near=a.loc[sel & ~ix]
        row=dict(site=site,time=str(time),source_QC_at_hold=
                 float(a.loc[ix,"VPD_F_QC"].iloc[0]) if pd.notna(a.loc[ix,"VPD_F_QC"].iloc[0]) else None,
                 n_raw_RH_valid=int(near.raw_RH_ok.sum()))
        for code,label in CLASSES.items():
            ok=near.loc[near.VPD_F_QC.eq(code)&near.physical]
            row[label+"_n"]=len(ok)
            row[label+"_median_RH_pct"]=float(ok.RH_from_VPD_pct.median()) if len(ok) else None
        unknown=near.loc[~near.VPD_F_QC.isin(CLASSES)&near.physical]
        row["UNKNOWN_QC_n"]=len(unknown)
        events.append(row)
    unique=a.loc[near_all].copy()
    stats=unique.groupby("QC_class").agg(
        unique_window_rows=("time","size"),
        physical_VPD_derived_RH=("physical","sum"),
        valid_raw_RH=("raw_RH_ok","sum")).reset_index()
    stats["site"]=site
    return pd.DataFrame(events),stats

def run(args):
    s11=args.stage11_root.resolve()
    s13=args.stage13f_root.resolve()
    if not (s11/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("No Stage11 scientific HOLD marker")
    if not (s13/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("No Stage13f scientific HOLD marker")
    m=json.loads((s11/"manifest.json").read_text())
    if m.get("scientific_status")!="HOLD_INDEPENDENT_VALIDATION_REQUIRED":
        raise ValueError("Stage11 manifest science status differs")
    e=json.loads((Path(m["source_stage08"])/"exact_input_manifest.json").read_text())
    info={x["site"]:x for x in e["sites"]}
    allrows=pd.read_csv(s11/"cold_humidity_repair_proposals.csv")
    holds=allrows.loc[allrows.decision.eq("HOLD_NO_SUPPORTED_ANALOGUE")]
    if len(holds)!=14 or any(holds.site.eq(s).sum()!=n for s,n in EXPECTED.items()):
        raise ValueError("Original HOLD set changed")
    receipts={str(s11/"manifest.json"):digest(s11/"manifest.json"),
              str(s13/"manifest.json"):digest(s13/"manifest.json")}
    result=[];stats=[]
    for site in EXPECTED:
        file=Path(info[site]["primary"]).resolve()
        pinned=m["input_hashes"].get(str(file))
        if not pinned or digest(file)!=pinned:raise ValueError("Pinned source altered: "+site)
        receipts[str(file)]=pinned
        events,qc=inspect(site,file,holds.loc[holds.site.eq(site),"time"].tolist())
        result.append(events);stats.append(qc)
    audit=pd.concat(result,ignore_index=True)
    unique=pd.concat(stats,ignore_index=True)
    print("STAGE14: 14 original HOLD records; +/-24h VPD-derived RH stratified by source QC")
    print("OFFICIAL DEFINITIONS: QC0=measured; QC1=good gapfill; QC2=downscaled ERA")
    print(audit.to_string(index=False))
    print("\nDEDUPLICATED WINDOW QC DISTRIBUTIONS")
    print(unique.to_string(index=False))
    print("HOLD EVENTS WITH PHYSICAL MEASURED-QC0 NEIGHBORS:",
          int((audit.MEASURED_QC0_n>0).sum()),"/14")
    print("CAUTION: even measured VPD-derived RH is not an independent direct RH sensor.")
    if any(digest(p)!=val for p,val in receipts.items()):
        raise ValueError("Original files changed during analysis")
    if not args.write_report:
        print("STAGE14 CHECK ONLY: nothing written")
        return 0
    out=(args.output_root.expanduser().resolve() if args.output_root else
         Path.home()/("AmeriFlux_Batch02_stage14_neighbor_QC_"+
                      datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8]))
    if out.exists() or any(out==x or out in x.parents or x in out.parents for x in (s11,s13,BASE)):
        raise ValueError("Unsafe/existing report output")
    out.mkdir(parents=True,exist_ok=False)
    audit.to_csv(out/"14_hold_QC_stratified_neighbors.csv",index=False)
    unique.to_csv(out/"deduplicated_neighborhood_QC.csv",index=False)
    (out/"manifest.json").write_text(json.dumps(dict(
        inputs_sha256=receipts,script_sha256=digest(Path(__file__)),
        science_status="SOURCE_QC_PROVENANCE_ONLY_NOT_FOR_DATM",
        model_files_changed=False),indent=2)+"\n")
    (out/"DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "Quality source audit only. No forcing approval.\n")
    print("STAGE14 REPORT:",out)
    return 0

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage11-root",type=Path,default=STAGE11)
    p.add_argument("--stage13f-root",type=Path,default=STAGE13F)
    p.add_argument("--write-report",action="store_true")
    p.add_argument("--output-root",type=Path)
    raise SystemExit(run(p.parse_args()))

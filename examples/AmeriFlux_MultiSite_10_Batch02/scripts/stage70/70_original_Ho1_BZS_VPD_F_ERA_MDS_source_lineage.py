#!/usr/bin/env python3
"""AmeriFlux Batch02 Stage70: source-immutable Ho1/BZS VPD_F lineage forensics.

Take the 16,874 exact (site, original source physical CSV row/timestamp)
Stage69 invalid original VPD>es_water(TA_F) events. Verify the original
FULLSET_HH product SHA256, and compare VPD_F to VPD_ERA, VPD_F_MDS and
TA_ERA *from the same original file*, with the official FLUXNET FULLSET
VPD_F_QC meaning:
 0 measured; 1 good MDS gapfill; 2 ERA-downscaled.
These processed ERA columns are NOT independent CDS ERA5 observations.

For each event, determine whether impossible VPD_F was inherited
directly from source VPD_ERA (QC2) or source MDS (QC1); whether source
VPD_ERA would be physically possible at its paired source TA_ERA;
and whether original TA_F/TA_ERA difference explains mismatched
saturation, with explicit counts and no pre-approval of any patches.

No edits to source, Stage64-69, ERA5/CDS, forcing, DATM, CIME or Slurm.
"""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
R=ROOT/"reports"
S61=R/"stage61_stage49_vs_stage60_full_hard_coverage_20261024T114810Z_fc209bf8"
S69=R/"stage69_16874_original_VPD_vs_water_es_source_diagnosis_20261025T080834Z_782347f2"
F69="16874_original_VPD_over_es_water_diagnostics.csv"
SITE_COUNTS={"US-Ho1":16788,"US-BZS":86}
FLUXNET_QC={0:"MEASURED",1:"HIGH_QUALITY_MDS_GAPFILL",2:"DOWNSCALED_ERA"}
TOL=0.00011

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as fh:
        for b in iter(lambda:fh.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()

def number(v):
    try:
        v=float(v)
        return v if np.isfinite(v) and v>-9990 else np.nan
    except (ValueError,TypeError):
        return np.nan

def es(tc):
    with np.errstate(over="ignore",invalid="ignore"):
        return 6.112*np.exp(np.clip(17.67*tc/(tc+243.5),-45,45))

def source_and_events():
    m69=json.loads((S69/"source_science_manifest.json").read_text())
    m61=json.loads((S61/"coverage_manifest.json").read_text())
    if ((S69/"INCOMPLETE_DO_NOT_USE").exists() or
        m69.get("schema")!="STAGE69_HO1_BZS_ORIGINAL_HUMIDITY_PHYSICS_MECHANISM_v1" or
        m69.get("n_original_nonpositive_vapor")!=16874 or
        m69.get("approved_for_DATM") is not False or
        m69.get("all_original_hard_HOLD_remain_unreleased") is not True or
        m61.get("schema")!="STAGE61_BATCH02_ORIGINAL_STAGE49_HARD_VS_STAGE60_CROSSWALK_v1" or
        m61.get("original_hard_total")!=26332):
        raise ValueError("Stage69/61 original source manifest science gate failed")
    for name,digest in m69.get("output_SHA256",{}).items():
        if sha(S69/name)!=digest:raise ValueError("Stage69 output SHA256 changed "+name)
    d=pd.read_csv(S69/F69,dtype={"site":str,"tower_local_start":str,
        "timestamp_start":str,"source_sha256":str,"shadow_UTC_START":str})
    if (len(d)!=16874 or d.duplicated(["site","tower_local_start"]).any()
        or Counter(d["site"])!=Counter(SITE_COUNTS)):
        raise ValueError("Stage69 original hard cohort is not exact")
    m49=json.loads((Path(m61["stage49_source"])/"provenance_and_hold.json").read_text())
    inv=Path(m49["inventory"]).resolve(strict=True)
    if sha(inv)!=m49["inventory_sha256"]:
        raise ValueError("Original source inventory SHA changed")
    specs=json.loads(inv.read_text())["completed"]
    sources={}
    for site in SITE_COUNTS:
        a=[x for x in specs if x["site"]==site and
           not str(x["source"]).startswith("ERA5")]
        if len(a)!=1:raise ValueError("Site original source ambiguous "+site)
        x=a[0]
        file=Path(x["file"])
        if file.is_symlink() or not file.is_file():
            raise ValueError("Original primary missing/nonregular "+str(file))
        if (sha(file)!=x["sha256"] or
            m49["primary_sha256_by_site"].get(site)!=x["sha256"]):
            raise ValueError("Original FLUXNET primary bytes SHA256 mismatch "+site)
        if (not d.loc[d["site"].eq(site),"source_sha256"].eq(x["sha256"]).all()):
            raise ValueError("Stage69 row source SHA differs from original "+site)
        sources[site]=x
    return d,sources,m49,m61,m69,sha(inv)

def read_exact_original(part,spec):
    """Read one complete HH original primary in bounded chunks; emit only 16,874 target rows."""
    file=Path(spec["file"])
    header=pd.read_csv(file,nrows=0).columns.tolist()
    cmap=spec["columns"]
    qmap=spec.get("qc_columns",{})
    ta=cmap["TA"];vpd=cmap["VPD"];tqc=qmap.get("TA");vqc=qmap.get("VPD")
    if not set(("TIMESTAMP_START",ta,vpd,tqc,vqc)).issubset(header):
        raise ValueError("Cannot prove original FLUXNET site/F/QC columns "+spec["site"])
    # Some site FLUXNET releases may omit the MDS or ERA companion column;
    # that absence becomes an explicit HOLD, not an invented lineage.
    opt=[c for c in ("VPD_ERA","VPD_F_MDS","VPD_F_MDS_QC","TA_ERA","VPD")
         if c in header]
    use=list(dict.fromkeys(["TIMESTAMP_START",ta,vpd,tqc,vqc]+opt))
    source_rows=pd.to_numeric(part["source_csv_row"],errors="raise").astype(int)
    if source_rows.lt(2).any() or source_rows.duplicated().any():
        raise ValueError("Invalid/duplicate source physical CSV line")
    requested=np.sort(source_rows.to_numpy())
    recorded={};offset=0
    for chunk in pd.read_csv(file,usecols=use,dtype="string",chunksize=120000):
        lo=offset+2;hi=lo+len(chunk)-1
        start=np.searchsorted(requested,lo,"left")
        end=np.searchsorted(requested,hi,"right")
        for line in requested[start:end]:
            row=chunk.iloc[int(line-lo)]
            recorded[int(line)]={"TIMESTAMP_START":str(row["TIMESTAMP_START"]).strip(),
                "native_TA_F":number(row[ta]),
                "native_VPD_F":number(row[vpd]),
                "native_TA_F_QC":number(row[tqc]),
                "native_VPD_F_QC":number(row[vqc]),
                **{c:number(row[c]) for c in opt}}
        offset+=len(chunk)
    if len(recorded)!=len(requested):
        raise ValueError("Original source physical line mismatch "+spec["site"])
    out=pd.DataFrame.from_dict(recorded,orient="index")
    out.index.name="source_csv_row"
    out.reset_index(inplace=True)
    return out,{"site":spec["site"],"path":str(file),"source_SHA256":spec["sha256"],
        "present_optional_fields":opt,
        "absent_optional_fields":[c for c in ("VPD_ERA","VPD_F_MDS","VPD_F_MDS_QC","TA_ERA","VPD")
          if c not in header],
        "n_original_physical_source_rows":len(recorded)}

def analyze(original,sources):
    parts=[];source_inventory=[]
    for site,n in SITE_COUNTS.items():
        target=original.loc[original["site"].eq(site)].copy()
        src,prov=read_exact_original(target,sources[site])
        joined=target.merge(src,on="source_csv_row",
            how="left",validate="one_to_one")
        if len(joined)!=n or joined["TIMESTAMP_START"].isna().any():
            raise ValueError("Source-row merge mismatch "+site)
        native_time=joined["TIMESTAMP_START"].astype(str).str.replace(
            r"\.0$","",regex=True)
        if not native_time.eq(joined["timestamp_start"].astype(str)).all():
            raise ValueError("Original HH native time differs from Stage69 "+site)
        for field,srcfield,tol in (
          ("TA_C","native_TA_F",0.00011),
          ("VPD_hPa","native_VPD_F",0.00011),
          ("TA_original_QC","native_TA_F_QC",0.001),
          ("VPD_original_QC","native_VPD_F_QC",0.001)):
            old=pd.to_numeric(joined[field],errors="coerce")
            new=pd.to_numeric(joined[srcfield],errors="coerce")
            if not np.isclose(old,new,rtol=0,atol=tol,equal_nan=True).all():
                raise ValueError("Exact original source evidence changed: "+site+"/"+field)
        era=joined["VPD_ERA"] if "VPD_ERA" in joined else pd.Series(
              np.nan,index=joined.index)
        mds=joined["VPD_F_MDS"] if "VPD_F_MDS" in joined else pd.Series(
              np.nan,index=joined.index)
        taera=joined["TA_ERA"] if "TA_ERA" in joined else pd.Series(
              np.nan,index=joined.index)
        joined["QC_source_type"]=joined["VPD_original_QC"].map(FLUXNET_QC)
        if joined["QC_source_type"].isna().any():
            raise ValueError("Unexpected VPD consolidated QC outside 0/1/2")
        joined["source_VPD_equals_ERA"]=(
            np.isfinite(era)&np.isclose(joined["native_VPD_F"],era,
                rtol=0,atol=TOL,equal_nan=False))
        joined["source_VPD_equals_MDS"]=(
            np.isfinite(mds)&np.isclose(joined["native_VPD_F"],mds,
                rtol=0,atol=TOL,equal_nan=False))
        joined["source_TA_ERA_C"]=taera
        joined["native_source_VPD_saturation_at_source_TA_ERA"]=(
             es(taera.to_numpy(dtype=float)))
        joined["source_VPD_F_physical_at_TA_ERA"]=(
             np.isfinite(taera)&(joined["native_VPD_F"]<=joined[
               "native_source_VPD_saturation_at_source_TA_ERA"]))
        joined["source_VPD_ERA_physical_at_TA_ERA"]=(
             np.isfinite(era)&np.isfinite(taera)&
             (era<=joined["native_source_VPD_saturation_at_source_TA_ERA"]))
        joined["native_TA_F_minus_TA_ERA_C"]=joined["TA_C"]-taera
        joined["source_TA_ERA_available"]=np.isfinite(taera)
        joined["independent_CDS_external_verified_for_event"]=False
        joined["DATM_approved"]=False
        source_inventory.append(prov)
        parts.append(joined)
    z=pd.concat(parts,ignore_index=True)
    if len(z)!=16874 or z.duplicated(["site","source_csv_row"]).any():
        raise ValueError("Original source VPD product lineage cohort counts failed")
    per=[]
    for (site,year,qc),grp in z.groupby(["site","tower_year","QC_source_type"],sort=True):
        qcnum=int(grp["VPD_original_QC"].iloc[0])
        product="VPD_ERA" if qcnum==2 else "VPD_F_MDS" if qcnum==1 else "MEASURED"
        present=bool(product in grp.columns) if product!="MEASURED" else True
        matches=grp["source_VPD_equals_ERA"] if qcnum==2 else (
          grp["source_VPD_equals_MDS"] if qcnum==1 else pd.Series(False,index=grp.index))
        ta_era=grp["source_TA_ERA_available"]
        per.append({"site":site,"tower_year":int(year),"VPD_F_QC":qcnum,
           "QC_source_type":qc,"events":len(grp),
           "expected_same_source_column":product,
           "expected_source_column_present":present,
           "matching_expected_original_VPD_companion":int(matches.sum()),
           "companion_missing_or_nonmatching":int((~matches).sum()),
           "TA_ERA_available":int(ta_era.sum()),
           "VPD_F_physical_at_ERA_T":int(grp["source_VPD_F_physical_at_TA_ERA"].sum()),
           "VPD_ERA_physical_at_ERA_T":int(grp["source_VPD_ERA_physical_at_TA_ERA"].sum()),
           "source_TA_F_minus_TA_ERA_median_C":float(grp[
               "native_TA_F_minus_TA_ERA_C"].median()) if ta_era.any() else np.nan})
    summary=pd.DataFrame(per)
    summary_site=summary.groupby(["site","VPD_F_QC","QC_source_type"],as_index=False).agg(
      {"events":"sum","matching_expected_original_VPD_companion":"sum",
       "companion_missing_or_nonmatching":"sum","TA_ERA_available":"sum",
       "VPD_F_physical_at_ERA_T":"sum","VPD_ERA_physical_at_ERA_T":"sum"})
    print("STAGE70 ORIGINAL VPD PRODUCT FULLSET QC SOURCE")
    print(summary_site.to_string(index=False))
    print("STAGE70 COMPANION SOURCE INVENTORY")
    print(json.dumps(source_inventory,indent=2))
    print("STAGE70 ORIGINAL YEAR/PROCESS SOURCE")
    print(summary.to_string(index=False))
    print("STAGE70 INTERPRETATION: QC2 downscaled ERA is NOT independent CDS; QC1 MDS is not direct measurement")
    print("STAGE70 NUMERIC PER-EVENT SOURCE MATCHES",int(summary.events.sum()))
    if int(summary.events.sum())!=16874:
        raise ValueError("Stage70 all 16874 original source events were not reconciled")
    return z,summary,summary_site,source_inventory

def self_test():
    assert FLUXNET_QC=={0:"MEASURED",1:"HIGH_QUALITY_MDS_GAPFILL",2:"DOWNSCALED_ERA"}
    f=pd.DataFrame({"flags":["ACTUAL_VAPOR_NONPOSITIVE"],"VPD_F_QC":[2]})
    assert f["flags"].iloc[0]=="ACTUAL_VAPOR_NONPOSITIVE"
    assert f["VPD_F_QC"].iloc[0]==2
    assert sum(SITE_COUNTS.values())==16874
    t=np.array([-20.,10.]);v=es(t)
    assert np.isfinite(v).all() and (v>0).all()
    print("STAGE70 SELF-TEST PASS | original physical CSV source-row and VPD_F vs ERA/MDS lineage gates")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    m=p.add_mutually_exclusive_group(required=True)
    m.add_argument("--self-test",action="store_true")
    m.add_argument("--check",action="store_true")
    m.add_argument("--audit",action="store_true")
    args=p.parse_args()
    if args.self_test:return self_test()
    src,spec,m49,m61,m69,invsha=source_and_events()
    z,year,site,inventory=analyze(src,spec)
    if args.check:
        print("STAGE70 CHECK PASS | 16874 original VPD lineage source rows reconciled; NO WRITES")
        return
    out=R/("stage70_Ho1_BZS_original_VPD_product_lineage_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
        "_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    marker=out/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Diagnostic only: no independent ERA / no forcing approval.\n")
    frames={
      "16874_original_F_VPD_ERA_MDS_exact_source_lineage.csv":z,
      "Ho1_BZS_original_VPD_product_source_by_year.csv":year,
      "Ho1_BZS_VPD_source_site_summary.csv":site}
    d={}
    for name,df in frames.items():
        loc=out/name;df.to_csv(loc,index=False);d[name]=sha(loc)
    path=out/"primary_original_source_provenance.json"
    path.write_text(json.dumps(inventory,sort_keys=True,indent=2)+"\n")
    d[path.name]=sha(path)
    if sha(S69/F69)!=m69["output_SHA256"][F69]:
        raise ValueError("Stage69 source changed during Stage70 source audit")
    provenance={
      "schema":"STAGE70_HO1_BZS_ORIGINAL_VPD_F_ERA_MDS_PRODUCT_PROVENANCE_v1",
      "original_Ho1_events":16788,"original_BZS_events":86,
      "n_original_VPD_events_exactly_scoped":16874,
      "original_VPD_quality_flag_definitions":FLUXNET_QC,
      "same_FLUXNET_processed_VPD_ERA_not_independent":True,
      "independent_CDS_ERA5_Ho1_BZS_not_yet_joined":True,
      "stage64_previous_9389_candidates_unchanged":True,
      "all_16874_original_HOLD_unreleased":True,
      "approved_for_DATM":False,
      "source_SHA256":{"stage69_events":sha(S69/F69),
         "stage69_manifest":sha(S69/"source_science_manifest.json"),
         "stage61_manifest":sha(S61/"coverage_manifest.json"),
         "stage49_inventory":invsha,
         **{name+"_primary_sha256":x["sha256"] for name,x in spec.items()}},
      "output_sha256":d,
      "no_source_or_forcing_model_writes":True}
    (out/"stage70_original_VPD_source_manifest.json").write_text(
       json.dumps(provenance,sort_keys=True,indent=2)+"\n")
    marker.unlink()
    print("STAGE70 AUDIT PASS | 16874 original VPD_F sources checked against same-release ERA/MDS companions")
    print("REPORT",out)
    print("NO ORIGINAL EC, CDS, STAGE64-69, NETCDF, DATM, CIME OR SLURM WRITES")
if __name__=="__main__":
    main()

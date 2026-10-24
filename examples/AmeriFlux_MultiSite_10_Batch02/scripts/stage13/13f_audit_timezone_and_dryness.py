#!/usr/bin/env python3
"""Stage13f: READ-ONLY UTC-offset and dry-event provenance for Batch02.

Investigate all 14 original Stage11 HOLD rows and the extraordinary US-ICt
low-RH ERA5 pilot period. Inspect site-release BIF time-zone metadata, original
tower RH/VPD/TA and QC, nearby observations, and +/-1 h UTC-offset hypotheses.

This is NOT model forcing. Do not claim approval if the BIF lacks UTC_OFFSET,
and do not use pilot half-hour interpolation as native ERA5 data.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

HOME = Path.home()
BASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
REPORT13E = HOME / "AmeriFlux_Batch02_stage13e_comparison_20261022T030619Z_bc88fdcd"
STAGE11 = BASE / "stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
SITES = ("US-EML", "US-GLE", "US-Ho1", "US-ICh", "US-ICt")
HOLD_COUNTS = {"US-EML":1, "US-GLE":3, "US-Ho1":0, "US-ICh":0, "US-ICt":10}

def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for x in iter(lambda:f.read(1<<20),b""):
            h.update(x)
    return h.hexdigest()

def parse_time(x):
    return pd.to_datetime(x.astype(str).str.strip().str.replace(r"\.0$","",regex=True),
                          format="%Y%m%d%H%M",errors="raise")

def numeric(s):
    x = pd.to_numeric(s, errors="coerce").to_numpy(dtype=float)
    x[~np.isfinite(x) | (x<=-9990)] = np.nan
    return x

def site_bif(item):
    root=Path(item["primary"]).parent
    bf=sorted(root.glob("*_BIF_*.csv"))
    rows=[]
    if len(bf)>1: raise ValueError("Multiple site release BIFs: "+item["site"])
    if bf:
        b=bf[0]
        with b.open("r",encoding="utf-8-sig",newline="") as stream:
            import csv
            table=csv.DictReader(stream)
            if not {"VARIABLE","DATAVALUE"}.issubset(set(table.fieldnames or [])):
                raise ValueError("BIF schema differs: "+str(b))
            for line in table:
                key=str(line.get("VARIABLE") or "").strip()
                if any(x in key.upper() for x in ("UTC_OFFSET","TIME_ZONE","TIMEZONE","GMT_OFFSET")):
                    rows.append(dict(variable=key,value=str(line.get("DATAVALUE") or "").strip(),
                                     siteid=str(line.get("SITE_ID") or "").strip()))
        return dict(site=item["site"],BIF_path=str(b),BIF_sha256=sha(b),
                    relevant_fields=rows,
                    source="RELEASE_BIF",
                    time_zone_evidence_status="BIF_FIELD_REQUIRES_MANUAL_SEMANTIC_CHECK" if rows
                        else "NOT_ESTABLISHED_FROM_RELEASE_BIF")
    if item["site"]!="US-Ho1":
        raise ValueError("Unexpected missing BIF for "+item["site"])
    return dict(site=item["site"],BIF_path=None,BIF_sha256=None,
                relevant_fields=[],source="OLDER_FULLSET_NO_BIF",
                time_zone_evidence_status="NOT_ESTABLISHED_SITE_BADM_REQUIRED")

def source_nearby(item, stamps):
    source=Path(item["primary"]).resolve()
    if not source.is_file():
        raise ValueError("Site primary file missing: "+str(source))
    header=set(pd.read_csv(source,nrows=0).columns)
    mandatory={"TIMESTAMP_START","TA_F","VPD_F"}
    if not mandatory.issubset(header):
        raise ValueError("Missing original meteorology columns")
    cols=["TIMESTAMP_START","TA_F","VPD_F"] + [
        x for x in ("TA_F_QC","VPD_F_QC","RH","RH_QC") if x in header]
    raw=pd.read_csv(source,usecols=cols,dtype={"TIMESTAMP_START":str})
    raw["time"]=parse_time(raw.TIMESTAMP_START)
    if raw.time.duplicated().any(): raise ValueError("Duplicate tower timestamps")
    for col in cols[1:]:
        raw[col]=numeric(raw[col])
    if "RH" not in raw: raw["RH"]=np.nan
    if "RH_QC" not in raw: raw["RH_QC"]=np.nan
    if "VPD_F_QC" not in raw: raw["VPD_F_QC"]=np.nan
    es=6.112*np.exp(17.67*raw.TA_F/(raw.TA_F+243.5))
    raw["RH_from_tower_VPD"]=100*(1-raw.VPD_F/es)
    validraw=(raw.RH>0)&(raw.RH<=100)
    validvpd=(raw.RH_from_tower_VPD>0)&(raw.RH_from_tower_VPD<=100.05)
    results=[]
    for stamp in stamps:
        target=pd.Timestamp(stamp)
        nearby=raw.loc[raw.time.between(target-pd.Timedelta("24h"),
                                        target+pd.Timedelta("24h"))].copy()
        at=nearby.loc[nearby.time.eq(target)]
        if len(at)!=1: raise ValueError(f"Expected exact tower source row: {item['site']}/{stamp}")
        r=at.iloc[0]
        window=nearby.loc[~nearby.time.eq(target)]
        rv=window.RH.between(0.00001,100)
        vp=window.RH_from_tower_VPD.between(0.00001,100.05)
        results.append(dict(site=item["site"],time=str(target),
            source_TA_C=float(r.TA_F) if pd.notna(r.TA_F) else None,
            source_VPD_hPa=float(r.VPD_F) if pd.notna(r.VPD_F) else None,
            source_VPD_QC=float(r.VPD_F_QC) if pd.notna(r.VPD_F_QC) else None,
            raw_RH_present=bool(pd.notna(r.RH) and 0<r.RH<=100),
            original_RH_pct=float(r.RH) if pd.notna(r.RH) else None,
            original_RH_QC=float(r.RH_QC) if pd.notna(r.RH_QC) else None,
            original_VPD_implied_RH_pct=(
                float(r.RH_from_tower_VPD) if pd.notna(r.RH_from_tower_VPD) else None),
            neighbors_24h_rows=len(window),
            neighbors_24h_valid_raw_RH=int(rv.sum()),
            neighbors_24h_raw_RH_median_pct=(
                float(window.loc[rv,"RH"].median()) if rv.any() else None),
            neighbors_24h_valid_physical_VPD_RH=int(vp.sum()),
            neighbors_24h_physical_VPD_RH_median_pct=(
                float(window.loc[vp,"RH_from_tower_VPD"].median()) if vp.any() else None),
            caution="Neighboring VPD-derived RH can come from processed/gapfilled estimates"))
    return pd.DataFrame(results),source

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage13e-root",type=Path,default=REPORT13E)
    p.add_argument("--stage11-root",type=Path,default=STAGE11)
    p.add_argument("--write-report",action="store_true")
    p.add_argument("--output-root",type=Path)
    args=p.parse_args()
    r13=args.stage13e_root.expanduser().resolve()
    r11=args.stage11_root.expanduser().resolve()
    if not (r13/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file() or \
       not (r11/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Expected Stage11 and 13e review-only reports")
    m11=json.loads((r11/"manifest.json").read_text())
    if m11["n_target_rows"]!=4884 or m11["scientific_status"]!="HOLD_INDEPENDENT_VALIDATION_REQUIRED":
        raise ValueError("Stage11 science status differs")
    source8=Path(m11["source_stage08"])
    manifest=json.loads((source8/"exact_input_manifest.json").read_text())
    info={r["site"]:r for r in manifest["sites"]}
    if not set(SITES).issubset(info):raise ValueError("Site mismatch")
    nominal_path=r13/"nominal_offset_pilot_comparison.csv"
    alt_path=r13/"alternative_offsets_sensitivity.csv"
    holds_path=r13/"14_original_holds_ERA_dewpoint.csv"
    n=pd.read_csv(nominal_path)
    a=pd.read_csv(alt_path)
    h=pd.read_csv(holds_path)
    if len(h)!=14 or len(set(zip(h.site,h.time)))!=14:
        raise ValueError("Original fourteen HOLD record identities changed")
    if any(int((h.site==site).sum())!=count for site,count in HOLD_COUNTS.items()):
        raise ValueError("HOLD site counts differ")
    if not h.RH_preserving_numeric_valid.astype(str).str.lower().eq("true").all():
        raise ValueError("HOLD candidate failed numeric screen")
    for site in SITES:
        source=Path(info[site]["primary"]).resolve()
        if sha(source)!=m11["input_hashes"].get(str(source)):
            raise ValueError("Pinned site primary source changed: "+site)
    if a.duplicated(["site","time","event","site_utc_offset_hypothesis"]).any():
        raise ValueError("Duplicate alternative offset audit record")
    receipt={str(p):sha(p) for p in (
        nominal_path,alt_path,holds_path,r13/"manifest.json",r11/"manifest.json")}
    evid=[site_bif(info[site]) for site in SITES]
    scan=[]
    for site in SITES:
        rows=h.loc[h.site.eq(site),"time"].tolist()
        if not rows:continue
        one,raw=source_nearby(info[site],rows)
        scan.append(one)
        receipt[str(raw)]=sha(raw)
    neighbors=pd.concat(scan,ignore_index=True)
    compare=h.merge(neighbors,on=["site","time"],validate="one_to_one")
    compare["ERA_RH_minus_neighbor_RH"]=(
        compare.era_RH_pct-compare.neighbors_24h_raw_RH_median_pct)
    compare["extra_dry_ERA_RH_below_15pct"]=compare.era_RH_pct.lt(15)
    a_h=a.merge(h[["site","time","event"]],on=["site","time","event"],
                validate="many_to_one",how="inner")
    time_summary=[]
    for (site,stamp,event),group in a_h.groupby(["site","time","event"]):
        nominal=h[(h.site==site)&(h.time==stamp)&(h.event==event)]
        values=pd.concat([group,nominal],ignore_index=True)
        rh=pd.to_numeric(values.era_RH_pct,errors="coerce")
        vpd=pd.to_numeric(values.RH_preserving_VPD_hPa,errors="coerce")
        time_summary.append(dict(site=site,time=stamp,event=event,
             n_offset_hypotheses=len(values),
             ERA_RH_min_pct=float(rh.min()),ERA_RH_max_pct=float(rh.max()),
             RH_preserving_VPD_min_hPa=float(vpd.min()),
             RH_preserving_VPD_max_hPa=float(vpd.max()),
             timezone_certified=False))
    print("========== STAGE13F SOURCE/DRYNESS CHECK ==========")
    print("14/14 original holds covered")
    print("VERY DRY ERA RH (<15%) among 14 holds:",
          int(compare.extra_dry_ERA_RH_below_15pct.sum()))
    print("Original tower valid RH at HOLD time:",
          int(compare.raw_RH_present.sum()))
    print("\nTIMEZONE METADATA INVENTORY")
    for item in evid:
        print(item["site"],item["time_zone_evidence_status"],
              json.dumps(item["relevant_fields"],ensure_ascii=True))
    cols=["site","time","era_RH_pct","RH_preserving_VPD_hPa",
          "original_VPD_implied_RH_pct","neighbors_24h_valid_raw_RH",
          "neighbors_24h_raw_RH_median_pct",
          "neighbors_24h_valid_physical_VPD_RH",
          "neighbors_24h_physical_VPD_RH_median_pct"]
    print("\n14 ORIGINAL HOLDS / 24H SOURCE EVIDENCE")
    print(compare[cols].to_string(index=False))
    print("\nUTC OFFSET SENSITIVITY FOR 14 HOLDS")
    print(pd.DataFrame(time_summary).to_string(index=False))
    if any(item["relevant_fields"] for item in evid):
        print("Some BIF time-zone metadata discovered; values REQUIRE manual interpretation.")
    else:
        print("No UTC offset established from these BIFs: retrieve site BADM UTC_OFFSET.")
    print("HUMIDITY REMAINS UNAPPROVED: physical feasibility is not tower validation.")
    if not args.write_report:
        print("CHECK ONLY, no files written")
        return 0
    target=args.output_root.expanduser().resolve() if args.output_root else (
        HOME/("AmeriFlux_Batch02_stage13f_provenance_"+
              datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
              "_"+uuid4().hex[:8]))
    if target.exists() or any(target==q or target in q.parents or q in target.parents
                              for q in (r11,r13,BASE)):
        raise ValueError("Refusing existing/unsafe output")
    target.mkdir(parents=True,exist_ok=False)
    compare.to_csv(target/"14_hold_source_neighborhood.csv",index=False)
    pd.DataFrame(time_summary).to_csv(target/"14_hold_offset_sensitivity.csv",index=False)
    (target/"site_BIF_UTC_offset_evidence.json").write_text(
        json.dumps(evid,indent=2)+"\n",encoding="utf-8")
    (target/"DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "Humidity/timezone not yet independently approved.\n")
    (target/"manifest.json").write_text(json.dumps(dict(
        sources_sha256=receipt,
        script_sha256=sha(Path(__file__)),
        science_status="SOURCE_AND_TIMEZONE_DIAGNOSTICS_ONLY",
        next_gate="Verify BADM UTC_OFFSET and external/collocated moisture observations",
        all_model_sources_preserved=True),indent=2)+"\n")
    print("STAGE13F REPORT:",target)
    return 0

if __name__=="__main__":
    raise SystemExit(main())

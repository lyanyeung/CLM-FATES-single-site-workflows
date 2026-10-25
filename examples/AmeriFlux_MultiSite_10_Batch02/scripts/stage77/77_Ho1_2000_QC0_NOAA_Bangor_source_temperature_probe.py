#!/usr/bin/env python3
"""Stage77: independent NOAA GHCNh Bangor QC-screened evidence for Ho1 2000.

Addresses the 505 Ho1 year-2000 original TA_F_QC=0 events with source-T
minus independent CDS ERA5 temperature >8C, none with original matched
QC0 observations from US-Ho2 or US-Ho3 (Stage76 verified).

Only original source-observed NOAA Bangor temperatures with Stage40's
original station-origin-specific provenance/QC rules may be compared.
NOAA Bangor is an airport about 46km from Ho1, NOT Howland forest
canopy temperature ground truth. The Ho1 2026 BIF nominal UTC-5 is
provisional for historical clock validation; exact ±30min NOAA matches
may reuse the same station observation: count distinct source reports.

--self-test: no source files/network.
--check: validate Stage76 original source-report SHA and exact 505 cases,
         original stage40 parser Git blob; NO NETWORK, NO WRITES.
--audit: get *2000 ONLY* NOAA GHCNh PSV from NOAA HTTPS in memory with
         restricted final host and bounded bytes; report original source
         SHA, NOAA raw QC and provenance distributions; pair up to 505
         native clock UTC shadow instants, and write a NEW isolated source
         archive, exact source match and statistics with manifest SHA.
         Source bytes archived unchanged in new report for repeatability.

There is no pre-existing approved NOAA-2000 checksum; this FIRST download
is a new source acquisition, NOT a prior-pinned historical validation.
No original FLUXNET/ERA5/forcing edits, no T replacement, no BIF clock or
historical period approval, no other-file or Slurm changes.
"""
import argparse,hashlib,json,urllib.request,urllib.error,urllib.parse
from collections import Counter
from datetime import datetime,timezone
from importlib import util
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch02"
PRIOR=BASE/"scripts/stage40/40_compare_NOAA_Bangor_QC_with_Ho1_CDS.py"
PRIOR_BLOB="8767dbcad2c3c6cd431b37968e867838eac01d87"
REPORT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports")
STAGE76=REPORT/"stage76_1675_Ho1_BZS_original_cross_tower_QC0_context_20261025T092852Z_ceabe542"
SRC="1675_original_Ho1_BZS_temperature_cross_tower_HOLD.csv"
YEAR=2000
COUNT=505
STATION="USW00014606"
URL=("https://www.ncei.noaa.gov/oa/global-historical-climatology-network/"
     "hourly/access/by-year/2000/psv/GHCNh_USW00014606_2000.psv")
LIMIT=32*1024*1024

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def git_blob(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Pinned Stage40 original QC parser absent/symlinked")
    data=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def prior_parser():
    if git_blob(PRIOR)!=PRIOR_BLOB:
        raise ValueError("Stage40 original NOAA source QC and time parser Git blob changed")
    spec=util.spec_from_file_location("batch02_stage40_original_QC_pinned",PRIOR)
    mod=util.module_from_spec(spec);spec.loader.exec_module(mod)
    if (mod.STATION!=STATION or
        mod.ALLOWED!={("223","1"):"ICAO-KBGR",("335","5"):"726088-14606"}):
        raise ValueError("Original Stage40 station/source QC screening rules changed")
    return mod

def original():
    m=json.loads((STAGE76/"stage76_source_science_manifest.json").read_text())
    if ((STAGE76/"INCOMPLETE_DO_NOT_USE").exists() or
        m.get("schema")!="STAGE76_HO1_HO2_HO3_ORIGINAL_QC0_CROSS_TOWER_T_HOLDS_v1" or
        m.get("original_temperature_holds")!=1675 or
        m.get("original_Ho1_temperature_holds")!=1619 or
        m.get("original_Ho1_2000_QC0_ERA5_T_diff_gt8C")!=505 or
        m.get("original_numeric_water_humidity_shadow_unchanged")!=15199 or
        m.get("exact_native_tower_timestamps_not_historical_time_verified") is not True or
        m.get("BIF_historical_UTC_offset_approved") is not False or
        m.get("approved_for_DATM") is not False):
        raise ValueError("Stage76 original source or science-status changed")
    for file,digest in m["outputs_SHA256"].items():
        if sha(STAGE76/file)!=digest:raise ValueError("Stage76 output checksum changed: "+file)
    d=pd.read_csv(STAGE76/SRC,dtype={
      "site":str,"tower_local_start":str,"shadow_UTC_START":str,
      "source_csv_row":str,"source_sha256":str},low_memory=False)
    subset=d.loc[(d["site"]=="US-Ho1") &
        d["tower_local_start"].str.startswith("2000") &
        d["science_status"].eq("HOLD_TOWER_T_VS_INDEPENDENT_ERA5_GT8C")].copy()
    if (len(subset)!=COUNT or
        subset["TA_original_QC"].astype(float).ne(0).any() or
        subset["source_temperature_cross_tower_classification"].ne(
           "HO1_HOLD_NO_NATIVE_NEIGHBOR_QC0_EXACT_TIME").any() or
        subset["source_csv_row"].duplicated().any() or
        subset["shadow_UTC_START"].duplicated().any()):
        raise ValueError("Original Ho1 2000 505 QC0 source cases changed")
    subset["utc_time"]=pd.to_datetime(subset["shadow_UTC_START"],
                                     format="%Y%m%d%H%M",errors="raise")
    subset["local_time"]=pd.to_datetime(subset["tower_local_start"],
                                       format="%Y%m%d%H%M",errors="raise")
    if not (subset["utc_time"]-subset["local_time"]).eq(
            pd.Timedelta(hours=5)).all():
        raise ValueError("Ho1 original BIF nominal UTC−5 shadow unexpectedly modified")
    for col in ("TA_C","CDS_ERA5_T2M_C"):
        subset[col]=pd.to_numeric(subset[col],errors="raise")
    if (not np.isfinite(subset["TA_C"]).all() or
        not np.isfinite(subset["CDS_ERA5_T2M_C"]).all() or
        (subset["TA_C"]-subset["CDS_ERA5_T2M_C"]).abs().le(8).any()):
        raise ValueError("Original measured cold source cohort is not >8C mismatch")
    return subset,m

def retrieve():
    request=urllib.request.Request(URL,headers={
       "User-Agent":"Batch02-Stage77 independent NOAA scientific read-only provenance",
       "Accept":"text/plain,text/csv,*/*"})
    try:
        with urllib.request.urlopen(request,timeout=50) as response:
            loc=urllib.parse.urlsplit(response.geturl())
            if loc.scheme!="https" or loc.hostname not in (
                 "www.ncei.noaa.gov","ncei.noaa.gov"):
                raise ValueError("NOAA redirected to unexpected non-HTTPS authority")
            data=response.read(LIMIT+1)
    except (urllib.error.URLError,urllib.error.HTTPError) as exc:
        raise RuntimeError("NOAA GHCNh 2000 original source unavailable: "+str(exc)) from exc
    if len(data)==0 or len(data)>LIMIT:
        raise ValueError("Invalid empty/oversized NOAA 2000 source")
    return data

def compare(frame,mod,blob):
    recs,flags,invalid,nrows=mod.parse_psv(blob,YEAR)
    noaa_utc=pd.to_datetime([r[0] for r in recs])
    if not len(recs) or not noaa_utc.is_monotonic_increasing:
        raise ValueError("NOAA station 2000 original timestamps absent/not monotonic")
    pair=[]
    for row in frame.to_dict("records"):
        target=row["utc_time"].to_pydatetime()
        status,obs=mod.select(recs,target)
        z=dict(row)
        z["NOAA_Bangor_source_QC_pair_status"]=status
        z["NOAA_Bangor_T_C"]=np.nan
        z["NOAA_Bangor_UTC_REPORT"]=""
        z["NOAA_Bangor_utc_time_abs_diff_minutes"]=np.nan
        z["NOAA_minus_Ho1_T_C"]=np.nan
        z["NOAA_minus_CDS_ERA5_T_C"]=np.nan
        z["NOAA_independent_ground_observation_supported"]=False
        z["temperature_source_selection_approved"]=False
        z["BIF_historical_offset_approved"]=False
        z["approved_for_DATM"]=False
        if obs is not None:
            z["NOAA_Bangor_T_C"]=float(obs[1])
            z["NOAA_Bangor_UTC_REPORT"]=obs[0].isoformat()
            z["NOAA_Bangor_utc_time_abs_diff_minutes"]=abs(
                 (obs[0]-target).total_seconds()/60)
            z["NOAA_minus_Ho1_T_C"]=float(obs[1]-row["TA_C"])
            z["NOAA_minus_CDS_ERA5_T_C"]=float(
                  obs[1]-row["CDS_ERA5_T2M_C"])
            z["NOAA_independent_ground_observation_supported"]=True
            z["NOAA_original_source_code"]=obs[2]
            z["NOAA_original_quality_code"]=obs[3]
            z["NOAA_original_station_code"]=obs[4]
        pair.append(z)
    result=pd.DataFrame(pair)
    paired=result.loc[result["NOAA_independent_ground_observation_supported"]].copy()
    distinct=(paired[["NOAA_Bangor_UTC_REPORT","NOAA_original_source_code",
                     "NOAA_original_station_code"]].drop_duplicates()
                     if len(paired) else pd.DataFrame())
    # One physical station report may be matched against multiple HH records:
    # do not claim all paired half-hours are independent observations.
    counts=result["NOAA_Bangor_source_QC_pair_status"].value_counts().to_dict()
    print("STAGE77 NOAA YEAR",YEAR,"SOURCE ROWS",nrows,
          "PLAUSIBLE",len(recs),"SOURCE QC PASS",sum(r[6] for r in recs),
          "NOAA_RAW_BYTES",len(blob),"SHA256",hashlib.sha256(blob).hexdigest())
    print("STAGE77 NOAA SOURCE CODE/DATA LABELS",flags.most_common(12))
    print("STAGE77 NOAA REJECTED SOURCE LABELS",dict(invalid))
    print("STAGE77 ORIGINAL Ho1 2000 TARGETS",len(result),
          "SOURCE QC PAIRED HALFHOURS",len(paired),
          "UNIQUE NOAA SOURCE REPORTS",len(distinct))
    print("STAGE77 NOAA MATCH STATUS",counts)
    metrics={}
    if len(paired):
        a=paired["NOAA_minus_Ho1_T_C"].abs()
        b=paired["NOAA_minus_CDS_ERA5_T_C"].abs()
        # Per-HH descriptive evidence only; serial dependence is present.
        metrics={"matched_halfhour_count":len(paired),
             "distinct_NOAA_report_count":len(distinct),
             "noaa_vs_Ho1_mae_C":round(float(a.mean()),3),
             "noaa_vs_CDS_mae_C":round(float(b.mean()),3),
             "noaa_closer_to_CDS_by_more_than1C":int((b+1<a).sum()),
             "noaa_closer_to_Ho1_by_more_than1C":int((a+1<b).sum()),
             "difference_within1C":int((a-b).abs().le(1).sum()),
             "max_halfhour_reuse_per_NOAA_report":int(
               paired.groupby("NOAA_Bangor_UTC_REPORT").size().max())}
    print("STAGE77 NOAA AIRPORT VS FOREST T TRIANGULATION",metrics)
    print("STAGE77 INTERPRETATION: NOAA airport ~46km, not Ho1 forest canopy ground truth")
    print("STAGE77 NOMINAL BIF UTC−5, FULL HISTORICAL EFFECTIVE PERIOD NOT CERTIFIED")
    return result,metrics,counts,flags,invalid,nrows

def self_test():
    mod=prior_parser()
    mod.selftest()
    assert YEAR==2000 and COUNT==505
    assert STATION=="USW00014606"
    assert URL.startswith("https://www.ncei.noaa.gov/")
    print("STAGE77 SELF-TEST PASS | original NOAA source QC whitelist, 505 Ho1 2000, UTC shadow")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--check",action="store_true")
    g.add_argument("--audit",action="store_true")
    a=p.parse_args()
    if a.self_test:return self_test()
    mod=prior_parser()
    cases,m=original()
    if a.check:
        print("STAGE77 CHECK PASS | pinned original 505 Ho1 measured temperature events, NO NETWORK/WRITES")
        return
    raw=retrieve()
    matched,metrics,counts,flags,invalid,nrows=compare(cases,mod,raw)
    dest=REPORT/("stage77_Ho1_2000_505_QC0_NOAA_Bangor_external_T_context_"+
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
            "_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    marker=dest/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("NOAA source/T comparison diagnostic only; no model approval.\n")
    source=dest/"GHCNh_USW00014606_2000_original_source.psv"
    with source.open("xb") as f:
        f.write(raw)
    out=dest/"505_Ho1_2000_QC0_temp_vs_NOAA_original_source.csv"
    matched.to_csv(out,index=False)
    summary={
      "schema":"STAGE77_HO1_2000_QC0_NOAA_EXTERNAL_STATION_T_COMPARISON_v1",
      "n_original_Ho1_2000_QC0_native_gt8C":505,
      "n_source_QC_paired_halfhours":int(matched[
          "NOAA_independent_ground_observation_supported"].sum()),
      "n_original_BZS_temperature_holds_unchanged":56,
      "NOAA_station_id":STATION,"NOAA_original_source_url":URL,
      "NOAA_GHCNh_original_rows":nrows,
      "NOAA_raw_sha256":sha(source),
      "NOAA_QC_selection":str(mod.ALLOWED),
      "source_match_status":counts,
      "metrics_descriptive_not_model_permissions":metrics,
      "historical_site_UTC_offset_effective_dates_verified":False,
      "NOAA_airport_not_forest_canopy_ground_truth":True,
      "automatic_tower_temperature_replacement_approved":False,
      "approved_for_DATM":False,
      "source_SHA256":{"stage76_source_manifest":sha(
           STAGE76/"stage76_source_science_manifest.json"),
           "stage76_original_1675":sha(STAGE76/SRC),
           "prior_stage40_parser_gitblob":PRIOR_BLOB},
      "output_SHA256":{
          source.name:sha(source),
          out.name:sha(out)},
      "no_existing_source_or_model_writes":True}
    (dest/"stage77_source_science_manifest.json").write_text(
          json.dumps(summary,indent=2,sort_keys=True)+"\n")
    marker.unlink()
    print("STAGE77 AUDIT PASS | immutable NOAA 2000 raw and exact 505 Ho1 QC0 T source context; no forcing approval")
    print("REPORT",dest)
    print("NO ORIGINAL FLUXNET, CDS, STAGE49-76, NETCDF FORCING, DATM, CIME OR SLURM CHANGES")

if __name__=="__main__":
    main()

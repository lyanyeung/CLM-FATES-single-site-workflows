#!/usr/bin/env python3
"""Batch02 Stage40: Bangor GHCNh source-QC-screened T vs Ho1/CDS, READ ONLY.

Reuses Stage39 v3 pinned Stage08/19/20/21 source preflight, 319-event exact
identity and candidate nominal UTC-5. Requires NOAA PSV bytes identical to
the successful Stage39 v3 SHA256 readings. Source-specific *provisional*
legacy QC pairs: (223,1) and (335,5), plus source-station ID checks.
No interpolation, no approved replacements, no source/forcing/NetCDF writes,
no CIME/DATM/Slurm changes. Airport != canopy; UTC offset remains provisional.
"""
import argparse
from bisect import bisect_left
from collections import Counter
import csv
from datetime import datetime,timedelta,timezone
import hashlib
import importlib.util
import io
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request
sys.dont_write_bytecode=True
import numpy as np
import pandas as pd

STATION="USW00014606"
ALLOWED={("223","1"):"ICAO-KBGR",("335","5"):"726088-14606"}
SOURCE_SHA={
 1998:"5d57abd919b39781aca114180b87c51a6b5e80d23cfbc8b5f632ad55b650272d",
 1999:"6feeb4cf0cd93cf0ac6b9dc6e7cb2a3a452aa9cd4c7a42fb4212ec4c31869ae1",
 2001:"f4c24d57d257eccfc0d82c2c15bcd9b85ab2c65235068fc9f39ff34ae58939fe",
}
MAX_BYTES=32*1024*1024

def prior_stage():
    p=Path(__file__).resolve().with_name("39_probe_NOAA_GHCNh_Bangor_history.py")
    if not p.is_file():raise FileNotFoundError("Download pinned Stage39 v3 next to Stage40: "+str(p))
    spec=importlib.util.spec_from_file_location("pinned_stage39",p)
    if spec is None or spec.loader is None:raise ValueError("Stage39 source import failed")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if mod.STATION!=STATION or mod.YEARS!={1998:64,1999:25,2001:230}:
        raise ValueError("Stage39 scope has changed")
    return mod

def parse_time(text):
    try:d=datetime.fromisoformat(str(text).strip().replace("Z","+00:00"))
    except ValueError:return None
    return d.astimezone(timezone.utc).replace(tzinfo=None) if d.tzinfo else d

def parse_psv(blob,year):
    text=blob.decode("utf-8-sig",errors="strict")
    if "|" not in text[:1024] or "<html" in text[:1024].lower():
        raise ValueError("NOAA content not pipe-separated PSV")
    csvrows=csv.DictReader(io.StringIO(text),delimiter="|")
    fields={name.strip().lower():name for name in csvrows.fieldnames or []}
    needed={"station","date","temperature","temperature_quality_code",
            "temperature_source_code","temperature_source_station_id",
            "temperature_measurement_code"}
    if not needed<=set(fields):raise ValueError("GHCNh required fields missing: "+str(needed-set(fields)))
    records=[]; flags=Counter();invalid=Counter();total=0
    for row in csvrows:
        total+=1
        if (row.get(fields["station"]) or "").strip()!=STATION:
            raise ValueError("GHCNh station ID mismatch")
        stamp=parse_time(row.get(fields["date"]))
        if stamp is None or stamp.year!=year:
            invalid["invalid_or_other_year_time"]+=1;continue
        try:temp=float((row.get(fields["temperature"]) or "").strip())
        except ValueError:
            invalid["nonnumeric_temp"]+=1;continue
        if not np.isfinite(temp) or not -80<=temp<=60:
            invalid["physically_implausible"]+=1;continue
        qc=(row.get(fields["temperature_quality_code"]) or "").strip()
        src=(row.get(fields["temperature_source_code"]) or "").strip()
        origin=(row.get(fields["temperature_source_station_id"]) or "").strip()
        meas=(row.get(fields["temperature_measurement_code"]) or "").strip()
        flags[(src,qc,origin,meas)]+=1
        provisional=(ALLOWED.get((src,qc))==origin and meas=="")
        records.append((stamp,temp,src,qc,origin,meas,provisional))
    records.sort(key=lambda r:r[0])
    if not records:raise ValueError("NOAA year has no numeric station T")
    return records,flags,invalid,total

def select(rows,target):
    times=[x[0] for x in rows]
    start=bisect_left(times,target-timedelta(minutes=30))
    candidates=[]
    for r in rows[start:]:
        delta=(r[0]-target).total_seconds()/60
        if delta>30:break
        if abs(delta)<=30:candidates.append((abs(delta),r))
    if not candidates:return "NO_NUMERIC_30MIN",None
    valid=[(dt,r) for dt,r in candidates if r[6]]
    if not valid:return "NO_SOURCE_QC_PASS_30MIN",None
    dist=min(dt for dt,_ in valid)
    tied=[r for dt,r in valid if abs(dt-dist)<1e-8]
    if max(r[1] for r in tied)-min(r[1] for r in tied)>.001:
        return "CONFLICTING_EQUIDISTANT_REPORTS",None
    return "PROVISIONAL_SOURCE_QC",tied[0]

def fetch_year(prior,year):
    url=prior.candidate_url(year)
    req=urllib.request.Request(url,headers={
        "User-Agent":"CLM-FATES Stage40 read-only scientific evidence",
        "Accept":"text/plain,text/csv,*/*"})
    try:
        with urllib.request.urlopen(req,timeout=35) as response:
            dest=urllib.parse.urlsplit(response.geturl())
            if dest.scheme!="https" or dest.hostname not in ("www.ncei.noaa.gov","ncei.noaa.gov"):
                raise ValueError("Unexpected NOAA HTTPS redirect")
            raw=response.read(MAX_BYTES+1)
    except (urllib.error.HTTPError,urllib.error.URLError) as error:
        raise RuntimeError("NOAA HTTPS failed: "+str(error)) from error
    if len(raw)>MAX_BYTES:raise ValueError("NOAA PSV exceeds 32 MiB memory cap")
    actual=hashlib.sha256(raw).hexdigest()
    if actual!=SOURCE_SHA[year]:
        raise ValueError("NOAA original PSV changed since Stage39 v3; year "+
                         str(year)+" actual="+actual+" expected="+SOURCE_SHA[year]+
                         " — stop for source version review")
    print("NOAA SOURCE VERIFIED",year,"bytes",len(raw),"SHA256",actual,flush=True)
    return parse_psv(raw,year)

def quant(a):
    x=pd.to_numeric(pd.Series(a),errors="coerce").dropna()
    return x.quantile([.05,.25,.50,.75,.95]).round(3).to_dict() if len(x) else {}

def selftest():
    header=("STATION|DATE|temperature|temperature_Measurement_Code|"
            "temperature_Quality_Code|temperature_Source_Code|temperature_Source_Station_ID\n")
    lines=("USW00014606|1999-02-13T04:45:00|8.0||1|223|ICAO-KBGR\n"
           "USW00014606|1999-02-13T05:45:00|8.5||5|335|726088-14606\n"
           "USW00014606|1999-02-13T06:45:00|9.0||2|335|726088-14606\n"
           "USW00014606|1999-02-13T07:45:00|9.2||5|335|BAD-ORIGIN\n")
    records,flags,invalid,n=parse_psv((header+lines).encode(),1999)
    assert n==4 and [r[6] for r in records]==[True,True,False,False]
    t=datetime(1999,2,13,4,30)
    assert select(records,t)[1][1]==8.0
    assert select(records,datetime(1999,2,13,5))[1][0]==records[0][0]
    assert select(records,datetime(1999,2,13,6,45))[0]=="NO_SOURCE_QC_PASS_30MIN"
    assert select(records,datetime(1999,2,13,7,45))[0]=="NO_SOURCE_QC_PASS_30MIN"
    conflict=("USW00014606|1999-02-13T04:00:00|8.0||1|223|ICAO-KBGR\n"
              "USW00014606|1999-02-13T05:00:00|9.0||1|223|ICAO-KBGR\n")
    other,_,_,_=parse_psv((header+conflict).encode(),1999)
    assert select(other,t)[0]=="CONFLICTING_EQUIDISTANT_REPORTS"
    print("STAGE40 SELF-TEST PASS | source-dependent QC, station provenance, time matching, duplicate use, tie rejection")

def report(prior,events):
    f=prior.S20/"all_4884_phase_transfer_QC_sensitivity.csv"
    pairs=pd.read_csv(f,usecols=["site","local","retained_TA_C","ERA5_T2M_C"],parse_dates=["local"])
    pairs=pairs.loc[pairs.site.eq("US-Ho1"),["local","retained_TA_C","ERA5_T2M_C"]]
    x=events.merge(pairs,on="local",how="left",validate="one_to_one",indicator=True)
    if len(x)!=319 or not x._merge.eq("both").all():raise ValueError("Original 319/source temperature join differs")
    if not np.isfinite(x.retained_TA_C).all() or not np.isfinite(x.ERA5_T2M_C).all():
        raise ValueError("Missing original paired model T")
    summary=[]
    for year,g in x.groupby("year",sort=True):
        rows,flags,invalid,total=fetch_year(prior,int(year))
        status=Counter();selected=[]
        print("\nYEAR",year,"PSV source rows",total,"numeric",len(rows),
              "source-QC screened",sum(t[6] for t in rows))
        print("RAW source/quality/origin/measurement distribution:",flags.most_common(12))
        print("UNUSABLE rows:",dict(invalid))
        for z in g.itertuples(index=False):
            requested=z.utc_candidate.to_pydatetime()
            label,r=select(rows,requested)
            status[label]+=1
            if r is not None:
                selected.append(dict(local=z.local,utc_NOAA=r[0],
                    delta_minutes=abs((r[0]-requested).total_seconds())/60,
                    NOAA_T_C=r[1],Ho1_QC2_T_C=z.retained_TA_C,
                    CDS_ERA5_T_C=z.ERA5_T2M_C,
                    source=r[2],qc=r[3],source_station=r[4]))
        print("SOURCE QC status over",len(g),"targets",dict(status))
        if not selected:
            summary.append(dict(year=int(year),targets=len(g),paired=0,unique_NOAA=0))
            continue
        frame=pd.DataFrame(selected)
        e_ho1=frame.NOAA_T_C-frame.Ho1_QC2_T_C
        e_cds=frame.NOAA_T_C-frame.CDS_ERA5_T_C
        uniq=frame[["utc_NOAA","source","source_station"]].drop_duplicates().shape[0]
        print("PAIRED SOURCE-QC OBSERVATIONS",len(frame),"UNIQUE NOAA REPORTS",uniq,
              "UNIQUE NOAA TIMES",frame.utc_NOAA.nunique(),
              "MAX SAME-TIME REUSE",int(frame.groupby("utc_NOAA").size().max()))
        print("Time offset min quantiles:",quant(frame.delta_minutes))
        print("NOAA minus Ho1 QC2 T quantiles:",quant(e_ho1))
        print("NOAA minus CDS ERA5 T quantiles:",quant(e_cds))
        print("MAE NOAA to Ho1",round(float(e_ho1.abs().mean()),3),
              "MAE NOAA to CDS",round(float(e_cds.abs().mean()),3))
        print("CDS closer by >1C",int((e_cds.abs()+1<e_ho1.abs()).sum()),
              "Ho1 closer by >1C",int((e_ho1.abs()+1<e_cds.abs()).sum()))
        print("Worst 6 Ho1 mismatches:")
        print(frame.assign(abs_Ho1=e_ho1.abs()).nlargest(6,"abs_Ho1")[
            ["local","utc_NOAA","delta_minutes","Ho1_QC2_T_C",
             "CDS_ERA5_T_C","NOAA_T_C","source","qc","source_station"]
            ].round(3).to_string(index=False))
        summary.append(dict(year=int(year),targets=len(g),paired=len(frame),
            unique_NOAA=uniq,mae_Ho1=round(float(e_ho1.abs().mean()),3),
            mae_CDS=round(float(e_cds.abs().mean()),3)))
    print("\nSTAGE40 SOURCE-QC-SCREENED COMPARISON | NO SCIENCE APPROVAL")
    print(pd.DataFrame(summary).to_string(index=False))
    print("Bangor airport ~46km from Howland forest, spatial representation uncertain.")
    print("Ho1 UTC−5 provisional; same NOAA hourly report can match multiple half-hour records.")
    print("All 319 Ho1 and all 4,884 Batch02 remain scientific HOLD.")
    print("NO FILES WRITTEN / NO FORCING, NETCDF, DATM, CIME OR SLURM CHANGES")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    flags=parser.add_mutually_exclusive_group(required=True)
    flags.add_argument("--self-test",action="store_true")
    flags.add_argument("--check",action="store_true")
    flags.add_argument("--audit",action="store_true",help="NOAA HTTPS in-memory only")
    args=parser.parse_args()
    if args.self_test:
        selftest()
        return
    m=prior_stage()
    opts=argparse.Namespace(s11=m.S11,s19=m.S19,s20=m.S20,s21=m.S21)
    unknown=m.gate(opts)
    if args.check:
        for y,g in unknown.groupby("year"):
            print("READY",y,"319-cohort rows",len(g),"pinned source SHA",SOURCE_SHA[int(y)])
        print("STAGE40 CHECK PASS | OFFLINE, NO WRITES OR APPROVAL")
        return
    report(m,unknown)

if __name__=="__main__":
    main()

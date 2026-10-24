#!/usr/bin/env python3
"""Stage41: NOAA report deduplication, 16-event robustness, Ho1 QC0 calibration.

READ ONLY. Original Stage08/19/20/21 Ho1 data and exact 319 target
timestamps are verified by SHA-pinned Stage39 and Stage40 modules. Only
source/QC-screened Bangor GHCNh observations are considered. The same NOAA
hourly report can match 2+ Ho1 half-hours and MUST NOT be counted as
independent measurements. Include 1999 Ho1 measured-coded QC0 observations
OUTSIDE the February abnormal period as a separate airport-to-tower control.

No files written, no new source, no interpolations, no modified forcing,
NetCDF, CIME, DATM or Slurm; 4,884 HOLD and zero science approvals.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import numpy as np
import pandas as pd

P39="849d22af0f32ac4e54f10b834cb77a710da1d98f"
P40="8767dbcad2c3c6cd431b37968e867838eac01d87"
N={1998:64,1999:25,2001:230}
EP={1998:4,1999:3,2001:9}
PAIRED={1998:64,1999:25,2001:227}
UNIQUE={1998:34,1999:18,2001:145}

def git_blob(path):
    data=Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def modules():
    folder=Path(__file__).resolve().parent
    mods=[]
    for stem,basename,expected in [
        ("stage39","39_probe_NOAA_GHCNh_Bangor_history.py",P39),
        ("stage40","40_compare_NOAA_Bangor_QC_with_Ho1_CDS.py",P40)]:
        path=folder/basename
        if not path.is_file():
            raise FileNotFoundError("Missing pinned prerequisite: "+str(path))
        actual=git_blob(path)
        if actual!=expected:
            raise ValueError(stem+" Git blob mismatch: "+actual+" vs "+expected)
        spec=importlib.util.spec_from_file_location("batch02_"+stem,path)
        if spec is None or spec.loader is None:raise ValueError("Unable to load "+stem)
        x=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(x)
        mods.append(x)
        print("PINNED PYTHON VERIFIED",stem,actual,flush=True)
    m,p=mods
    if m.YEARS!=N or m.STATION!="USW00014606" or p.STATION!=m.STATION:
        raise ValueError("Stage39/40 original study identity changed")
    return m,p

def episode_labels(frame):
    x=frame.sort_values("local").copy()
    x["year"]=x.local.dt.year
    x["episode"]=x.groupby("year").local.diff().ne(
        pd.Timedelta(minutes=30)).groupby(x.year).cumsum().astype(int)
    if x.groupby("year").size().to_dict()!=N:
        raise ValueError("Stage39 original 319 timestamp count differs")
    if x.groupby("year").episode.nunique().to_dict()!=EP:
        raise ValueError("Stage38 16 continuous episodes differ")
    return x

def ho1_original_qc0_1999(m):
    m11=json.loads((m.S11/"manifest.json").read_text())
    m08=json.loads((Path(m11["source_stage08"])/"exact_input_manifest.json").read_text())
    info=[r for r in m08["sites"] if r["site"]=="US-Ho1"]
    if len(info)!=1:raise ValueError("Original Ho1 site inventory missing")
    path=m.verify(info[0]["primary"],m08["input_sha256"],"US-Ho1 QC0 calibration")
    raw=pd.read_csv(path,usecols=["TIMESTAMP_START","TA_F","TA_F_QC"],
                    dtype={"TIMESTAMP_START":str})
    raw=raw.loc[raw.TIMESTAMP_START.str.startswith("1999")].copy()
    raw["local"]=pd.to_datetime(
        raw.TIMESTAMP_START.str.strip().str.replace(r"\.0$","",regex=True),
        format="%Y%m%d%H%M")
    raw["TA_F"]=pd.to_numeric(raw.TA_F,errors="coerce")
    raw["TA_F_QC"]=pd.to_numeric(raw.TA_F_QC,errors="coerce")
    q=raw.loc[raw.TA_F_QC.eq(0)&raw.TA_F.notna()&raw.TA_F.gt(-9990),
              ["local","TA_F"]].copy()
    if len(q)!=3005 or q.local.duplicated().any():
        raise ValueError("Stage34 Ho1 1999 original QC0 expected 3005")
    q["utc_candidate"]=q.local+pd.Timedelta(hours=5)
    return q

def unique_reports(frame):
    rows=[]
    for key,g in frame.groupby(["utc_noaa","source","station"],sort=True):
        if g.noaa_t.max()-g.noaa_t.min()>.001:
            raise ValueError("One NOAA source-report identity contains inconsistent temperatures")
        rows.append(dict(utc_noaa=key[0],source=key[1],station=key[2],
                         uses=len(g),abs_ho1=float((g.noaa_t-g.ho1_t).abs().mean()),
                         abs_cds=float((g.noaa_t-g.cds_t).abs().mean())))
    return pd.DataFrame(rows)

def pairs(p,source_rows,cohort):
    found=[];status=Counter()
    for z in cohort.itertuples(index=False):
        request=z.utc_candidate.to_pydatetime()
        label,r=p.select(source_rows,request)
        status[label]+=1
        if r is None:continue
        found.append(dict(
            local=z.local,year=int(z.year),episode=int(z.episode),
            utc_noaa=r[0],source=r[2],station=r[4],
            offset_minutes=abs((r[0]-request).total_seconds())/60,
            noaa_t=float(r[1]),ho1_t=float(z.retained_TA_C),
            cds_t=float(z.ERA5_T2M_C)))
    return pd.DataFrame(found),status

def quant(a):
    q=pd.to_numeric(pd.Series(a),errors="coerce").dropna()
    return q.quantile([.05,.25,.5,.75,.95]).round(3).to_dict() if len(q) else {}

def check_gate(m):
    opts=argparse.Namespace(s11=m.S11,s19=m.S19,s20=m.S20,s21=m.S21)
    target=m.gate(opts)
    e=episode_labels(target)
    control=ho1_original_qc0_1999(m)
    print("STAGE41 OFFLINE PREFLIGHT PASS: 319 targets, 16 episodes,",
          "Ho1 1999 measured-QC0",len(control))
    return e,control

def audit(m,p,target,control):
    stage20=pd.read_csv(m.S20/"all_4884_phase_transfer_QC_sensitivity.csv",
                        usecols=["site","local","retained_TA_C","ERA5_T2M_C"],
                        parse_dates=["local"])
    stage20=stage20.loc[stage20.site.eq("US-Ho1"),
                         ["local","retained_TA_C","ERA5_T2M_C"]]
    x=target.merge(stage20,on="local",how="left",validate="one_to_one",indicator=True)
    if len(x)!=319 or not x._merge.eq("both").all():
        raise ValueError("Stage20 original 319 pairing differs")
    if not np.isfinite(x[["retained_TA_C","ERA5_T2M_C"]].to_numpy(float)).all():
        raise ValueError("Stage20 paired T is not finite")
    summary=[];pooled=[]
    for year,g in x.groupby("year",sort=True):
        # fetch_year checks official NCEI host and stage39 byte-exact SHA256.
        met,flags,invalid,total=p.fetch_year(m,int(year))
        f,status=pairs(p,met,g)
        if len(f)!=PAIRED[int(year)]:
            raise ValueError("Stage40 paired count differs, year "+str(year))
        if int(year)==2001 and status["CONFLICTING_EQUIDISTANT_REPORTS"]!=3:
            raise ValueError("Stage40 2001 ambiguous record count changed")
        un=unique_reports(f)
        if len(un)!=UNIQUE[int(year)]:
            raise ValueError("Stage40 number of distinct NOAA reports differs")
        eho=(f.noaa_t-f.ho1_t).abs()
        ecd=(f.noaa_t-f.cds_t).abs()
        print("\n"+"="*105)
        print("YEAR",year,"Ho1 target halfhours",len(g),"QC-screened pairs",len(f),
              "DISTINCT NOAA REPORTS",len(un),"episodes",g.episode.nunique())
        print("Stage40 status",dict(status))
        print("Half-hour paired MAE Ho1",round(float(eho.mean()),3),
              "CDS",round(float(ecd.mean()),3))
        print("Equal-weight distinct NOAA reports MAE Ho1",
              round(float(un.abs_ho1.mean()),3),"CDS",
              round(float(un.abs_cds.mean()),3))
        print("Distinct reports: CDS closer by >1C",
              int((un.abs_cds+1<un.abs_ho1).sum()),
              "Ho1 closer by >1C",int((un.abs_ho1+1<un.abs_cds).sum()))
        print("NOAA report used more than once",int(un.uses.gt(1).sum()),
              "max uses",int(un.uses.max()))
        erows=[]
        for event,z in f.groupby("episode",sort=True):
            eh=(z.noaa_t-z.ho1_t).abs()
            ec=(z.noaa_t-z.cds_t).abs()
            erows.append(dict(event=int(event),first=z.local.min(),last=z.local.max(),
                              halfhours=len(z),unique_NOAA=len(unique_reports(z)),
                              MAE_Ho1=round(float(eh.mean()),3),
                              MAE_CDS=round(float(ec.mean()),3),
                              CDS_closer_1C=int((ec+1<eh).sum()),
                              Ho1_closer_1C=int((eh+1<ec).sum())))
        print("EVENT-LEVEL REPORT (correlated events are not independent replicates):")
        print(pd.DataFrame(erows).to_string(index=False))
        summary.append(dict(year=int(year),halfhours=len(f),unique_NOAA=len(un),
                            target_MAE_Ho1=round(float(eho.mean()),3),
                            target_MAE_CDS=round(float(ecd.mean()),3),
                            NOAA_report_MAE_Ho1=round(float(un.abs_ho1.mean()),3),
                            NOAA_report_MAE_CDS=round(float(un.abs_cds.mean()),3)))
        pooled.append(f)
        if int(year)==1999:
            ctrl=control.copy()
            ctrl["year"]=1999
            ctrl["episode"]=0
            ctrl["retained_TA_C"]=ctrl.TA_F
            ctrl["ERA5_T2M_C"]=np.nan
            cal,cal_status=pairs(p,met,ctrl)
            print("\n1999 Ho1 ORIGINAL QC0 vs Bangor source-QC calibration (OUTSIDE anomaly):")
            print("QC0 tower n",len(control),"QC-screened NOAA pairs",len(cal),
                  "source-unique NOAA",len(unique_reports(cal)) if len(cal) else 0)
            print("QC0 measurement MONTHS:",control.local.dt.month.value_counts().sort_index().to_dict())
            print("NOAA pairing status",dict(cal_status))
            if len(cal):
                diff=cal.noaa_t-cal.ho1_t
                print("Bangor minus Ho1 original measured-coded QC0 T (C):",quant(diff))
                print("MAE",round(float(diff.abs().mean()),3))
                for mo,zz in cal.groupby(cal.local.dt.month):
                    ee=zz.noaa_t-zz.ho1_t
                    print("control month",mo,"n",len(zz),
                          "bias",round(float(ee.mean()),3),
                          "MAE",round(float(ee.abs().mean()),3))
            print("CAUTION: QC0 calibration months are not February 1999 anomaly winter.")
    total=pd.concat(pooled,ignore_index=True)
    reports=unique_reports(total)
    print("\n"+"="*105)
    print("STAGE41 SUMMARY | SOURCE-QUALITY-SCREENED, NO SCIENCE APPROVAL")
    print(pd.DataFrame(summary).to_string(index=False))
    print("Total paired halfhours",len(total),"DISTINCT NOAA REPORTS",len(reports),
          "continuous episodes",sum(EP.values()))
    print("Overall equal-weight source-report MAE: Ho1",round(float(reports.abs_ho1.mean()),3),
          "CDS",round(float(reports.abs_cds.mean()),3))
    print("Annual/episode serial correlation remains; do not report naive p-values.")
    print("Ho1 UTC-5 is provisional; Bangor airport ~46km distant and not canopy ground truth.")
    print("4,884 Batch02 rows SCIENTIFIC HOLD; zero approved forcing repairs.")
    print("NO FILES WRITTEN / NO DATM, CIME, NETCDF, FORCING OR SLURM MODIFICATIONS")

def selftest():
    t=pd.DataFrame(dict(
        local=pd.to_datetime(["1998-11-21 00:00","1998-11-21 00:30",
                              "1998-11-21 03:00"])))
    event=t.local.diff().ne(pd.Timedelta(minutes=30)).cumsum()
    assert event.tolist()==[1,1,2]
    d=pd.DataFrame(dict(
        utc_noaa=pd.to_datetime(["1998-11-21 05:00"]*2+["1998-11-21 09:00"]),
        source=["223"]*3,station=["ICAO-KBGR"]*3,
        noaa_t=[8.0,8.0,9.0],ho1_t=[-11.0,-10.0,-9.0],
        cds_t=[8.1,8.2,9.2]))
    result=unique_reports(d)
    assert len(result)==2 and sorted(result.uses)==[1,2]
    assert abs(result.abs_ho1.mean()-18.25)<1e-9
    try:unique_reports(d.assign(noaa_t=[8.0,8.5,9.0]))
    except ValueError as e:
        assert "inconsistent" in str(e)
    else:raise AssertionError("Conflicting NOAA report timestamps incorrectly accepted")
    print("STAGE41 SELF-TEST PASS | contiguous events, report dedup, conflicting source fail-stop")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    modes=ap.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--audit",action="store_true",help="NOAA HTTPS reads into RAM only")
    opts=ap.parse_args()
    if opts.self_test:
        selftest()
        return
    m,p=modules()
    x,cal=check_gate(m)
    if opts.check:
        print("OFFLINE CHECK ONLY, no NOAA request, no data modifications")
        return
    audit(m,p,x,cal)

if __name__=="__main__":
    main()

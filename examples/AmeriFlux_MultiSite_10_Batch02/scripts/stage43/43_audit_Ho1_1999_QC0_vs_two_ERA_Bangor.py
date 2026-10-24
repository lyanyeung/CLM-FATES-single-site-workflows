#!/usr/bin/env python3
"""Stage43 | Ho1 autumn-1999 measured-QC0 versus ERA provenance triangulation.

Scope: original immutable Ho1 1999 QC0 October-December controls (n=3,005)
and the original February 1999 Ho1 QC2 anomaly events (n=25). Compare:
  (A) Ho1 original measured-coded TA_F (QC0) or original QC2 TA_F,
  (B) Ho1 original embedded TA_ERA,
  (C) nearby Ho2 original embedded TA_ERA, NEVER assumed measured,
  (D) Bangor NOAA GHCNh station temperature after Stage40 source/QC screen.

Investigate if long observed-QC0 Bangor-vs-Ho1 differences are mirrored by
either embedded FLUXNET ERA forcing product. Report months, unique NOAA
source reports and sustained episodes, never declare a temperature winner
or attribute cause without sensor/BADM metadata.

All input sources SHA256-verified via prior stages; Stage42 exact Git blob
pinned; Stage39/40/41 pins are checked transitively. For --audit ONLY,
1999 Bangor original PSV is HTTPS-read into RAM and byte-SHA256-verified.
No disk products, no downloads-to-disk, no forcing changes, no model jobs,
no NetCDF/DATM/CIME/Slurm actions, no scientific repair approvals.
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

ST42_FILE="42_audit_Ho1_1999_QC0_Bangor_temporal_bias.py"
ST42_BLOB="903c62949ea4f7c9b6ab8402a364a377e5b61c37"
YEAR=1999
CONTROL_EXPECTED=3005
CONTROL_MONTHS={10:77,11:1440,12:1488}
FEB_EXPECTED=25
NOAA_CONTROL_EXPECTED=2986
NOAA_CONTROL_UNIQUE=1498
NOAA_FEB_EXPECTED=25

def blob_id(path):
    raw=Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def stage42_module():
    path=Path(__file__).resolve().with_name(ST42_FILE)
    if not path.is_file():
        raise FileNotFoundError("Download pinned Stage42 and Stage39/40/41 beside Stage43")
    got=blob_id(path)
    if got!=ST42_BLOB:
        raise ValueError("Stage42 Git blob unexpected: "+got+" wanted "+ST42_BLOB)
    spec=importlib.util.spec_from_file_location("pinned_stage42",path)
    if spec is None or spec.loader is None:
        raise ValueError("Failed loading pinned Stage42 prerequisite")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    print("PREREQUISITE VERIFIED",ST42_FILE,got,flush=True)
    return mod

def load_one_year(m,site):
    m11=json.loads((m.S11/"manifest.json").read_text())
    m08=json.loads((Path(m11["source_stage08"])/"exact_input_manifest.json").read_text())
    items=[v for v in m08["sites"] if v["site"]==site]
    if len(items)!=1:raise ValueError("Missing unique original "+site+" in Stage08 manifest")
    raw=m.verify(items[0]["primary"],m08["input_sha256"],site+" original TA ERA")
    columns=["TIMESTAMP_START","TA_F","TA_F_QC","TA_ERA"]
    header=set(pd.read_csv(raw,nrows=0).columns)
    if not set(columns)<=header:
        raise ValueError(site+" original hourly product missing TA_ERA/T/QC")
    a=pd.read_csv(raw,usecols=columns,dtype={"TIMESTAMP_START":str})
    a=a.loc[a.TIMESTAMP_START.str.startswith("1999")].copy()
    a["local"]=pd.to_datetime(a.pop("TIMESTAMP_START").str.strip().str.replace(
        r"\.0$","",regex=True),format="%Y%m%d%H%M",errors="raise")
    if a.local.duplicated().any() or not a.local.is_monotonic_increasing:
        raise ValueError(site+" original 1999 timestamp sequence invalid")
    for name in ("TA_F","TA_ERA","TA_F_QC"):
        a[name]=pd.to_numeric(a[name],errors="coerce")
        a.loc[a[name]<=-9990,name]=np.nan
    if not a.TA_F_QC.dropna().isin([0,1,2]).all():
        raise ValueError(site+" original 1999 T quality codes not 0/1/2")
    print("ORIGINAL SHA256 VERIFIED",site,"1999 rows",len(a),
          "TA_F_QC0",int((a.TA_F_QC.eq(0)&a.TA_F.notna()).sum()),
          "TA_ERA numeric",int(a.TA_ERA.notna().sum()),flush=True)
    return a[["local","TA_F","TA_F_QC","TA_ERA"]]

def gate(t42):
    m,p,s41=t42.load_verified_stages()  # validates exact Stage39,40,41 source Git blobs
    # Recheck all source & timestamp SHA256, original 1999 QC0 count, 25 Feb held
    ctrl,feb=t42.measured_control(m,p,s41)
    if len(ctrl)!=CONTROL_EXPECTED or len(feb)!=FEB_EXPECTED:
        raise ValueError("Stage42 1999 controls or Feb anomalies changed")
    if ctrl.local.dt.month.value_counts().sort_index().to_dict()!=CONTROL_MONTHS:
        raise ValueError("1999 original QC0 seasonal coverage changed")
    ho1=load_one_year(m,"US-Ho1")
    ho2=load_one_year(m,"US-Ho2")
    def join(subset,label):
        v=subset.merge(ho1.rename(columns={"TA_F":"Ho1_source_T",
                                            "TA_F_QC":"Ho1_source_QC",
                                            "TA_ERA":"Ho1_ERA_T"}),
                       on="local",how="left",validate="one_to_one",indicator=True)
        if not v._merge.eq("both").all():
            raise ValueError(label+" original Ho1 source timestamps missing")
        v.drop(columns="_merge",inplace=True)
        if not np.allclose(v.TA_F,v.Ho1_source_T,rtol=0,atol=1e-6,equal_nan=True):
            raise ValueError(label+" original Ho1 raw TA_F mismatch")
        v=v.merge(ho2.rename(columns={"TA_F":"Ho2_T",
                                      "TA_F_QC":"Ho2_QC",
                                      "TA_ERA":"Ho2_ERA_T"}),
                  on="local",how="left",validate="one_to_one",indicator=True)
        if not v._merge.eq("both").all():
            raise ValueError(label+" original Ho2 source timestamps missing")
        v.drop(columns="_merge",inplace=True)
        if not np.isfinite(v[["TA_F","Ho1_ERA_T","Ho2_ERA_T"]].to_numpy(float)).all():
            raise ValueError(label+" non-finite original T or nearby ERA source")
        return v
    c=join(ctrl.copy(),"CONTROL")
    f=join(feb.copy(),"FEBRUARY")
    if not c.Ho1_source_QC.eq(0).all():
        raise ValueError("Stage41 original Ho1 autumn QC0 changed")
    if not f.Ho1_source_QC.eq(2).all():
        raise ValueError("Stage37 original Ho1 February QC2 changed")
    if not np.allclose(f.TA_F,f.Ho1_ERA_T,rtol=0,atol=.001):
        raise ValueError("Stage37 original February Ho1 QC2 no longer equals TA_ERA")
    print("STAGE43 SOURCE PREFLIGHT PASS: Ho1 1999 Oct-Dec QC0=3005;",
          "February QC2=25; Ho1/Ho2 ERA source present")
    return m,p,t42,c,f

def screen_noaa(t42,p,source,table):
    times=[x[0] for x in source]
    found=[];status=Counter()
    for row in table.itertuples(index=False):
        utc=row.local.to_pydatetime()+pd.Timedelta(hours=5).to_pytimedelta()
        label,x=t42.fast_select(source,times,utc)
        status[label]+=1
        if x is None:continue
        found.append(dict(local=row.local,utc_noaa=x[0],
                          noaa_temp=float(x[1]),noaa_src=x[2],noaa_qc=x[3],
                          noaa_source_station=x[4],
                          target_noaa_delta_minutes=abs((x[0]-utc).total_seconds())/60))
    o=pd.DataFrame(found)
    if o.empty:return o,status
    o=table.merge(o,on="local",how="inner",validate="one_to_one")
    return o,status

def stats(frame,lhs,rhs):
    d=frame[lhs]-frame[rhs]
    d=pd.to_numeric(d,errors="coerce").dropna()
    if not len(d):
        return {"n":0}
    return dict(n=len(d),bias=round(float(d.mean()),3),
                median=round(float(d.median()),3),
                MAE=round(float(d.abs().mean()),3),
                p95_abs=round(float(d.abs().quantile(.95)),3),
                n_abs_gt10C=int(d.abs().gt(10).sum()))

def show_metrics(frame,heading):
    print("\n"+heading)
    for lhs,rhs in [
        ("noaa_temp","TA_F"),
        ("Ho1_ERA_T","TA_F"),
        ("Ho2_ERA_T","TA_F"),
        ("noaa_temp","Ho1_ERA_T"),
        ("noaa_temp","Ho2_ERA_T"),
        ("Ho1_ERA_T","Ho2_ERA_T")
    ]:
        print(f"{lhs} minus {rhs}",stats(frame,lhs,rhs))
    if len(frame):
        uniq=frame[["utc_noaa","noaa_src","noaa_source_station"]].drop_duplicates()
        print("half-hour target pairs",len(frame),
              "DISTINCT NOAA reports",len(uniq),
              "max report target reuse",
              int(frame.groupby(["utc_noaa","noaa_src","noaa_source_station"]).size().max()))
        print("Ho2 original TA_F_QC distribution (NOT sensor validation):",
              frame.Ho2_QC.value_counts(dropna=False).to_dict())

def long_events(frame):
    matched=frame.sort_values("local").copy()
    matched["airport_minus_ho1"]=matched.noaa_temp-matched.TA_F
    problem=matched.loc[matched.airport_minus_ho1.abs().gt(10)].copy()
    if problem.empty:return pd.DataFrame()
    problem["run"]=problem.local.diff().ne(pd.Timedelta(minutes=30)).cumsum()
    problem["airport_minus_ho2era"]=problem.noaa_temp-problem.Ho2_ERA_T
    problem["ho1era_minus_ho1"]=problem.Ho1_ERA_T-problem.TA_F
    problem["ho2era_minus_ho1"]=problem.Ho2_ERA_T-problem.TA_F
    return problem.groupby("run").agg(
        first=("local","min"),last=("local","max"),halfhours=("local","size"),
        Bangor_minus_Ho1_median=("airport_minus_ho1","median"),
        Bangor_minus_Ho2ERA_median=("airport_minus_ho2era","median"),
        Ho1ERA_minus_Ho1_median=("ho1era_minus_ho1","median"),
        Ho2ERA_minus_Ho1_median=("ho2era_minus_ho1","median")
    ).sort_values("halfhours",ascending=False).head(15)

def run_audit(m,p,t42,control,feb):
    rows,flags,invalid,total=p.fetch_year(m,YEAR)
    obs,status=screen_noaa(t42,p,rows,control)
    febobs,febstatus=screen_noaa(t42,p,rows,feb)
    if len(obs)!=2986 or len(febobs)!=25:
        raise ValueError("Stage41/42 historical NOAA source-QC matching changed")
    u=obs[["utc_noaa","noaa_src","noaa_source_station"]].drop_duplicates()
    if len(u)!=NOAA_CONTROL_UNIQUE:
        raise ValueError("Stage41 original 1498 unique NOAA control reports changed")
    if abs(float((obs.noaa_temp-obs.TA_F).abs().mean())-5.024)>.006:
        raise ValueError("Stage41 original 5.024C observed-QC0 airport MAE changed")
    if abs(float((febobs.noaa_temp-febobs.TA_F).abs().mean())-13.008)>.006:
        raise ValueError("Stage40 original 13.008C February QC2 airport MAE changed")
    print("\n"+"="*110)
    print("STAGE43 | 1999 HO1 MEASURED QC0/FLUXNET ERA/HO2 ERA/BANGOR TRIANGULATION")
    print("Ho1 original QC0 controls 3005, NOAA-QC-screened 2986; 25 February QC2 anomaly")
    print("All sources unchanged: original source + pinned NOAA SHA256 verified")
    print("="*110)
    print("1999 QC0 NOAA pairing statuses",dict(status))
    print("1999 FEB QC2 NOAA pairing statuses",dict(febstatus))
    show_metrics(obs,"ORIGINAL Ho1 QC0 OCT–DEC CONTROLS — NO PRETENCE THAT HO2 ERA IS OBSERVED")
    for mo,g in obs.groupby(obs.local.dt.month):
        show_metrics(g,"MEASURED QC0 CONTROL MONTH "+str(mo))
    print("\n1999 measured-QC0 LONG ABS(BANGOR-HO1) >10C EPISODES:")
    event=long_events(obs)
    print(event.round(3).to_string() if len(event) else "NONE")
    show_metrics(febobs,"FEBRUARY 1999 Ho1 QC2 FAILURES — DO NOT INFER SOURCE CORRECTION")
    print("\nTOP 10 FEBRUARY ORIGINAL HO1 QC2 VS BANGOR CONTRADICTIONS:")
    z=febobs.copy()
    z["err"]=abs(z.noaa_temp-z.TA_F)
    print(z.nlargest(10,"err")[[
        "local","utc_noaa","TA_F","Ho1_ERA_T","Ho2_ERA_T",
        "noaa_temp","Ho2_QC","noaa_src","noaa_qc"
    ]].round(3).to_string(index=False))
    print("\nSCIENTIFIC LIMITATIONS:")
    print("Ho2 TA_ERA is another processed FLUXNET ERA forcing product, NOT measured QC0.")
    print("Bangor airport ~46km from Ho1 canopy; remote air temperature not site ground truth.")
    print("A shared ERA source may be correlated with CDS ERA5; numerical agreement")
    print("does NOT prove statistical independence or a physical correction.")
    print("1999 QC0 controls are in Oct-Dec; February lacks Ho1 measured temperatures.")
    print("Ho1 local-minus-UTC=-5 is provisional; BADM/BASE remains uncertified.")
    print("4,884 Stage08 source targets remain scientific HOLD; zero approved forcing changes.")
    print("NO OUTPUT FILE WRITES / NO NETCDF, FORCING, DATM, CIME OR SLURM CHANGES")

def selftest():
    a=pd.DataFrame({
        "local":pd.to_datetime(["1999-11-02 00:00","1999-11-02 00:30",
                                "1999-11-02 06:00"]),
        "TA_F":[-3.,-2.,3.],"Ho1_ERA_T":[-2.,-1.,2.],
        "Ho2_ERA_T":[6.,7.,4.],
        "Ho2_QC":[2,2,2],
        "noaa_temp":[7.,7.,5.],
        "utc_noaa":pd.to_datetime(["1999-11-02 05:53"]*2+["1999-11-02 11:53"]),
        "noaa_src":["223"]*3,"noaa_source_station":["ICAO-KBGR"]*3
    })
    assert stats(a,"noaa_temp","TA_F")["n_abs_gt10C"]==0
    assert stats(a,"Ho2_ERA_T","TA_F")["MAE"]==6.333
    e=long_events(a.assign(noaa_temp=[8.,9.,5.]))
    assert len(e)==1 and int(e.halfhours.iloc[0])==2
    assert a[["utc_noaa","noaa_src","noaa_source_station"]].drop_duplicates().shape[0]==2
    print("STAGE43 SELF-TEST PASS | source comparisons, provenance duplication,")
    print("long-event segmentation, and no output files")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--audit",action="store_true",help="NOAA 1999 PSV in RAM only")
    args=parser.parse_args()
    if args.self_test:
        selftest()
        return
    t42=stage42_module()
    m,p,_,control,feb=gate(t42)
    if args.check:
        print("STAGE43 CHECK PASS — source pinned, 1999 controls",len(control),
              "Feb failures",len(feb),"; offline, no data files written")
        return
    run_audit(m,p,t42,control,feb)

if __name__=="__main__":
    main()

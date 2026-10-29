#!/usr/bin/env python3
"""US-NC2: one-pass site+source scientific triage, only original reads and fresh reports.

Choose latest signed Stage11Q derived trial when present, otherwise signed
Stage11L. Do not pretend Stage11Q was run. Check original Stage07 FLUXMET
source SHA, source QC, physical water/ice VPD/QBOT and 2025-Mar 18/23/25
research-source discontinuities. NEVER alter any forcing, cases, DATM or Slurm.
"""
import hashlib,json,sys,argparse
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np,pandas as pd
sys.dont_write_bytecode=True
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=R/"qcv5_native_trial_20261022T024559Z_36c46e58"
L=R/"science_trials/stage11l_US-NC2_humidity_only_20261024T100319Z_31a4697e"
LFILE="US-NC2_humidity_only_new_shadow_NOLEAP.csv"
LREC="stage11l_scientific_hold_receipt.json"
QGLOB="stage11q_US-NC2_auto9_RH_only_*"
QFILE="US-NC2_humidity_only_auto9_shadow_NOLEAP.csv"
QREC="stage11q_sha_science_hold_receipt.json"
COLS=["time","TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE"]
BOUNDARIES=[
 ("MAR18_START","202503181800","202503181830"),
 ("MAR23_ORIGINAL","202503230830","202503230900"),
 ("MAR23_END","202503231500","202503231530"),
 ("MAR25_END","202503251000","202503251030")
]
GROUP_DAYS={"20250318","20250323","20250325"}
def guard(cond,msg):
    if not bool(cond):raise RuntimeError("US-NC2 ONEPASS STOP: "+str(msg))
def fil(p):
    p=Path(p);guard(p.is_file() and not p.is_symlink(),"source missing "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with fil(p).open("rb") as z:
        for b in iter(lambda:z.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def es(t):
    t=np.asarray(t,dtype=float)
    return 6.112*np.exp(17.67*t/(t+243.5))
def ei(t):
    t=np.asarray(t,dtype=float)
    return 6.112*np.exp(22.46*t/(t+272.62))
def good_receipt(folder,filename,receipt,expected):
    r=json.loads(fil(folder/receipt).read_text())
    guard(r.get("version")==expected,"source trial receipt version not pinned "+str(folder))
    guard(sha(folder/filename)==r["output_sha256"][filename],
          "source SHA changed "+str(folder/filename))
    guard(r.get("Postv5_approved")==0 and r.get("DATM_ready")==0 and
          r.get("spinup_authorized")==0,"research source unexpected production approval")
    return r
def choose_source():
    lr=good_receipt(L,LFILE,LREC,"stage11l-v1-20261024-11-humidity-only-successor")
    qdirs=sorted(d for d in (R/"science_trials").glob(QGLOB)
                 if d.is_dir() and not d.is_symlink())
    if not qdirs:
        print("US-NC2 SOURCE SELECTED: signed Stage11L (no actual Stage11Q directory found)",flush=True)
        return L/LFILE,"STAGE11L",lr
    # A reported actual Stage11Q must have complete receipts and pass ALL SHA checks.
    valid=[]
    for d in qdirs:
        receipt=d/QREC
        if not receipt.is_file() or receipt.is_symlink():
            print("US-NC2 WARNING: unsealed/incomplete Stage11Q dir, not selected:",d,flush=True)
            continue
        qr=good_receipt(d,QFILE,QREC,
             "stage11q-v1-20261024-automated-nine-source-humidity-shadow")
        guard(sha(L/LFILE)==qr["input_stage11l_forcing_SHA256"],
              "Stage11Q predecessor Stage11L input source SHA differs")
        for name,digest in qr["output_sha256"].items():
            guard(sha(d/name)==digest,"Stage11Q sealed output SHA mismatch "+name)
        valid.append((d,qr))
    if not valid:
        print("US-NC2 SOURCE SELECTED: Stage11L (Stage11Q report directory incomplete, not assumed)",flush=True)
        return L/LFILE,"STAGE11L",lr
    guard(len(valid)==1,"multiple signed Stage11Q versions: operator must identify active derivative")
    d,qr=valid[0]
    print("US-NC2 SOURCE SELECTED: actual sealed Stage11Q, 9-extra-RH candidate:",d,flush=True)
    return d/QFILE,"STAGE11Q",qr
def original_source():
    m=json.loads(fil(S07/"exact_input_manifest.json").read_text())
    sites=[z for z in m["sites"] if z["site"]=="US-NC2"]
    guard(len(sites)==1 and int(sites[0]["native_minutes"])==30
          and int(sites[0]["first_year"])==2005
          and int(sites[0]["last_year"])==2025,
          "US-NC2 signed original 2005-2025 HH site release changed")
    for item in ("primary","era"):
        p=fil(sites[0][item])
        guard(m["input_sha256"].get(str(p.resolve()))==sha(p),
              "source original "+item+" SHA differs")
    return sites[0]
def strict_clock(s):
    t=pd.to_datetime(s.time,errors="raise")
    exp=pd.date_range("2005-01-01","2025-12-31 23:30",freq="30min")
    exp=exp[~((exp.month==2)&(exp.day==29))]
    guard(len(s)==len(exp)==367920 and t.is_unique and
          np.array_equal(t.to_numpy(),exp.to_numpy()),
          "original 21 year 367920 native NOLEAP clock differs")
    return t,t.dt.strftime("%Y%m%d%H%M")
def selftest():
    guard(21*365*48==367920 and len(BOUNDARIES)==4 and
          es(-10)>ei(-10) and abs(float(es(10))-12.2717)<.02,
          "physical/clock self-test")
    guard(pd.Series(["abc",None]).equals(pd.Series(["abc",None])),
          "mixed string/NaN exact comparison")
    print("US-NC2 ONEPASS SELF-TEST PASS (source read-only)",flush=True)
def assess():
    source,stage,receipt=choose_source()
    orig=original_source()
    s=pd.read_csv(source,dtype={"time":str},low_memory=False)
    guard(list(s.columns)==COLS,"candidate 10-column schema")
    dt,key=strict_clock(s)
    a={c:pd.to_numeric(s[c],errors="raise").to_numpy(float) for c in COLS[1:]}
    t=a["TA_USE"];p=a["PSRF"];v=a["VPD_USE"];q=a["QBOT"]
    with np.errstate(invalid="ignore",divide="ignore",over="ignore"):
        ew=es(t);e=ew-v;qq=0.622*100*e/(p-0.378*100*e)
        rw=100*e/ew;ri=100*e/ei(t)
    complete=np.logical_and.reduce([np.isfinite(z) for z in a.values()])
    water=complete&(v>=0)&(e>=0)&(p>50000)&(p<110000)&
          np.isclose(q,qq,rtol=1e-7,atol=1e-9)
    tk=complete&(np.abs(a["TBOT"]-t-273.15)<1e-8)
    ice_warn=water&(t<0)&(ri>100)
    dry_warn=water&(rw<5)
    wind_bad=complete&(a["WIND"]<0)
    pr_bad=complete&(a["PRECTmms"]<0)
    sw_bad=complete&(a["FSDS"]< -1)
    lw_bad=complete&(a["FLDS"]<0)
    k=key.to_numpy()
    idmap={z:i for i,z in enumerate(k)}
    guard(len(idmap)==len(k),"native clock/source duplicate")
    old=pd.read_csv(L/LFILE,dtype={"time":str},low_memory=False)
    guard(len(old)==len(s) and old.time.equals(s.time),
          "latest selected science source cannot align to Stage11L")
    old_v=old.VPD_USE.to_numpy(float)
    original_selected=pd.read_csv(S07/"US-NC2/forcing/processed_v5/US-NC2_CLM_forcing_2005_2025.csv",
                                  dtype={"time":str},low_memory=False)
    guard(len(original_selected)==len(s) and original_selected.time.equals(s.time),
          "Stage07 original selected time differs from latest")
    need_raw=set()
    for name,aa,bb in BOUNDARIES:
        for z in (aa,bb):
            i=idmap[z]
            for j in range(max(0,i-4),min(len(s),i+5)):
                need_raw.add(k[j])
    for day in GROUP_DAYS:
        need_raw.update(z for z in k if z.startswith(day))
    frame=pd.read_csv(orig["primary"],usecols=["TIMESTAMP_START","TA_F","TA_F_QC",
       "VPD_F","VPD_F_QC"],dtype={"TIMESTAMP_START":str},low_memory=False)
    paired=pd.read_csv(orig["era"],usecols=["TIMESTAMP_START","TA_ERA","VPD_ERA"],
       dtype={"TIMESTAMP_START":str},low_memory=False)
    raw=frame.loc[frame.TIMESTAMP_START.isin(need_raw)].merge(
       paired.loc[paired.TIMESTAMP_START.isin(need_raw)],
       on="TIMESTAMP_START",how="left",validate="one_to_one")
    raw=raw.set_index("TIMESTAMP_START",drop=False)
    guard(set(need_raw)<=set(raw.index),"original source native context missing")
    events=[]
    for day in sorted(GROUP_DAYS):
        for z in k:
            if not z.startswith(day):continue
            i=idmap[z];r=raw.loc[z]
            tv=float(r.TA_F);ov=float(r.VPD_F)
            es_native=float(es(tv)) if np.isfinite(tv) else np.nan
            xera=float(r.TA_ERA);vera=float(r.VPD_ERA)
            era_rh=100*(1-vera/float(es(xera))) if np.isfinite([xera,vera]).all() else np.nan
            events.append(dict(native_key=z,native_time=s.time.iloc[i],
                original_TA_C=tv,original_T_QC=r.TA_F_QC,
                original_VPD_hPa=ov,original_VPD_QC=r.VPD_F_QC,
                original_implied_RHwater_pct=100*(1-ov/es_native) if es_native>0 else np.nan,
                companion_ERA_T_C=xera,companion_ERA_VPD_hPa=vera,
                companion_ERA_water_RH_pct=era_rh,
                selected_stage=stage,selected_VPD_hPa=v[i],
                prior_Stage11L_VPD_hPa=old_v[i],
                selected_QBOT=q[i],selected_RHwater_pct=rw[i],
                selected_RHice_pct=ri[i],
                selected_water_QBOT_physically_valid=bool(water[i]),
                source_QC0_measured_VPD=(float(r.VPD_F_QC)==0),
                original_and_selected_VPD_differ=bool(not np.isclose(
                    ov,v[i],rtol=0,atol=1e-9)),
                original_QC_not_independent_validation=True))
    daydf=pd.DataFrame(events)
    edges=[]
    for name,aa,bb in BOUNDARIES:
        i=idmap[aa];j=idmap[bb]
        guard(j==i+1,"old four documented source boundaries not direct 30min")
        for side,idx in (("left",i),("right",j)):
            z=k[idx];r=raw.loc[z]
            edges.append(dict(boundary=name,side=side,native_key=z,
                native_time=s.time.iloc[idx],
                source_VPD_QC=r.VPD_F_QC,source_T_QC=r.TA_F_QC,
                original_source_VPD_hPa=float(r.VPD_F),
                previous_Stage11L_VPD_hPa=old_v[idx],
                selected_stage=stage,selected_VPD_hPa=v[idx],
                selected_RH_water_pct=rw[idx],
                selected_actual_vapour_e_hPa=e[idx],
                selected_VPD_QBOT_valid=bool(water[idx]),
                measured_original_QC0=(float(r.VPD_F_QC)==0),
                full_edge_jump_hPa=float(abs(v[j]-v[i])),
                previous_Stage11L_jump_hPa=float(abs(old_v[j]-old_v[i])),
                exceeds_old_4hPa_guard=bool(abs(v[j]-v[i])>4),
                repair_approved=False))
    edge=pd.DataFrame(edges)
    year=dt.dt.year.to_numpy()
    totals=[]
    for y in sorted(set(year)):
        w=year==y
        totals.append(dict(year=int(y),half_hours=int(w.sum()),
          missing=int((~complete&w).sum()),water_QBOT_failed=int((~water&w).sum()),
          temperature_conversion_failed=int((~tk&w).sum()),
          water_RH_below5pct=int((dry_warn&w).sum()),
          ice_RH_above100pct=int((ice_warn&w).sum()),
          negative_wind=int((wind_bad&w).sum()),
          negative_precip=int((pr_bad&w).sum()),
          negative_SW=int((sw_bad&w).sum()),
          negative_LW=int((lw_bad&w).sum())))
    annual=pd.DataFrame(totals)
    overview={"version":"US-NC2-onepass-v1-20261029","site":"US-NC2",
       "selected_stage":stage,"selected_file":str(source),
       "signed_receipt_SHA256":sha(source.parent/(QREC if stage=="STAGE11Q" else LREC)),
       "original_tower_release_SHA256":sha(orig["primary"]),
       "original_source_ERA_SHA256":sha(orig["era"]),
       "source_native_30min_rows":len(s),
       "missing_meteorology":int((~complete).sum()),
       "water_vpd_QBOT_closure_fail":int((~water).sum()),
       "TBOT_TA_conversion_fail":int((~tk).sum()),
       "ice_RH_over100pct":int(ice_warn.sum()),
       "water_RH_below5pct":int(dry_warn.sum()),
       "four_documented_boundary_max_deltaVPD":float(edge.full_edge_jump_hPa.max()),
       "four_boundaries_over4hPa":int(edge.loc[edge.exceeds_old_4hPa_guard,"boundary"].nunique()),
       "source_QC0_not_implied_by_CDS_ERA5":True,
       "PFT_ZBOT_UTC_DATM_not_checked":True,
       "postv5_D​ATM_AD400_approved":False,
       "original_source_and_prior_shadow_unchanged":True}
    print("\nUS-NC2 ALL 367920 NATIVE HALFHOURS",flush=True)
    print(json.dumps(overview,indent=2),flush=True)
    print("\nUS-NC2 FOUR EXISTING 2025 SOURCE-NATIVE HUMIDITY EVENT BOUNDARIES",flush=True)
    print(edge[["boundary","side","native_time","source_VPD_QC",
        "original_source_VPD_hPa","previous_Stage11L_VPD_hPa",
        "selected_VPD_hPa","selected_RH_water_pct",
        "selected_VPD_QBOT_valid","full_edge_jump_hPa"]].to_string(index=False),flush=True)
    print("\nUS-NC2 ALL 21 YEARS summary",flush=True)
    print(annual.to_string(index=False),flush=True)
    print("US-NC2 2025 THREE-DAY SOURCE-NATIVE CLASSIFICATION COUNTS:")
    for date,df in daydf.groupby(daydf.native_key.str.slice(0,8)):
        print(date,"original_VPD_QC0",int(df.source_QC0_measured_VPD.sum()),
              "original_invalid_RH",int((df.original_implied_RHwater_pct<0).sum()),
              "selected_water_unphysical",int((~df.selected_water_QBOT_physically_valid).sum()),
              "selected_source_different",int(df.original_and_selected_VPD_differ.sum()),flush=True)
    print("US-NC2 ONEPASS HUMAN SCIENCE ASSESSMENT PREPARED | NO SOURCE/CASE/SLURM WRITES",flush=True)
    return overview,annual,daydf,edge
def main():
    p=argparse.ArgumentParser()
    group=p.add_mutually_exclusive_group(required=True)
    for k in ("self-test","check","run"):group.add_argument("--"+k,action="store_true")
    a=p.parse_args()
    selftest()
    if a.self_test:return
    overview,annual,days,edges=assess()
    if a.check:return
    report=R/"reports"/("us_nc2_2025_march_onepass_source_manual_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    report.mkdir(parents=True,exist_ok=False)
    tables={"US_NC2_21year_science_QA.csv":annual,
        "US_NC2_2025_Mar18_23_25_original_tower_ERA_selected.csv":days,
        "US_NC2_four_original_source_boundary_comparison.csv":edges}
    hashes={}
    for name,tab in tables.items():
        tab.to_csv(report/name,index=False,float_format="%.17g")
        hashes[name]=sha(report/name)
    (report/"US_NC2_summary.json").write_text(json.dumps(overview,indent=2)+"\n")
    hashes["US_NC2_summary.json"]=sha(report/"US_NC2_summary.json")
    (report/"US_NC2_signed_readonly_receipt.json").write_text(json.dumps(
      {"version":"US-NC2-onepass-v1-20261029","output_SHA256":hashes,
       "source_or_forcing_modified":False,"Postv5_approved":False,
       "DATM_ready":False,"Slurm":False},indent=2)+"\n")
    print("US-NC2 ONEPASS REPORT:",report,flush=True)
    print("US-NC2 367920 ONEPASS SCIENCE REVIEW SUCCESS | ORIGINALS UNCHANGED",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as e:
        print("US-NC2 ONEPASS FAIL CLOSED:",e,file=sys.stderr,flush=True)
        raise

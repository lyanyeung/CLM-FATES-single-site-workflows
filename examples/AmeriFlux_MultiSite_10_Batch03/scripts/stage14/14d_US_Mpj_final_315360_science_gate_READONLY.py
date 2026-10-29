#!/usr/bin/env python3
"""US-Mpj one-pass latest 315360-row source science admission screen, READ ONLY.

Checks the actual Stage13O signed research shadow against immutable Stage07:
native NOLEAP chronology, 17 paired VPD/QBOT-only source edits; 3 original
2014 centre values, 2 originally preserved Feb2018 VPD and approved Feb2020
TA unchanged; whole-site meteorological completeness, e/QBOT closure, water
and ice saturation distribution, annual exception counts. Not Post-v5,
PFT admission, DATM or job authorization.
--check prints only. --run emits a NEW SHA-sealed report; no prior data edits.
"""
import argparse,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np,pandas as pd
sys.dont_write_bytecode=True
VER="US-Mpj-315360-full-meteorology-onepass-v1-20261029"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
P=R/"science_trials/stage13o_Mpj_20HH_operator_approved_ERA_RH_20261026T210746Z_5c3c8653"
OLD=R/"qcv5_native_trial_20261022T024559Z_36c46e58/US-Mpj/forcing/processed_v5/US-Mpj_CLM_forcing_2008_2025.csv"
SRC=P/"US-Mpj_CLM_forcing_2008_2025_STAGE13O_20HH_ERA_RH_RESEARCH_SHADOW.csv"
RECEIPT=P/"stage13o_Mpj_20HH_ERA_RH_SHA_receipt.json"
EVID=P/"exact_20_original_QC1_ERA_RH_VPD_QBOT_science_source_ledger.csv"
FIELDS=["time","TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE"]
KEYS={
    "2014-10-11 02:30:00","2014-10-11 04:30:00",
    "2014-10-21 08:30:00",
}
PRESERVE=["2018-02-02 17:30:00","2018-02-02 19:00:00",
          "2020-02-11 06:30:00"]
def need(ok,msg):
    if not bool(ok):raise RuntimeError("US-Mpj FULL SITE STOP: "+msg)
def digest(p):
    p=Path(p);need(p.is_file() and not p.is_symlink(),"missing source "+str(p))
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def esw(t):
    t=np.asarray(t,float)
    return 6.112*np.exp(17.67*t/(t+243.5))
def esi(t):
    t=np.asarray(t,float)
    return 6.112*np.exp(22.46*t/(t+272.62))
def self_test():
    need(len(FIELDS)==10 and 18*365*48==315360,"315360/NOLEAP source count")
    need(float(esi(-20))<float(esw(-20)),"subzero ice/water saturation")
    a=pd.Series(["2008-01-01",None]);b=pd.Series(["2008-01-01",None])
    need(a.equals(b),"pandas exact string including missing value comparison")
    print("US-Mpj ONEPASS SELF-TEST PASS | no scientific inputs changed",flush=True)
def load():
    need(P.is_dir() and not P.is_symlink(),"actual Stage13O user-confirmed run folder")
    rec=json.loads(RECEIPT.read_text())
    need(rec.get("version")=="batch03-stage13o-v1-20261026-two-full-QC1-source-runs"
         and rec.get("DATM_ready") is False
         and rec.get("production_Postv5_authorized") is False
         and rec.get("spinup_authorized") is False
         and rec.get("new_edits",{}).get("VPD_USE")==17
         and rec.get("new_edits",{}).get("QBOT")==17
         and rec.get("original_2018_and_2020_preserved") is True,
         "Stage13O original signed science receipt or model hold changed")
    for f,hash_ in rec["output_SHA256"].items():
        need(digest(P/f)==hash_,"Stage13O SHA verification failure "+f)
    need(digest(OLD)==rec["original_Stage07_sha256"],
         "Stage07 original 18yr forcing parent SHA changed")
    source=pd.read_csv(SRC,dtype={"time":str},low_memory=False)
    old=pd.read_csv(OLD,dtype={"time":str},low_memory=False)
    need(list(source.columns)==FIELDS==list(old.columns) and
         len(source)==len(old)==315360,
         "Stage13O 315360 native original source schema changed")
    need(source.time.equals(old.time),"original and repaired native timestamps differ")
    dt=pd.to_datetime(source.time,format="%Y-%m-%d %H:%M:%S",errors="raise")
    expected=pd.date_range("2008-01-01","2025-12-31 23:30",freq="30min")
    expected=expected[~((expected.month==2)&(expected.day==29))]
    need(len(expected)==315360 and
         np.array_equal(dt.to_numpy(),expected.to_numpy()),
         "exact native 2008-2025 NOLEAP chronology differs")
    changes={}
    for c in FIELDS:
        if c=="time":
            changes[c]=np.zeros(len(source),dtype=bool)
            continue
        v=pd.to_numeric(source[c],errors="raise").to_numpy(float)
        o=pd.to_numeric(old[c],errors="raise").to_numpy(float)
        changes[c]=~np.isclose(v,o,atol=1e-12,rtol=0,equal_nan=True)
        need(not changes[c].any() if c not in ("VPD_USE","QBOT") else True,
             "unauthorized original meteorology edit to "+c)
    need(int(changes["VPD_USE"].sum())==17 and
         np.array_equal(changes["VPD_USE"],changes["QBOT"]),
         "operator-approved 17 2014 source VPD/QBOT times differ")
    ledger=pd.read_csv(EVID,low_memory=False)
    need(len(ledger)==20,"two signed source QC1 10HH episodes must have 20 rows")
    years=dt.dt.year.to_numpy()
    for t in PRESERVE+list(KEYS):
        z=np.flatnonzero(dt.eq(pd.Timestamp(t)).to_numpy())
        need(len(z)==1 and not changes["VPD_USE"][z[0]],
             "protected original 2014/2018/2020 source value altered "+t)
    return source,old,rec,dt,years,changes
def assess():
    s,o,rec,dt,years,changes=load()
    arr={f:pd.to_numeric(s[f],errors="raise").to_numpy(float) for f in FIELDS[1:]}
    t=arr["TA_USE"];p=arr["PSRF"];v=arr["VPD_USE"];q=arr["QBOT"]
    es=esw(t);ei=esi(t);e=es-v
    with np.errstate(divide="ignore",invalid="ignore"):
        qcheck=0.622*(100*e)/(p-0.378*(100*e))
        rw=100*e/es
        ri=100*e/ei
    complete=np.ones(len(s),dtype=bool)
    for x in arr.values():complete &=np.isfinite(x)
    phase_ok=complete&(p>=50000)&(p<=110000)&(t>=-80)&(t<=65)
    physics=phase_ok&(v>=0)&(v<=es)&(e>=0)&(q>0)&(q<.08)&(
         np.isclose(q,qcheck,rtol=1e-7,atol=1e-9))
    temp=phase_ok&(np.abs(arr["TBOT"]-t-273.15)<=1e-8)
    wind=complete&(arr["WIND"]>=0)
    rain=complete&(arr["PRECTmms"]>=0)
    sw=complete&(arr["FSDS"]>=-1)
    lw=complete&(arr["FLDS"]>=0)
    low_rh=physics&(rw<5)
    ice_high=physics&(t<0)&(ri>100)
    bad=np.flatnonzero(~physics|~temp|~wind|~rain|~sw|~lw|low_rh|ice_high)
    data=pd.DataFrame({
      "native_time":s.time.iloc[bad].to_numpy(),
      "year":years[bad],"T_C":t[bad],"PSRF_Pa":p[bad],
      "VPD_hPa":v[bad],"QBOT_kgkg":q[bad],
      "RH_water_pct":rw[bad],"RH_ice_pct":ri[bad],
      "source_ERA_repair_2014":changes["VPD_USE"][bad],
      "missing_meteorology":~complete[bad],
      "water_QBOT_closure_issue":~physics[bad],
      "TBOT_conversion_issue":~temp[bad],
      "wind_negative":~wind[bad],
      "precip_negative":~rain[bad],
      "shortwave_below_minus1":~sw[bad],
      "longwave_negative":~lw[bad],
      "RHwater_below5pct_caution":low_rh[bad],
      "RHice_gt100pct_caution":ice_high[bad],
      "science_not_production_approved":True
    })
    rows=[]
    for year in sorted(set(years)):
        y=years==year
        rows.append({"year":int(year),"rows":int(y.sum()),
         "meteorology_missing":int((~complete&y).sum()),
         "physics_nonclosure":int((~physics&y).sum()),
         "TBOT_nonclosure":int((~temp&y).sum()),
         "negative_wind":int((~wind&y).sum()),
         "negative_precip":int((~rain&y).sum()),
         "negative_SW":int((~sw&y).sum()),
         "negative_LW":int((~lw&y).sum()),
         "RHwater_below5pct":int((low_rh&y).sum()),
         "RHice_above100pct":int((ice_high&y).sum()),
         "Stage13O_new_changed_rows":int((changes["VPD_USE"]&y).sum())})
    annual=pd.DataFrame(rows)
    summary={
      "version":VER,"site":"US-Mpj","native_hh":len(s),
      "model_columns":FIELDS,"full_noleap_chronology_correct":True,
      "source_Stage13O_receipt_sha256":digest(RECEIPT),
      "immutable_Stage07_parent_sha256":digest(OLD),
      "changed_VPD_and_QBOT_source_native_halfhours":17,
      "all_meteorology_finite":bool(complete.all()),
      "all_water_VPD_QBOT_consistent":bool(physics.all()),
      "all_TBOT_TA_consistent":bool(temp.all()),
      "negative_wind_rows":int((~wind).sum()),
      "negative_precip_rows":int((~rain).sum()),
      "negative_FSDS_rows":int((~sw).sum()),
      "negative_FLDS_rows":int((~lw).sum()),
      "RHwater_below5pct_warning":int(low_rh.sum()),
      "RHice_above100pct_warning":int(ice_high.sum()),
      "PFT_surface_height_not_audited":True,
      "postv5_DATM_AD400_approval":False,
      "no_existing_science_input_writes":True}
    print("\nUS-Mpj 315360 EXACT NATIVE MET FORENSIC SUMMARY",flush=True)
    print(json.dumps(summary,indent=2),flush=True)
    print("\nUS-Mpj PER YEAR (SOURCE QUALITY NOT EQUAL TO TOWER TRUTH)",flush=True)
    print(annual.to_string(index=False),flush=True)
    if len(data):
        print("\nUS-Mpj FIRST UP TO 35 ATTENTION ROWS",flush=True)
        print(data.head(35).to_string(index=False),flush=True)
    else:print("\nUS-Mpj NO WIDE-MET/PHYSICS FLAGS IN PROPOSED RESEARCH INPUT",flush=True)
    print("US-Mpj SOURCE PHYSICS SCREEN COMPLETE; operator to decide remaining QA/PFT admission",flush=True)
    return summary,annual,data
def main():
    a=argparse.ArgumentParser()
    k=a.add_mutually_exclusive_group(required=True)
    k.add_argument("--self-test",action="store_true")
    k.add_argument("--check",action="store_true")
    k.add_argument("--run",action="store_true")
    args=a.parse_args()
    self_test()
    if args.self_test:return
    summary,annual,issues=assess()
    if args.check:
        print("US-Mpj READONLY CHECK SUCCESS | no output/source writes",flush=True)
        return
    out=R/"reports"/("us_mpj_315360_science_gate_READONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(exist_ok=False,parents=True)
    docs={"US_Mpj_annual_meteorology_science_summary.csv":annual,
          "US_Mpj_original_humidity_physical_attention_rows.csv":issues}
    hashes={}
    for fn,df in docs.items():
        df.to_csv(out/fn,index=False)
        hashes[fn]=digest(out/fn)
    (out/"US_Mpj_full_site_readonly_assessment.json").write_text(json.dumps(summary,indent=2)+"\n")
    hashes["US_Mpj_full_site_readonly_assessment.json"]=digest(out/"US_Mpj_full_site_readonly_assessment.json")
    (out/"US_Mpj_315360_READONLY_SHA_receipt.json").write_text(json.dumps(
         {"version":VER,"site":"US-Mpj","outputs_SHA256":hashes,
          "no_model_job_or_forcing_writes":True},indent=2)+"\n")
    print("US-Mpj SCIENCE GATE REPORT:",out,flush=True)
    print("US-Mpj SCIENCE ONEPASS SUCCESS | SOURCE ORIGINAL INTACT, NO SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as e:
        print("US-Mpj SCIENCE AUDIT FAIL CLOSED:",e,file=sys.stderr,flush=True)
        raise

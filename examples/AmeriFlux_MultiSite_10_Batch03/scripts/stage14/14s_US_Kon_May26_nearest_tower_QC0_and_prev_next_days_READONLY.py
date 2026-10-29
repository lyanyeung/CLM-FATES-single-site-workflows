#!/usr/bin/env python3
"""Read-only US-Kon May 26 2011 source T-QC1 plateau and nearest true T QC0.

Outputs: exact native 02:00/02:30 source QC; contiguous source TA_F QC1
run endpoints; nearest 6 real TA_F QC0 before and after the failure;
May 25/26/27 native local 00:00–12:00 side-by-side with FLUXNET paired
TA_ERA and separately downloaded SHA-verified ERA5-Land T2m.
No source writes, model writes, science overlays or Slurm.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
SRC=R/"qcv5_native_trial_20261022T024559Z_36c46e58/exact_input_manifest.json"
READER=Path.home()/"US_Kon_nine_tower_ERA5Land_pm2h.py"
EXPECTED_READER_BLOB="dabc868924ec46a5a2905ad3505a100fd1974e52"
QC_CENTER="201105260200"
BIF_UTC_OFFSET_H=-6

def need(ok,msg):
    if not bool(ok):raise RuntimeError("US-Kon QC0-NEIGHBOR READONLY STOP: "+msg)
def sha(p):
    p=Path(p)
    need(p.is_file() and not p.is_symlink(),"missing original file "+str(p))
    d=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):d.update(chunk)
    return d.hexdigest()

def read_inputs():
    manifest=json.loads(SRC.read_text())
    site=[x for x in manifest["sites"] if x["site"]=="US-Kon"]
    need(len(site)==1 and int(site[0]["native_minutes"])==30 and
         int(site[0]["first_year"])==2004 and
         int(site[0]["last_year"])==2019,
         "original signed US-Kon site/clock changed")
    spec=site[0]
    for kind in ("primary","era"):
        fp=Path(spec[kind])
        need(sha(fp)==manifest["input_sha256"].get(str(fp.resolve())),
             "original tower/companion ERA SHA mismatch "+kind)
    a=pd.read_csv(spec["primary"],usecols=[
        "TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"],
        dtype={"TIMESTAMP_START":str},low_memory=False)
    b=pd.read_csv(spec["era"],
        usecols=["TIMESTAMP_START","TA_ERA","VPD_ERA"],
        dtype={"TIMESTAMP_START":str},low_memory=False)
    need(a.TIMESTAMP_START.is_unique and b.TIMESTAMP_START.is_unique,
         "original source has duplicate HH timestamps")
    a=a.set_index("TIMESTAMP_START")
    b=b.set_index("TIMESTAMP_START")
    a=a.loc[a.index.str[:4]=="2011"].copy()
    b=b.loc[b.index.str[:4]=="2011"].copy()
    need(a.index.is_monotonic_increasing and
         a.index.equals(b.index) and
         QC_CENTER in a.index,
         "2011 native tower and paired ERA clocks not aligned")
    for c in a.columns:a[c]=pd.to_numeric(a[c],errors="coerce").mask(
        lambda x:x<=-9990)
    for c in b.columns:b[c]=pd.to_numeric(b[c],errors="coerce").mask(
        lambda x:x<=-9990)
    return a.join(b,validate="one_to_one")

def grid_reader():
    need(sha(READER) is not None,"grid source helper missing")
    bb=READER.read_bytes()
    blob=hashlib.sha1(b"blob "+str(len(bb)).encode()+b"\0"+bb).hexdigest()
    need(blob==EXPECTED_READER_BLOB,"Stage14O original ERA5-Land loader blob changed")
    sp=importlib.util.spec_from_file_location("kon_signed_stage14o",str(READER))
    mod=importlib.util.module_from_spec(sp)
    sp.loader.exec_module(mod)
    grid,status=mod.read_grid(2011)
    need(grid is not None,"ERA5-Land original source missing "+status)
    t,data=grid
    need(set(data)=={"t2m","d2m","sp"},"ERA5-Land source incomplete")
    return t,data,status

def with_grid(d,clock,data):
    out=d.copy()
    local=pd.to_datetime(out.index,format="%Y%m%d%H%M",errors="raise")
    utc=local+pd.Timedelta(minutes=15)-pd.Timedelta(hours=BIF_UTC_OFFSET_H)
    need(utc.min()>=clock.min() and utc.max()<=clock.max(),
         "native timestamp out of verified ERA5-Land UTC clock")
    xp=clock.asi8.astype(float)/1e9
    xx=utc.asi8.astype(float)/1e9
    out["ERA5Land_T2m_C"]=np.interp(xx,xp,data["t2m"])-273.15
    out["Tower_minus_ERA5_C"]=out.TA_F-out.ERA5Land_T2m_C
    out["Tower_minus_FLUX_ERA_C"]=out.TA_F-out.TA_ERA
    return out

def display(out,label):
    use=["TA_F","TA_F_QC","VPD_F_QC","TA_ERA","ERA5Land_T2m_C",
         "Tower_minus_ERA5_C","Tower_minus_FLUX_ERA_C"]
    print("\n"+"="*84)
    print(label)
    print("="*84)
    print(out[use].round(3).to_string(na_rep="—"),flush=True)

def main():
    s=read_inputs()
    clock,gd,status=grid_reader()
    center=s.index.get_loc(QC_CENTER)
    need(isinstance(center,(int,np.integer)) and
         int(s.TA_F_QC.iloc[center])==1 and
         int(s.TA_F_QC.loc["201105260230"])==1,
         "original 02:00/02:30 source T must both be QC1")
    print("US-Kon ORIGINAL TIME LOCAL STANDARD UTC-6; grid use native start+15m+6h UTC")
    print("Verified actual ERA5-Land source:",status)
    print("Original 02:00 T/QC:",s.loc["201105260200",["TA_F","TA_F_QC"]].to_dict())
    print("Original 02:30 T/QC:",s.loc["201105260230",["TA_F","TA_F_QC"]].to_dict())
    print("Stage14R 02:00→02:30 ΔT=4.407°C was a mixing boundary, NOT observed QC0")

    # Find entire continuous source QC1 run containing the event (do not
    # pretend a distant or QC1 donor is measured).
    start=center
    end=center
    qc=s.TA_F_QC.to_numpy()
    while start>0 and qc[start-1]==1 and (
            pd.to_datetime(s.index[start],format="%Y%m%d%H%M")-
            pd.to_datetime(s.index[start-1],format="%Y%m%d%H%M")==pd.Timedelta(minutes=30)):
        start-=1
    while end<len(s)-1 and qc[end+1]==1 and (
            pd.to_datetime(s.index[end+1],format="%Y%m%d%H%M")-
            pd.to_datetime(s.index[end],format="%Y%m%d%H%M")==pd.Timedelta(minutes=30)):
        end+=1
    print("\nEXACT CONTIGUOUS ORIGINAL TA_F_QC1 PLATFORM",
          s.index[start],"to",s.index[end],"HH",end-start+1)
    print("QC1 first/last T °C:",float(s.TA_F.iloc[start]),float(s.TA_F.iloc[end]))
    before=s.iloc[:center].loc[lambda x:x.TA_F_QC.eq(0)&x.TA_F.notna()].tail(6)
    after=s.iloc[center+1:].loc[lambda x:x.TA_F_QC.eq(0)&x.TA_F.notna()].head(6)
    need(not before.empty and not after.empty,
         "true observed QC0 T anchors not found in 2011")
    center_dt=pd.to_datetime(QC_CENTER,format="%Y%m%d%H%M")
    print("\nNEAREST 6 ACTUAL MEASURED TEMPERATURE QC0 BEFORE 02:00")
    display(with_grid(before,clock,gd),"source temperature QC0 before")
    print("\nNEAREST 6 ACTUAL MEASURED TEMPERATURE QC0 AFTER 02:00")
    display(with_grid(after,clock,gd),"source temperature QC0 after")
    closest_before=pd.to_datetime(before.index[-1],format="%Y%m%d%H%M")
    closest_after=pd.to_datetime(after.index[0],format="%Y%m%d%H%M")
    print("NEAREST MEASURED QC0 GAPS, hours:",
          "prior",round((center_dt-closest_before).total_seconds()/3600,2),
          "next",round((closest_after-center_dt).total_seconds()/3600,2))

    # Compare exact same local clock hours previous and next days; QC1
    # never silently relabelled measured.
    dates=["2011-05-25","2011-05-26","2011-05-27"]
    for day in dates:
        ks=pd.date_range(day+" 00:00",day+" 12:00",freq="30min").strftime("%Y%m%d%H%M")
        part=s.reindex(ks)
        need(part.TA_F.notna().all(),"source local day has missing original TA_F "+day)
        counts=part.TA_F_QC.value_counts().to_dict()
        print("\nDAY",day,"00:00–12:00 T_QC counts",counts)
        gridpart=with_grid(part,clock,gd)
        if day=="2011-05-26":
            display(gridpart,"EVENT DAY all 30min 00:00–12:00")
        else:
            display(gridpart.iloc[::2],"CONTROL "+day+" hourly 00:00–12:00")
    print("\nRESULT: read-only SOURCE and ERA5-Land audit; no forcing, case, Slurm or reports written.")
    print("Do not infer actual tower measurements from any TA_F_QC1 plateau.")

if __name__=="__main__":
    main()

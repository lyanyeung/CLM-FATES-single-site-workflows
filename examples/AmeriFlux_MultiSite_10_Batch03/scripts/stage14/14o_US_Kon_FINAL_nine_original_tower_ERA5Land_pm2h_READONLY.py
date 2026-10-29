#!/usr/bin/env python3
"""US-Kon nine protected VPD/QBOT source events: direct ±2h FULL VALUES.

Read ONLY immutable original AmeriFlux FLUXMET and its paired ERA
(verified by original Stage07 source SHA), selected signed Stage14K
research tape, and ORIGINAL locally downloaded SHA-verified ERA5-Land
point NetCDF/ZIP for 2011/2012 when present. No ERA5 download, no new
fill, no reports, Slurm, DATM or other source writes.

Seven CONTIGUOUS event windows combine the three 2011-Feb22 holds;
all source-native 30-minute records ±2h are printed.
Original QC0 only denotes actual tower measurements: QC1 gapfilled,
QC2 ERA-dependent. RH calculated from original TA_F/VPD_F
is NOT a separately measured raw RH sensor.
Local TIMESTAMP_START +15min, UTC offset -6h (BIF; provisional model
clock approval) maps to existing ERA5-Land UTC hourly data.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
try:
    from netCDF4 import Dataset,num2date
    NC_OK=True
except ImportError:
    NC_OK=False

VERSION="Kon-nine-actual-native-original-tower-paired-ERA-verified-ERA5Land-v1-20261029"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S=R/"qcv5_native_trial_20261022T024559Z_36c46e58"
K=R/"science_trials/US_Kon_68_ERA_RH_9HARD_HOLD_SCENARIO_20261029T044949Z_ebbfd739"
KF="US-Kon_280320_ERA_RH68_9HOLD_RESEARCH_ONLY_NOT_DATM.csv"
HOLD=["201102220830","201102220900","201102220930",
      "201105261100","201109291830","201110150730",
      "201110230730","201202251030","201208050900"]
# Seven discrete episodes, not nine repetitive overlapping tables
GROUPS=[
 ("2011-02-22 trio",["201102220830","201102220900","201102220930"]),
 ("2011-05-26",["201105261100"]),
 ("2011-09-29",["201109291830"]),
 ("2011-10-15",["201110150730"]),
 ("2011-10-23",["201110230730"]),
 ("2012-02-25",["201202251030"]),
 ("2012-08-05",["201208050900"])
]
SITE="US-Kon"; UTC_OFFSET_H=-6
def require(ok,reason):
    if not bool(ok): raise RuntimeError("US-Kon NINE SOURCE AUDIT STOP: "+str(reason))
def readable(f):
    f=Path(f);require(f.is_file() and not f.is_symlink(),"missing original "+str(f));return f
def sha(f):
    h=hashlib.sha256()
    with readable(f).open("rb") as z:
        for b in iter(lambda:z.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def key(t):
    return pd.Series(t).astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)
def sat(t):
    t=np.asarray(t,dtype=float)
    with np.errstate(invalid="ignore",divide="ignore",over="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))
def safe_numbers(s):
    x=pd.to_numeric(s,errors="coerce")
    return x.mask(x<=-9990)
def weighted_range():
    times=[]
    for title,keys in GROUPS:
        ts=pd.to_datetime(keys,format="%Y%m%d%H%M")
        times.extend(pd.date_range(ts.min()-pd.Timedelta(hours=2),
                                   ts.max()+pd.Timedelta(hours=2),
                                   freq="30min"))
    return pd.DatetimeIndex(sorted(set(times)))
def self_test():
    require(len(HOLD)==9 and sum(len(g) for _,g in GROUPS)==9 and
            len(set(k for _,g in GROUPS for k in g))==9 and
            len(pd.date_range("2011-02-22 06:30","2011-02-22 11:30",freq="30min"))==11 and
            abs(float(sat(20))-23.369471)<0.01,
            "nine center keys/time/physics regression")
    print("US-Kon NINE ±2H ORIGINAL TOWER/PAIRED ERA/ERA5-LAND SELF-TEST PASS",flush=True)
def original_and_selected():
    receipt=json.loads(readable(K/"US_Kon_68_9_SHA_receipt.json").read_text())
    require(receipt.get("version")=="batch03-US-Kon-68ERA-RH-research-9HOLD-v1-20261029" and
            receipt.get("DATM_ready") is False and
            receipt.get("output_SHA256",{}).get(KF)==sha(K/KF),
            "Stage14K signed selected original source changed")
    mf=json.loads(readable(S/"exact_input_manifest.json").read_text())
    matches=[x for x in mf["sites"] if x["site"]==SITE]
    require(len(matches)==1 and int(matches[0]["native_minutes"])==30 and
            int(matches[0]["first_year"])==2004 and
            int(matches[0]["last_year"])==2019,
            "original site release metadata changed")
    spec=matches[0]
    for field in ("primary","era"):
        f=readable(spec[field])
        require(mf["input_sha256"].get(str(f.resolve()))==sha(f),
                "original tower or paired ERA SHA changed: "+field)
    selected=pd.read_csv(readable(K/KF),dtype={"time":str},low_memory=False)
    require(len(selected)==280320 and
            {"time","TA_USE","VPD_USE","QBOT","PSRF"}<=set(selected.columns),
            "original 280320 model source schema changed")
    selected["native_key"]=key(selected.time).to_numpy()
    require(selected.native_key.is_unique,"selected original time duplicate")
    selected=selected.set_index("native_key")
    require(set(selected.index[selected.VPD_USE.isna()])==set(HOLD) and
            set(selected.index[selected.QBOT.isna()])==set(HOLD),
            "actual original nine special HOLDs missing mask changed")
    wanted=weighted_range().strftime("%Y%m%d%H%M")
    def source_csv(path,required_cols,optional_cols=()):
        head=list(pd.read_csv(readable(path),nrows=0).columns)
        cols=["TIMESTAMP_START"]+required_cols+[c for c in optional_cols if c in head]
        require(set(cols)<=set(head),"original source lacks required columns "+str(path))
        frame=pd.read_csv(path,usecols=cols,dtype={"TIMESTAMP_START":str},
                          low_memory=False)
        require(frame.TIMESTAMP_START.is_unique,"original release timestamp duplicated")
        frame=frame.loc[frame.TIMESTAMP_START.isin(wanted)].copy()
        frame=frame.set_index("TIMESTAMP_START").reindex(wanted)
        require(len(frame)==len(wanted) and not frame[required_cols].isna().all(axis=1).any(),
                "original selected time not found in source "+str(path))
        for c in frame.columns:frame[c]=safe_numbers(frame[c])
        return frame
    tower=source_csv(spec["primary"],["TA_F","TA_F_QC","VPD_F","VPD_F_QC"],
           ["VPD_F_MDS","RH","RH_F","RH_F_QC"])
    era=source_csv(spec["era"],["TA_ERA","VPD_ERA"])
    selected=selected.reindex(wanted)
    require(selected.TA_USE.notna().all() and selected.PSRF.notna().all(),
            "selected source T or pressure missing around nine center events")
    c=tower.join(era,validate="one_to_one").join(
        selected[["TA_USE","VPD_USE","QBOT","PSRF"]],validate="one_to_one")
    c.index.name="native_key"
    c["local_time"]=pd.to_datetime(c.index,format="%Y%m%d%H%M").strftime("%Y-%m-%d %H:%M")
    c["center_HOLD"]=c.index.isin(HOLD)
    c["original_RH_from_T_VPD_pct"]=100*(1-c.VPD_F/sat(c.TA_F))
    true=(c.TA_F_QC.eq(0)&c.VPD_F_QC.eq(0)&
          c.TA_F.notna()&c.VPD_F.notna()&
          c.original_RH_from_T_VPD_pct.between(0,100))
    c["original_both_QC0_measured_RH_derived_pct"]=c.original_RH_from_T_VPD_pct.where(true)
    c["companion_ERA_RH_from_T_VPD_pct"]=100*(1-c.VPD_ERA/sat(c.TA_ERA))
    c["selected_RHwater_pct"]=100*(1-c.VPD_USE/sat(c.TA_USE))
    c["ERA5Land_T2m_C"]=np.nan
    c["ERA5Land_D2m_C"]=np.nan
    c["ERA5Land_RHwater_pct"]=np.nan
    c["ERA5Land_SP_Pa"]=np.nan
    c["ERA5Land_grid_RH_at_selected_T_VPD_hPa"]=np.nan
    return c

def read_grid(year):
    # Original Stage09f and later Stage12f (both signed CDS products)
    stems=[
      R/"external_evidence/era5land_timeseries"/SITE/str(year)/
        f"ERA5Land_{SITE}_{year}_t2m_d2m_sp",
      R/"external_evidence/era5land_timeseries_stage12f_missing_years"/SITE/str(year)/
        f"ERA5Land_{SITE}_{year}_stage12f_t2m_d2m_sp"
    ]
    verified=[]
    for stem in stems:
        receipt=Path(str(stem)+".receipt.json")
        files=[Path(str(stem)+ext) for ext in (".zip",".nc")]
        present=[f for f in files if f.exists()]
        if not receipt.exists() and not present:continue
        require(len(present)==1 and receipt.is_file() and not receipt.is_symlink(),
                "incomplete or ambiguous signed ERA5-Land artifact "+str(stem))
        f=readable(present[0]);r=json.loads(readable(receipt).read_text())
        expect=r.get("response_sha256",r.get("artifact_sha256"))
        require(r.get("site")==SITE and int(r.get("year",-1))==year and
                expect==sha(f) and r.get("request",{}).get("location"),
                "ERA5-Land downloaded original SHA or metadata mismatch "+str(f))
        pos=r["request"]["location"]
        verified.append((f,float(pos["latitude"]),float(pos["longitude"])))
    if not verified:
        return None,"NO_SHA_VERIFIED_ERA5LAND_LOCAL_SOURCE_FOR_YEAR_"+str(year)
    require(len(verified)==1,"multiple independent ERA5-Land source artifacts for year; manual selection needed")
    f,lat,lon=verified[0]
    require(NC_OK,"netCDF4 required to read existing ERA5-Land NetCDF/ZIP")
    expected=pd.date_range(f"{year-1}-12-29 00:00:00",
                           f"{year+1}-01-03 23:00:00",freq="h")
    fields={}
    coords=[]
    def load_ds(ds):
        time=ds.variables.get("valid_time")
        if time is None:time=ds.variables.get("time")
        require(time is not None and getattr(time,"units",None),
                "ERA5-Land original UTC CF time missing")
        dates=num2date(time[:],time.units,
                      calendar=getattr(time,"calendar","standard"),
                      only_use_cftime_datetimes=False,
                      only_use_python_datetimes=True)
        d=pd.DatetimeIndex(pd.to_datetime([str(x) for x in dates]))
        require(d.equals(expected),"ERA5-Land original UTC hourly evidence time incorrect")
        lat_v=float(np.asarray(ds.variables["latitude"][:]).reshape(-1)[0])
        lon_v=float(np.asarray(ds.variables["longitude"][:]).reshape(-1)[0])
        require(abs(lat_v-lat)<.151 and abs(lon_v-lon)<.151,
                "ERA5-Land gridpoint request geometry changed")
        coords.append((lat_v,lon_v))
        for fld,unit in (("t2m","K"),("d2m","K"),("sp","Pa")):
            if fld not in ds.variables:continue
            require(fld not in fields and str(getattr(ds.variables[fld],"units",""))==unit,
                    "ERA5-Land variable duplicated or changed units "+fld)
            a=np.asarray(np.ma.asarray(ds.variables[fld][:]).filled(np.nan),
                         dtype=float).reshape(-1)
            require(len(a)==len(expected) and np.isfinite(a).all(),
                    "ERA5-Land source variable invalid "+fld)
            fields[fld]=a
    if zipfile.is_zipfile(f):
        with zipfile.ZipFile(f) as z:
            require(z.testzip() is None,"ERA5-Land original ZIP CRC corrupt")
            members=[m for m in z.infolist() if m.filename.endswith(".nc")]
            require(1<=len(members)<=6,"ERA5-Land NetCDF ZIP member count invalid")
            for m in members:
                require(not m.filename.startswith("/") and
                        ".." not in Path(m.filename).parts and
                        m.file_size<100000000,
                        "unsafe ERA5-Land NetCDF ZIP member")
                with Dataset("inmemory.nc","r",memory=z.read(m)) as ds:load_ds(ds)
    else:
        with Dataset(str(f),"r") as ds:load_ds(ds)
    require(set(fields)=={"t2m","d2m","sp"} and
            all(abs(x[0]-coords[0][0])<1e-5 and
                abs(x[1]-coords[0][1])<1e-5 for x in coords),
            "ERA5-Land full T2m/D2m/SP or consistent gridpoint missing")
    return (expected,fields), "VERIFIED_"+str(f)

def add_grid(c):
    outcomes={}
    for year in (2011,2012):
        frame=c.loc[c.index.str[:4]==str(year)]
        if frame.empty:continue
        grid,status=read_grid(year)
        outcomes[year]=status
        if grid is None:continue
        hour,fields=grid
        # Original native HH is LOCAL STANDARD START, no daylight saving.
        # Output UTC MIDPOINT from BIF offset -6; model DATM clock unapproved.
        local=pd.to_datetime(frame.index,format="%Y%m%d%H%M")
        utc=local+pd.Timedelta(minutes=15)-pd.Timedelta(hours=UTC_OFFSET_H)
        require(utc.min()>=hour[0] and utc.max()<=hour[-1],
                "ERA5-Land local+15min UTC mapping out of downloaded coverage")
        s=hour.asi8.astype(float)/1e9
        tt=utc.asi8.astype(float)/1e9
        t=np.interp(tt,s,fields["t2m"])-273.15
        d=np.interp(tt,s,fields["d2m"])-273.15
        p=np.interp(tt,s,fields["sp"])
        rh=100*sat(d)/sat(t)
        require(np.isfinite([t,d,p,rh]).all() and
                (d<=t+.1).all() and (rh>0).all() and (rh<=100.2).all(),
                "downloaded ERA5-Land T2m D2m SP/RH physics failed")
        c.loc[frame.index,"ERA5Land_T2m_C"]=t
        c.loc[frame.index,"ERA5Land_D2m_C"]=d
        c.loc[frame.index,"ERA5Land_RHwater_pct"]=rh
        c.loc[frame.index,"ERA5Land_SP_Pa"]=p
        c.loc[frame.index,"ERA5Land_grid_RH_at_selected_T_VPD_hPa"]=(
            sat(c.loc[frame.index,"TA_USE"].to_numpy(float))*(1-rh/100))
    return outcomes

def print_audit(c,grid_outcomes):
    print("\nUS-Kon REAL VERIFIED ERA5-LAND SOURCE STATUS (not companion ERA):")
    for y,s in grid_outcomes.items():print(y,s,flush=True)
    print("SITE BIF CLOCK UTC_OFFSET = -6; grid join uses local TIMESTAMP_START + 15m + 6h UTC.")
    print("UTC offset/ERA5-Land representativeness not production-clock-approved.")
    centers=c.loc[HOLD].copy()
    cols=["local_time","TA_F","TA_F_QC","VPD_F","VPD_F_QC",
          "original_both_QC0_measured_RH_derived_pct",
          "TA_ERA","VPD_ERA","companion_ERA_RH_from_T_VPD_pct",
          "ERA5Land_T2m_C","ERA5Land_D2m_C","ERA5Land_RHwater_pct",
          "TA_USE","VPD_USE","QBOT"]
    print("\n===== ALL NINE ACTUAL ORIGINAL TOWER & PAIRED ERA & ERA5-LAND CENTER VALUES =====")
    print(centers[cols].round(3).to_string(index=True,na_rep="—"),flush=True)
    for title,keys in GROUPS:
        ix=pd.to_datetime(keys,format="%Y%m%d%H%M")
        from_key=(ix.min()-pd.Timedelta(hours=2)).strftime("%Y%m%d%H%M")
        to_key=(ix.max()+pd.Timedelta(hours=2)).strftime("%Y%m%d%H%M")
        part=c.loc[(c.index>=from_key)&(c.index<=to_key)].copy()
        use=["local_time","center_HOLD","TA_F","TA_F_QC","VPD_F","VPD_F_QC",
             "original_both_QC0_measured_RH_derived_pct",
             "TA_ERA","VPD_ERA","companion_ERA_RH_from_T_VPD_pct",
             "ERA5Land_T2m_C","ERA5Land_D2m_C","ERA5Land_RHwater_pct",
             "TA_USE","VPD_USE"]
        print("\n===== "+title+" | native source ±2h context =====")
        print(part[use].round(3).to_string(index=True,na_rep="—"),flush=True)
    print("\nOBSERVED QC: QC0 = original observed TA or VPD in its own column;")
    print("                 QC1 = MDS/gapfilled, QC2 = ERA-dependent.")
    print("The original_both_QC0_measured_RH_derived_pct column is")
    print("derived from TWO simultaneously QC0 tower variables;")
    print("original VPD_F and native TA_F have no independent direct RH sensor proof.")
    print("TA_ERA/VPD_ERA are FLUXNET companion ERA, NOT ERA5-Land T2m/D2m.")
    print("Selected Stage14K research VPD_USE/QBOT for all 9 are genuinely NaN.")
    print("US-Kon NINE ORIGINAL TOWER / PAIRED ERA / ERA5-LAND ±2H REVIEW COMPLETE | NO SOURCE/MODEL/SLURM WRITES",flush=True)

def main():
    parser=argparse.ArgumentParser()
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test",action="store_true")
    mode.add_argument("--run",action="store_true")
    args=parser.parse_args()
    self_test()
    if args.self_test:return
    c=original_and_selected()
    g=add_grid(c)
    print_audit(c,g)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("US-Kon NINE SOURCE REVIEW FAIL CLOSED:",e,file=sys.stderr,flush=True)
        raise

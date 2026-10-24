#!/usr/bin/env python3
"""Stage35 | Read-only comparison with measured-coded Howland neighbour temperatures.

Only original source TA_F with TA_F_QC==0 from Ho2/Ho3 is a comparison
anchor. QC0 does not guarantee independent hardware or meteorological
representativeness. Time alignment and Ho1 UTC_OFFSET remain provisional.
Never edit raw data, forcing, NetCDF, DATM, CIME, or Slurm jobs.
"""
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
sys.dont_write_bytecode=True
import numpy as np
import pandas as pd

H=Path.home()
BASE=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S11=BASE/"stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
S19=H/"AmeriFlux_Batch02_stage19_full_dewpoint_audit_20261023T015650Z_8505582f"
S20=H/"AmeriFlux_Batch02_stage20_physical_evidence_review_20261023T021238Z_d7a70a5f"
S21=H/"AmeriFlux_Batch02_stage21_postv5_candidate_decisions_20261023T022056Z_b754ce13"
SITES=("US-Ho1","US-Ho2","US-Ho3")
YEAR_BAD={1998:64,1999:25,2001:230,2003:1,2004:6,2005:60,2007:39}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda:f.read(1048576),b""):h.update(part)
    return h.hexdigest()

def numeric(x):
    a=pd.to_numeric(x,errors="coerce")
    return a.mask((a<=-9990)|~np.isfinite(a))

def es(t):
    with np.errstate(all="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))

def pinned(path,ledger,label):
    path=Path(path).resolve(strict=True)
    matches=[]
    for key,value in ledger.items():
        try:same=Path(key).resolve(strict=True)==path
        except (OSError,RuntimeError):same=False
        if same:matches.append(value)
    if not matches:raise ValueError(label+" missing in Stage08 hash ledger: "+str(path))
    if len(set(matches))!=1:raise ValueError("Conflicting SHA aliases for "+label)
    actual=sha(path)
    if actual!=matches[0]:raise ValueError(label+" SHA256 mismatch: "+str(path))
    return path

def read_tower(path):
    cols=["TIMESTAMP_START","TA_F","TA_F_QC"]
    if not set(cols)<=set(pd.read_csv(path,nrows=0).columns):
        raise ValueError("TA_F/TA_F_QC unavailable in "+str(path))
    a=pd.read_csv(path,usecols=cols,dtype={"TIMESTAMP_START":str})
    a["local"]=pd.to_datetime(a.TIMESTAMP_START.str.strip().str.replace(
        r"\.0$","",regex=True),format="%Y%m%d%H%M")
    a["TA_F"]=numeric(a.TA_F)
    a["TA_F_QC"]=numeric(a.TA_F_QC)
    if a.local.duplicated().any() or not a.local.is_monotonic_increasing:
        raise ValueError("Tower timestamps are not unique/increasing")
    a["measured_T"]=a.TA_F_QC.eq(0)&a.TA_F.notna()
    return a[["local","TA_F","TA_F_QC","measured_T"]]

def metadata(path,ledger,site):
    bifs=sorted(path.parent.glob("*_BIF_*.csv"))
    if not bifs:return ("NO_RELEASE_BIF",None)
    if len(bifs)!=1:return ("AMBIGUOUS_BIF_FILES",None)
    p=bifs[0].resolve(strict=True)
    try:
        pinned(p,ledger,"BIF "+site)
        state="SHA_PINNED_BIF"
    except ValueError:
        state="BIF_NOT_IN_STAGE08_SHA_LEDGER"
    offsets=[]
    with p.open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):
            if str(row.get("VARIABLE","")).strip().upper()=="UTC_OFFSET" and \
               str(row.get("SITE_ID","")).strip() in ("",site):
                try:offsets.append(float(row["DATAVALUE"]))
                except (ValueError,TypeError):pass
    if len(offsets)!=1:return (state+"_UTC_OFFSET_MISSING_OR_AMBIGUOUS",None)
    return (state,offsets[0])

def read_inputs(args):
    for directory in (args.stage11_root,args.stage19_root,args.stage20_root):
        if not (directory/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
            raise ValueError("Scientific HOLD marker missing: "+str(directory))
    m11=json.loads((args.stage11_root/"manifest.json").read_text())
    m19=json.loads((args.stage19_root/"manifest.json").read_text())
    m20=json.loads((args.stage20_root/"manifest.json").read_text())
    m21=json.loads((args.stage21_root/"manifest.json").read_text())
    if (m19.get("n_target_rows"),m19.get("scientifically_approved_rows"))!=(4884,0):
        raise ValueError("Stage19 HOLD identity changed")
    if (m20.get("number_targets"),m20.get("number_approved"))!=(4884,0):
        raise ValueError("Stage20 HOLD identity changed")
    if m19.get("US_Ho1_UTC_offset_status")!="PROVISIONAL_BADM_NOT_VERIFIED":
        raise ValueError("US-Ho1 clock metadata status changed")
    if Path(m20["stage19_root"]).resolve()!=args.stage19_root.resolve() or \
       sha(args.stage19_root/"manifest.json")!=m20["stage19_manifest_sha256"]:
        raise ValueError("Stage19/20 manifests not linked")
    if sha(args.stage20_root/"all_4884_phase_transfer_QC_sensitivity.csv")!=m21["stage20_csv_sha256"]:
        raise ValueError("Stage20 hash differs from Stage21")
    m08=json.loads((Path(m11["source_stage08"])/"exact_input_manifest.json").read_text())
    info={i["site"]:i for i in m08["sites"] if i["site"] in SITES}
    if set(info)!=set(SITES):raise ValueError("Missing a Howland site in Stage08")
    towers={};paths={};clocks={}
    for site in SITES:
        raw=pinned(info[site]["primary"],m08["input_sha256"],site+" original FLUXMET")
        if site=="US-Ho1" and sha(raw)!=m19["original_source_sha256"][site]:
            raise ValueError("Stage19 Ho1 source hash mismatch")
        towers[site]=read_tower(raw)
        clocks[site]=metadata(raw,m08["input_sha256"],site)
        paths[site]=raw
        print("ORIGINAL VERIFIED",site,"rows",len(towers[site]),
              "QC0",int(towers[site].measured_T.sum()),
              "BIF UTC",clocks[site],flush=True)
    a=pd.read_csv(args.stage20_root/"all_4884_phase_transfer_QC_sensitivity.csv",
        usecols=["site","local","retained_TA_C","TA_F_QC",
                 "ERA5_T2M_C","ERA5_Td2M_C","Td_transfer_water_VPD_hPa"],
        parse_dates=["local"])
    if len(a)!=4884 or a.duplicated(["site","local"]).any():
        raise ValueError("Stage20 all-site target contract differs")
    a=a.loc[a.site.eq("US-Ho1")].copy()
    if len(a)!=917:raise ValueError("Ho1 held targets not 917")
    a=a.merge(towers["US-Ho1"][["local","TA_F","TA_F_QC"]],
              on="local",how="left",validate="one_to_one",
              suffixes=("","_source"),indicator=True)
    if not a._merge.eq("both").all():raise ValueError("Missing original Ho1 sample")
    if not np.isclose(a.retained_TA_C,a.TA_F,atol=1e-6,rtol=0,equal_nan=True).all():
        raise ValueError("Stage20 retained TA differs from original")
    if not np.isclose(a.TA_F_QC,a.TA_F_QC_source,atol=0,rtol=0,equal_nan=True).all():
        raise ValueError("Stage20 T source QC differs from original")
    a.drop(columns="_merge",inplace=True)
    if [int(a.TA_F_QC.eq(q).sum()) for q in (0,1,2)]!=[216,1,700]:
        raise ValueError("Stage34 Ho1 QC0/QC1/QC2 counts changed")
    bad=(es(a.retained_TA_C)-es(a.ERA5_Td2M_C)).lt(-.005)
    if not np.allclose(es(a.retained_TA_C)-es(a.ERA5_Td2M_C),
                       a.Td_transfer_water_VPD_hPa,atol=1e-7,rtol=1e-8):
        raise ValueError("Stage20 Td VPD not reproduced")
    a["bad_Td"]=bad
    a["year"]=a.local.dt.year
    if int(bad.sum())!=425 or not a.loc[bad,"TA_F_QC"].eq(2).all():
        raise ValueError("Stage34 425 QC2 baseline not reproduced")
    if a.loc[bad].groupby("year").size().to_dict()!=YEAR_BAD:
        raise ValueError("Stage34 negative-VPD year counts changed")
    return towers,paths,clocks,a

def qc2_runs(t):
    a=t.loc[t.TA_F_QC.eq(2)].copy()
    a["run"]=a.local.diff().ne(pd.Timedelta(minutes=30)).cumsum()
    z=a.groupby("run").agg(start=("local","min"),end=("local","max"),
                           halfhours=("local","size"))
    z["days"]=z.halfhours/48
    return z.sort_values("halfhours",ascending=False).head(12)

def report(towers,paths,clocks,held):
    print("\n"+"="*108)
    print("STAGE35 | HOWLAND NEIGHBOUR QC0 TEMPERATURE CROSS-VALIDATION (READ ONLY)")
    print("="*108)
    print("Ho1 longest continuous QC2 temperature-fill runs:")
    print(qc2_runs(towers["US-Ho1"]).to_string(index=False))
    for site in ("US-Ho2","US-Ho3"):
        t=towers[site]
        join=held.merge(t[["local","TA_F","TA_F_QC","measured_T"]].rename(
            columns={"TA_F":"neighbor_T","TA_F_QC":"neighbor_QC",
                     "measured_T":"neighbor_measured"}),
            on="local",how="left",validate="one_to_one")
        join["neighbor_measured"]=join.neighbor_measured.fillna(False).astype(bool)
        join["group"]=np.where(join.bad_Td,"NEGATIVE_TD","OTHER_HELD")
        print("\n"+"-"*105)
        print(site,"release:",paths[site].name,"UTC evidence:",clocks[site])
        if clocks[site][1] not in (-5.0,None):
            print("WARNING: neighbour site BIF offset inconsistent with provisional Ho1 UTC-5; comparison provisional only")
        rows=[]
        for (year,group),x in join.groupby(["year","group"]):
            v=x.loc[x.neighbor_measured].copy()
            if v.empty:
                rows.append(dict(year=int(year),cohort=group,held=len(x),
                                 neighbor_QC0=0,MAE_vs_FLUXNET=None,MAE_vs_CDS=None,
                                 CDS_closer_0p5C=0,FLUXNET_closer_0p5C=0))
                continue
            e_f=(v.neighbor_T-v.retained_TA_C).abs()
            e_c=(v.neighbor_T-v.ERA5_T2M_C).abs()
            rows.append(dict(year=int(year),cohort=group,held=len(x),neighbor_QC0=len(v),
                             MAE_vs_FLUXNET=round(e_f.mean(),3),
                             MAE_vs_CDS=round(e_c.mean(),3),
                             CDS_closer_0p5C=int((e_c+.5<e_f).sum()),
                             FLUXNET_closer_0p5C=int((e_f+.5<e_c).sum())))
        print("Year-by-year overlap at the 917 Ho1 held timestamps:")
        print(pd.DataFrame(rows).to_string(index=False))
        focus=join.loc[join.bad_Td & join.neighbor_measured]
        print("NEGATIVE Td events with",site,"QC0 measured temperature:",len(focus),"/425")
        if len(focus):
            e_f=(focus.neighbor_T-focus.retained_TA_C).abs()
            e_c=(focus.neighbor_T-focus.ERA5_T2M_C).abs()
            print("Neighbor QC0 MAE vs FLUXNET Ho1 QC2:",round(e_f.mean(),3),
                  "| vs CDS T:",round(e_c.mean(),3))
            print("CDS closer by >0.5C:",int((e_c+.5<e_f).sum()),
                  "FLUXNET closer by >0.5C:",int((e_f+.5<e_c).sum()))
            print("Largest 8 conflicts with QC0 neighbor evidence:")
            print(focus.nsmallest(8,"Td_transfer_water_VPD_hPa")[
                 ["local","retained_TA_C","ERA5_T2M_C","ERA5_Td2M_C",
                  "neighbor_T","Td_transfer_water_VPD_hPa"]
            ].round(3).to_string(index=False))
        annual=t.assign(year=t.local.dt.year).groupby("year").agg(
            native_rows=("local","size"),QC0_measured=("measured_T","sum"))
        print("Neighbour annual observed coverage in selected Ho1 anomaly years:")
        print(annual.reindex(sorted(held.year.unique())).fillna(0).astype(int).to_string())
    print("\nCAUTION: Ho2/Ho3 do NOT cover 1998; Ho3 is a harvested-site microclimate.")
    print("QC0 does not prove independent instrumentation; Ho1 site UTC metadata remains provisional.")
    print("No automatic replacement or source ranking is authorized.")
    print("All 917 Ho1 and 4,884 Batch02 held records remain SCIENTIFIC HOLD.")
    print("NO FILES WRITTEN / NO DATM, CIME, FORCING, ERA5 DOWNLOAD OR SLURM ACTIONS")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--audit",action="store_true")
    p.add_argument("--stage11-root",type=Path,default=S11)
    p.add_argument("--stage19-root",type=Path,default=S19)
    p.add_argument("--stage20-root",type=Path,default=S20)
    p.add_argument("--stage21-root",type=Path,default=S21)
    args=p.parse_args()
    towers,paths,clocks,held=read_inputs(args)
    print("STAGE35 PREFLIGHT PASS | Ho1 917 held / 425 Td negative; 3 original source SHA256 verified")
    if args.check:
        print("CHECK ONLY | no writes/approvals")
        return
    report(towers,paths,clocks,held)

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Reproducible READ-ONLY Batch02 Stage23–31 scientific audits.

Previous Stage23–30 were one-off inline operator scripts. These are maintainable
reimplementations of the same scientific questions, not byte-identical copies.
All original forcing, candidate and model files remain unchanged.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import numpy as np
import pandas as pd

N = {"US-EML": 1327, "US-GLE": 295, "US-Ho1": 917, "US-ICh": 169, "US-ICt": 2176}
BASE = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
ST11 = BASE / "stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
ST19 = Path.home() / "AmeriFlux_Batch02_stage19_full_dewpoint_audit_20261023T015650Z_8505582f"
ST20 = Path.home() / "AmeriFlux_Batch02_stage20_physical_evidence_review_20261023T021238Z_d7a70a5f"

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()

def numeric(x):
    n=pd.to_numeric(x,errors="coerce")
    return n.mask((n<=-9990)|~np.isfinite(n))

def es(t):
    with np.errstate(all="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))

def exceed(t,v):
    sat=es(t)
    with np.errstate(all="ignore"):
        z=np.maximum(np.maximum(v-sat,-v),0)
    return z.where(np.isfinite(t)&np.isfinite(v)&np.isfinite(sat))

def read_source(path,era_only=False):
    head=set(pd.read_csv(path,nrows=0).columns)
    minimum={"TIMESTAMP_START","TA_ERA","VPD_ERA"}
    if not era_only:
        minimum|={"TA_F","TA_F_QC","VPD_F","VPD_F_QC"}
    if not minimum<=head: raise ValueError("Missing source columns: "+str(minimum-head))
    optional=("TA_F_MDS","TA_F_MDS_QC","VPD_F_MDS","VPD_F_MDS_QC","RH")
    cols=sorted(minimum|({*optional}&head))
    a=pd.read_csv(path,usecols=cols,dtype={"TIMESTAMP_START":str})
    a["local"]=pd.to_datetime(a.pop("TIMESTAMP_START").str.strip().str.replace(r"\.0$","",regex=True),format="%Y%m%d%H%M")
    if a.local.duplicated().any() or not a.local.is_monotonic_increasing:
        raise ValueError("Invalid source timestamp ordering: "+str(path))
    for c in a.columns:
        if c!="local":a[c]=numeric(a[c])
    for c in optional:
        if c not in a:a[c]=np.nan
    return a

def qtable(x):
    return x.groupby(["TA_F_QC","VPD_F_QC"],dropna=False).size().to_string()

def episodes(x):
    if x.empty:return "NONE"
    x=x.sort_values("local").copy()
    x["episode"]=x.local.diff().ne(pd.Timedelta(minutes=30)).cumsum()
    return x.groupby("episode").agg(start=("local","min"),end=("local","max"),records=("local","size")).sort_values("records",ascending=False).head(10).to_string(index=False)

def target_join(a,ts,site):
    t=ts.loc[ts.site.eq(site),["local"]]
    x=t.merge(a,on="local",how="left",validate="one_to_one",indicator=True)
    if len(x)!=N[site] or not x._merge.eq("both").all():raise ValueError("Missing target/source join: "+site)
    return x.drop(columns="_merge")

def main(fixed=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage",type=int,choices=list(range(23,32)),default=fixed,required=fixed is None)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--audit",action="store_true")
    p.add_argument("--stage11-root",type=Path,default=ST11)
    p.add_argument("--stage19-root",type=Path,default=ST19)
    p.add_argument("--stage20-root",type=Path,default=ST20)
    args=p.parse_args()
    if fixed is not None and args.stage!=fixed:raise ValueError("Wrapper stage mismatch")
    s11,s19,s20=args.stage11_root,args.stage19_root,args.stage20_root
    for d in (s11,s19):
        if not (d/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():raise ValueError("Missing HOLD marker "+str(d))
    m11=json.loads((s11/"manifest.json").read_text())
    m19=json.loads((s19/"manifest.json").read_text())
    if m19.get("n_target_rows")!=4884 or m19.get("scientifically_approved_rows")!=0:
        raise ValueError("Stage19 HOLD contract changed")
    m08=json.loads((Path(m11["source_stage08"])/"exact_input_manifest.json").read_text())
    source={r["site"]:r for r in m08["sites"] if r["site"] in N}
    if set(source)!=set(N):raise ValueError("Unexpected source sites")
    ts=pd.read_csv(s19/"all_4884_ERA5_RH_VPD_QBOT_sensitivity.csv",parse_dates=["local"])
    if len(ts)!=4884 or ts.duplicated(["site","local"]).any() or ts.groupby("site").size().to_dict()!=N:
        raise ValueError("Stage19 target mismatch")
    s20rows=None
    if args.stage>=29:
        if not (s20/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():raise ValueError("Stage20 HOLD marker missing")
        m20=json.loads((s20/"manifest.json").read_text())
        if m20.get("number_targets")!=4884 or m20.get("number_approved")!=0:
            raise ValueError("Unexpected Stage20 science contract")
        if Path(m20["stage19_root"]).resolve()!=s19.resolve() or sha(s19/"manifest.json")!=m20["stage19_manifest_sha256"]:
            raise ValueError("Stage20 does not match Stage19")
        s20rows=pd.read_csv(s20/"all_4884_phase_transfer_QC_sensitivity.csv",parse_dates=["local"])
        if len(s20rows)!=4884 or s20rows.duplicated(["site","local"]).any():
            raise ValueError("Stage20 table mismatch")
        if set(zip(s20rows.site,s20rows.local))!=set(zip(ts.site,ts.local)):
            raise ValueError("Stage19–20 timestamp difference")
    print("STAGE",args.stage,"READ-ONLY SCIENCE AUDIT",flush=True)
    total=0
    for site,item in source.items():
        original=Path(item["primary"]).resolve(strict=True)
        if sha(original)!=m19["original_source_sha256"].get(site):
            raise ValueError("Raw source checksum changed: "+site)
        if args.stage==28:
            companion=Path(item["era"]).resolve(strict=True)
            if sha(companion)!=m08["input_sha256"].get(str(companion)):
                raise ValueError("Stage08 ERA companion hash changed: "+site)
        if args.check: print("VERIFIED",site,original.name,flush=True);continue
        a=read_source(original)
        x=target_join(a,ts,site)
        outside=~a.local.isin(x.local)
        ef=exceed(a.TA_F,a.VPD_F)
        ee=exceed(a.TA_ERA,a.VPD_ERA)
        f=outside&ef.gt(.005)
        e=outside&ee.gt(.005)
        print("\n==========",site,"==========")
        if args.stage==23:
            print("TARGETS",len(x),"\nQC\n"+qtable(x))
            for name,t,v in [("final","TA_F","VPD_F"),("ERA","TA_ERA","VPD_ERA"),("MDS","TA_F_MDS","VPD_F_MDS")]:
                ex=exceed(x[t],x[v]);print(name,"available",int(ex.notna().sum()),"bad",int(ex.gt(.005).sum()))
            print("QC2 ERA temperature matches",int(((x.TA_F-x.TA_ERA).abs().le(.001)&x.TA_F_QC.eq(2)).sum()))
            print("QC2 ERA VPD matches",int(((x.VPD_F-x.VPD_ERA).abs().le(.001)&x.VPD_F_QC.eq(2)).sum()))
            print("QC1 MDS VPD matches",int(((x.VPD_F-x.VPD_F_MDS).abs().le(.001)&x.VPD_F_QC.eq(1)).sum()))
        elif args.stage==24:
            for label,exc in [("FINAL",ef),("ERA",ee)]:
                for scope,mask in [("all",np.ones(len(a),dtype=bool)),("target",~outside),("outside",outside)]:
                    print(label,scope,"available",int((mask&exc.notna()).sum()),"strict",int((mask&exc.gt(0)).sum()),"bad>.005",int((mask&exc.gt(.005)).sum()))
                t=a.TA_F if label=="FINAL" else a.TA_ERA
                for lo,hi in [(-np.inf,-30),(-30,-20),(-20,-10),(-10,0),(0,np.inf)]:
                    mask=outside&t.ge(lo)&t.lt(hi)&exc.notna()
                    print(label,"T",lo,hi,"available",int(mask.sum()),"bad",int((mask&exc.gt(.005)).sum()))
        elif args.stage==25:
            total+=int((f|e).sum())
            print("FINAL",int(f.sum()),"ERA",int(e.sum()),"BOTH",int((f&e).sum()),"FINAL_ONLY",int((f&~e).sum()),"ERA_ONLY",int((~f&e).sum()))
            print("FINAL>.05",int((outside&ef.gt(.05)).sum()),"ERA>.05",int((outside&ee.gt(.05)).sum()))
            print("final QC pairs\n"+qtable(a.loc[f]))
        elif args.stage in (26,27):
            if site not in ("US-EML","US-Ho1"):continue
            pair=(0,2) if site=="US-Ho1" else (0,1)
            z=a.loc[f&a.TA_F_QC.eq(pair[0])&a.VPD_F_QC.eq(pair[1])].copy()
            print("FOCUS QC",pair,"n",len(z))
            if site=="US-Ho1":
                print("VPD matches ERA",int((z.VPD_F-z.VPD_ERA).abs().le(.001).sum()))
                print("ERA pair valid",int(exceed(z.TA_ERA,z.VPD_ERA).le(.005).sum()))
                print("ERA-minus-measured T median",round((z.TA_ERA-z.TA_F).median(),4))
                ctl=a.loc[outside&a.TA_F_QC.eq(0)&a.VPD_F_QC.eq(2)&ef.le(.005)]
                print("Consistent controls",len(ctl),"median temp gap",(ctl.TA_ERA-ctl.TA_F).median())
            else:
                print("VPD matches MDS",int((z.VPD_F-z.VPD_F_MDS).abs().le(.001).sum()))
                print("MDS pair invalid",int(exceed(z.TA_F_MDS,z.VPD_F_MDS).gt(.005).sum()))
                print("MDS QC",z.VPD_F_MDS_QC.value_counts(dropna=False).to_dict())
            if args.stage==27:
                print("Longest episodes:\n"+episodes(z))
                if site=="US-EML":
                    q=a.loc[f&a.TA_F_QC.eq(0)&a.VPD_F_QC.eq(0)]
                    print("QC0/QC0 exceptions:\n"+q[["local","TA_F","VPD_F"]].to_string(index=False))
        elif args.stage==28:
            companion=read_source(Path(item["era"]).resolve(),era_only=True)
            y=x.merge(companion[["local","TA_ERA","VPD_ERA"]],on="local",validate="one_to_one",suffixes=("_embedded","_companion"))
            if len(y)!=N[site]:raise ValueError("Companion join incomplete: "+site)
            ok=(y.TA_ERA_embedded-y.TA_ERA_companion).abs().le(.001)&(y.VPD_ERA_embedded-y.VPD_ERA_companion).abs().le(.001)
            rh=100*(1-y.VPD_ERA_companion/es(y.TA_ERA_companion))
            held=pd.read_csv(Path(m11["source_stage08"])/site/"forcing/qc_v5"/(site+"_native_RH_resolution_attempts.csv"),parse_dates=["time"])
            held=held.loc[held.decision.ne("CANDIDATE_RAW_RH"),["time","ERA_RH_pct"]].rename(columns={"time":"local"})
            if len(held)!=N[site]:raise ValueError("Stage08 hold count mismatch")
            compare=y[["local"]].assign(rh=rh).merge(held,on="local",validate="one_to_one")
            print("ERA identity",int(ok.sum()),"/",len(y),"RH<-2",int(rh.lt(-2).sum()),"Stage08 RH max discrepancy",float((compare.rh-compare.ERA_RH_pct).abs().max()))
        else:
            b=s20rows.loc[s20rows.site.eq(site)]
            y=x.merge(b,on="local",validate="one_to_one",suffixes=("","_stage20"))
            if args.stage==29:
                cdsrh=y.ERA5_RH_water_pct
                tgap=y.TA_ERA-y.ERA5_T2M_C
                td_vpd=es(y.retained_TA_C)-es(y.ERA5_Td2M_C)
                ice=y.ERA5_ice_RH_above100_subzero.astype(str).str.lower().eq("true")
                print("CDS RH numerically valid",int((cdsrh.gt(0)&cdsrh.le(100.05)).sum()),
                      "FLUXNET inferred RH<-2",int((100*(1-y.VPD_ERA/es(y.TA_ERA))).lt(-2).sum()),
                      "abs T gap >5C",int(tgap.abs().gt(5).sum()),
                      "Td transfer negative VPD",int(td_vpd.lt(-.005).sum()),
                      "ice caution",int(ice.sum()))
            elif args.stage==30:
                z=y.loc[y.TA_F_QC.eq(0)&y.TA_F.notna()&y.ERA5_T2M_C.notna()]
                total+=len(z)
                if len(z):
                    fe=(z.TA_ERA-z.TA_F).abs()
                    ce=(z.ERA5_T2M_C-z.TA_F).abs()
                    print("QC0 anchors",len(z),"FLUXNET T MAE",round(fe.mean(),3),"CDS T MAE",round(ce.mean(),3),
                          "CDS closer",int((ce<fe-.01).sum()),"FLUXNET closer",int((fe<ce-.01).sum()))
                else:print("No independent observed-temperature QC0 at these timestamps")
            elif args.stage==31:
                rh=y.ERA5_RH_water_pct
                t=y.retained_TA_C
                v=y.sensitivity_VPD_hPa
                td=es(t)-es(y.ERA5_Td2M_C)
                ice=y.ERA5_ice_RH_above100_subzero.astype(str).str.lower().eq("true")
                for label,mask in [("MEASURED_T",y.TA_F_QC.eq(0)),("ERA_ORIGIN_T",y.TA_F_QC.eq(2)),("OTHER_T",~y.TA_F_QC.isin([0,2]))]:
                    print(label,"n",int(mask.sum()),"RH-transfer numerically valid",int((mask&rh.gt(0)&rh.le(100.05)&v.ge(-.005)&v.le(es(t)+.005)).sum()),
                          "Td-transfer VPD negative",int((mask&td.lt(-.005)).sum()),"ice caution",int((mask&ice).sum()),
                          "median |RH vs Td transfer VPD|",float((v[mask]-td[mask]).abs().median()) if mask.any() else None)
                if site=="US-Ho1":print("UTC OFFSET PROVISIONAL: ALL CHOICES HOLD")
    if args.stage==25:print("\nDISTINCT OUTSIDE-TARGET UNION",total)
    if args.stage==30:print("\nQC0 ANCHOR TOTAL",total)
    print("\nNO WRITES / NO FORCING APPROVAL / NO SLURM JOBS")

if __name__=="__main__":main()

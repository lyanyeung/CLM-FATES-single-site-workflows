#!/usr/bin/env python3
"""US-MOz Jan09: exact QC-source manual 49HH alternative ONEPASS research scenarios.

Source decisions based on actual Stage14H operator evidence:
  Jan09 07:30–10:00: 6 original TA_F/VPD_F QC1
  Jan09 11:30–12:30: 3 original QC1
  Jan09 13:30–Jan10 09:00: 40 original QC1
  Source QC2 10:30/11:00/13:00 and measured Jan10 09:30 QC0 unchanged.
Create TWO isolated scientifically unapproved research candidates using
(A) original SHA-pinned FLUXNET paired ERA TA_ERA/VPD_ERA
(B) old signed downloaded CDS ERA5-Land t2m/d2m/sp with BIF UTC-6,
    resampled at exact FLUXNET native 30min interval midpoint.
No re-downloading or new scientific approval; all Stage14G 27+1 and
operator-approved Stage13L 40 source values remain identical.
Full 315360 source finite/thermodynamics + exact 49-only source edits,
QC0/QC2 unchanged, all 30min source boundaries and evidence in ledger.
Run --run generates new SEPARATE research versions, never input overwrites;
--check prints all results without writing; no Slurm, DATM, Post-v5.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np,pandas as pd
sys.dont_write_bytecode=True
VER="US-MOz-Jan09-49QC1-two-independent-source-provenance-variants-v1-20261029"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
P=R/"science_trials/US_MOz_14G_QC1_LEFT_EDGE_ONE_HH_SENSITIVITY_20261029T042521Z_dcda1a16"
S07=R/"qcv5_native_trial_20261022T024559Z_36c46e58"
S13L=R/"science_trials/stage13l_US_MOz_40HH_user_approved_CDSEra5Land_20261026T193902Z_95631db8"
EVD=R/"external_evidence/era5land_timeseries/US-MOz/2005_stage13j/ERA5Land_US-MOz_Jan03_Jan11_2005_t2m_d2m_sp.receipt.json"
CSVP="US-MOz_315360_27ERA_plus1QC1bridge_and40approved_RESEARCH.csv"
PR="US_MOz_QC1_bridge_SHA_receipt.json"
SOURCE40="US-MOz_CLM_forcing_2004_2021_STG13L_40HH_REANALYSIS_SHADOW.csv"
COLS="time TBOT QBOT PSRF FSDS FLDS WIND PRECTmms TA_USE VPD_USE".split()
FIRST=pd.Timestamp("2005-01-09 07:30")
LAST=pd.Timestamp("2005-01-10 09:00")
STEP=pd.Timedelta(minutes=30)
EPISODES=[
("JAN09_AM_QC1","2005-01-09 07:30","2005-01-09 10:00",6),
("JAN09_MID_QC1","2005-01-09 11:30","2005-01-09 12:30",3),
("JAN09_PM_TO_JAN10_QC1","2005-01-09 13:30","2005-01-10 09:00",40)]
PROTECTED=pd.DatetimeIndex([
pd.Timestamp("2005-01-09 10:30"),pd.Timestamp("2005-01-09 11:00"),
pd.Timestamp("2005-01-09 13:00"),pd.Timestamp("2005-01-10 09:30")])
def ensure(ok,msg):
    if not bool(ok):raise RuntimeError("US-MOz JAN09 49 SOURCE STOP: "+str(msg))
def must(f):
    f=Path(f);ensure(f.is_file() and not f.is_symlink(),"missing pinned file "+str(f))
    return f
def sha(f):
    h=hashlib.sha256()
    with must(f).open("rb") as g:
        for b in iter(lambda:g.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def es(t):
    t=np.asarray(t,float)
    with np.errstate(over="ignore",invalid="ignore",divide="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))
def esi(t):
    t=np.asarray(t,float)
    with np.errstate(over="ignore",invalid="ignore",divide="ignore"):
        return 6.112*np.exp(22.46*t/(t+272.62))
def qfun(e,pressure):
    return 0.622*100*e/(pressure-0.378*100*e)
def core_times():
    spans=[];group={}
    for label,start,end,n in EPISODES:
        d=pd.date_range(start,end,freq="30min")
        ensure(len(d)==n,"source group cardinality "+label)
        spans.extend(d)
        for dt in d:group[dt]=label
    ix=pd.DatetimeIndex(spans)
    ensure(len(ix)==49 and ix.is_unique and len(set(ix)&set(PROTECTED))==0,
           "49 exact operator source halfhours not distinct")
    return ix,group
def selftest():
    core_times()
    ensure(float(es(-20))>float(esi(-20)) and
      pd.Series(["a",None]).equals(pd.Series(["a",None])),
      "source water and mixed-type exact comparison regression")
    print("US-MOz JAN09 49QC1 TWO-SOURCE SELF-TEST PASS",flush=True)
def signed_inputs():
    pre=json.loads(must(P/PR).read_text())
    lrec=json.loads(must(S13L/"stage13l_MOz_40HH_science_SHA_receipt.json").read_text())
    ensure(pre.get("version")=="US-MOz-QC1-1HH-operator-interpolate-T-e-v1-20261029"
       and pre.get("science_approved") is False
       and pre.get("source_Stage13L")==sha(S13L/SOURCE40),
       "Stage14G bridge receipt/Stage13L ancestor altered")
    for name,dig in pre["output_SHA256"].items():
        ensure(sha(P/name)==dig,"current Stage14G source receipt SHA differs "+name)
    ensure(lrec.get("operator_approved_source_native_events_modified")==40
       and lrec.get("DATM_ready") is False and
       lrec["output_SHA256"][SOURCE40]==sha(S13L/SOURCE40),
       "user-approved Stage13L first40 source receipt changed")
    meta=json.loads(must(S07/"exact_input_manifest.json").read_text())
    sel=[z for z in meta["sites"] if z["site"]=="US-MOz"]
    ensure(len(sel)==1 and int(sel[0]["native_minutes"])==30
      and int(sel[0]["first_year"])==2004
      and int(sel[0]["last_year"])==2021,"original 2004–21 station identity")
    refs={str(Path(p).resolve()):v for p,v in meta["input_sha256"].items()}
    for what in ("primary","era"):
        src=must(sel[0][what])
        ensure(sha(src)==refs.get(str(src.resolve())),"original "+what+" hash differs")
    return sel[0],lrec,pre
def raw_subset(path,cols,keys):
    x=pd.read_csv(must(path),usecols=["TIMESTAMP_START",*cols],
         dtype={"TIMESTAMP_START":str},low_memory=False)
    ensure(x.TIMESTAMP_START.is_unique and
      x.TIMESTAMP_START.str.fullmatch(r"\d{12}").all(),
      "native original timestamp duplicate/invalid")
    x=x.loc[x.TIMESTAMP_START.isin(keys.strftime("%Y%m%d%H%M"))].copy()
    x.index=pd.DatetimeIndex(pd.to_datetime(x.TIMESTAMP_START,format="%Y%m%d%H%M"))
    x.drop(columns="TIMESTAMP_START",inplace=True)
    ensure(len(x)==len(keys) and set(x.index)==set(keys),
         "missing exact source original episode native time")
    return x.loc[keys].apply(pd.to_numeric,errors="coerce")
def load_CDS_full(receipt):
    evidence=json.loads(must(EVD).read_text())
    binary=must(evidence["response_file"])
    ensure(sha(binary)==evidence["response_sha256"]
           and sha(binary)==receipt["CDS_ERA5Land_original_binary_SHA256"],
           "exact originally verified CDS/Stage13L downloaded scientific source changed")
    from netCDF4 import Dataset,num2date
    found={}
    def read(ds):
        mapping={"t2m":("t2m","2m_temperature"),
          "d2m":("d2m","2m_dewpoint_temperature"),
          "sp":("sp","surface_pressure")}
        coords={"latitude":("latitude","lat"),"longitude":("longitude","lon")}
        for kind,keys in coords.items():
            names=[k for k in keys if k in ds.variables]
            ensure(len(names)==1,"ERA5 source coordinate absent "+kind)
            values=np.asarray(ds.variables[names[0]][:]).reshape(-1)
            target=38.7441 if kind=="latitude" else -92.2000
            ensure(len(values)==1 and abs(float(values[0])-target)<0.3,
                   "original CDS site gridpoint location incorrect")
        k=next((k for k in ("valid_time","time") if k in ds.variables),None)
        ensure(k is not None,"CDS CF-time absent")
        tvar=ds.variables[k]
        units=getattr(tvar,"units","")
        ensure("since" in units,"CDS original source time unit missing")
        tv=num2date(tvar[:],units,calendar=getattr(tvar,"calendar","standard"),
            only_use_cftime_datetimes=False,only_use_python_datetimes=True)
        idx=pd.DatetimeIndex(pd.to_datetime([str(z) for z in tv],utc=True)).tz_convert(None)
        for name,aliases in mapping.items():
            found_names=[n for n in aliases if n in ds.variables]
            if not found_names:continue
            ensure(name not in found,"two distinct NetCDF variables named "+name)
            v=ds.variables[found_names[0]]
            raw=np.ma.asarray(v[:]).filled(np.nan)
            ensure(raw.shape[0]==len(idx) and np.prod(raw.shape[1:])==1,
                   "CDS multiple gridpoints or mismatched time axis")
            u=str(getattr(v,"units","")).lower()
            ensure(u in (("k","kelvin") if name!="sp" else ("pa","pascal","pascals")),
                   "CDS original temperature/pressure units changed "+name)
            found[name]=pd.Series(np.asarray(raw,float).reshape(-1),index=idx,name=name)
    if binary.suffix.lower()==".zip":
        with zipfile.ZipFile(binary) as z:
            ensure(z.testzip() is None,"CDS source ZIP CRC error")
            nc=[a for a in z.infolist() if a.filename.lower().endswith(".nc") and not a.is_dir()]
            ensure(1<=len(nc)<=10,"CDS ZIP source NetCDF inventory changed")
            for a in nc:
                ensure(a.file_size<400000000,"source NetCDF unbounded decompression")
                with Dataset("inmem.nc",mode="r",memory=z.read(a)) as ds:read(ds)
    else:
        with Dataset(str(binary)) as ds:read(ds)
    ensure(set(found)=={"t2m","d2m","sp"},"original CDS t2m,d2m,sp incomplete")
    a=pd.DataFrame(found).sort_index()
    ensure(a.index.is_unique and a.index.is_monotonic_increasing and
      np.all(np.diff(a.index.values).astype("timedelta64[m]").astype(float)==60),
      "CDS UTC hourly source clock incomplete")
    ensure((a.t2m.between(180,335)).all() and
      (a.d2m<=a.t2m+.1).all() and (a.sp.between(45000,111000)).all(),
      "original downloaded ERA5 physics/source invalid")
    a["T_C"]=a.t2m-273.15
    a["VPD_hPa"]=es(a.T_C)-es(a.d2m-273.15)
    return a
def map_CDS(grid,target):
    utc=target+pd.Timedelta(minutes=15)+pd.Timedelta(hours=6)
    ensure(utc.min()>=grid.index.min() and utc.max()<=grid.index.max(),
           "CDS native BIF UTC-6 source window not fully covered")
    cols=["T_C","VPD_hPa","sp"]
    combined=grid[cols].reindex(grid.index.union(utc)).sort_index().interpolate(
       method="time",limit_area="inside").reindex(utc)
    ensure(len(combined)==len(target) and np.isfinite(combined.to_numpy(float)).all(),
           "interpolated verified CDS source gap")
    combined.index=target
    return combined
def one_variant(parent,times,groups,raw,era,new_T,new_V,method):
    new=parent.copy(deep=True)
    sitepressure=parent.loc[times,"PSRF"].to_numpy(float)
    water=es(new_T)-new_V
    qbot=qfun(water,sitepressure)
    vld=(np.isfinite(new_T)&np.isfinite(new_V)&np.isfinite(qbot)&
         (water>0)&(new_V>=0)&(new_V<es(new_T))&
         (qbot>0)&(qbot<0.08)&(sitepressure>50000)&(sitepressure<110000))
    ensure(bool(vld.all()),"model T/e/VPD/QBOT invalid "+method+
           " at "+str(times[np.flatnonzero(~vld)].tolist()[:8]))
    for c,value in (("TA_USE",new_T),("VPD_USE",new_V),
                    ("TBOT",new_T+273.15),("QBOT",qbot)):
        new.loc[times,c]=value
    # Full-site original time, original selected surface pressure and all
    # non-meteorology untouched. No other original QC1, QC2, QC0 affected.
    rest=~parent.index.isin(times)
    for c in COLS:
        if c not in ("TA_USE","VPD_USE","TBOT","QBOT"):
            ensure(parent[c].equals(new[c]),"off-scope field altered "+c)
        else:
            ensure(parent.loc[rest,c].equals(new.loc[rest,c]),
                   "off-scope source value changed "+c)
    protect=pd.date_range("2005-01-05 19:00","2005-01-07 09:30",freq="30min")
    ensure(parent.loc[protect,COLS].equals(new.loc[protect,COLS]),
           "prior 27+one-bridge/40 source results not exactly preserved")
    # Every original 2004–2021 native 30min physics check.
    a={c:pd.to_numeric(new[c],errors="raise").to_numpy(float) for c in COLS[1:]}
    ta=a["TA_USE"];v=a["VPD_USE"];p=a["PSRF"]
    e=es(ta)-v
    closed=(np.logical_and.reduce([np.isfinite(x) for x in a.values()])&
      (p>50000)&(p<110000)&(v>=0)&(v<es(ta))&(e>0)&
      np.isclose(a["QBOT"],qfun(e,p),rtol=1e-6,atol=1e-8)&
      np.isclose(a["TBOT"],ta+273.15,rtol=0,atol=1e-8))
    ensure(bool(closed.all()),"315360 VPD/QBOT/TBOT full closure failed "+method)
    edges=[]
    scopes=[(a,b,g) for g,a,b,n in EPISODES]
    critical=[]
    for aa,bb,g in scopes:
        t0=pd.Timestamp(aa);t1=pd.Timestamp(bb)
        for pivot in (t0,t1+STEP):
            prev=pivot-STEP
            if prev not in new.index or pivot not in new.index:continue
            x=new.loc[prev];y=new.loc[pivot]
            difft=abs(float(y.TA_USE)-float(x.TA_USE))
            diffv=abs(float(y.VPD_USE)-float(x.VPD_USE))
            o=parent.loc[prev];p0=parent.loc[pivot]
            edges.append(dict(method=method,episode=g,
              previous_time=str(prev),current_time=str(pivot),
              previous_native_QC_label="QC1_OR_QC2_OR_QC0_BY_ORIGINAL_MANIFEST",
              T_before_abs_C=abs(float(p0.TA_USE)-float(o.TA_USE)),
              T_after_abs_C=difft,VPD_before_abs_hPa=abs(float(p0.VPD_USE)-float(o.VPD_USE)),
              VPD_after_abs_hPa=diffv,after_T_jump_gt4C=difft>4,
              after_VPD_jump_gt4hPa=diffv>4))
            critical.append((difft,diffv))
    edge=pd.DataFrame(edges)
    # Count all 30min jumps in Jan08..Jan10 (including historical Jan08
    # 13:00 / 14:00); do not hide pre-existing unmodified problems.
    j0=new.loc["2005-01-08":"2005-01-10"]
    dp=j0.TA_USE.diff().abs();dv=j0.VPD_USE.diff().abs()
    detail=pd.DataFrame(dict(native_time=[str(t) for t in times],
      source_original_T_QC=raw.TA_F_QC.to_numpy(float),
      source_original_VPD_QC=raw.VPD_F_QC.to_numpy(float),
      original_selected_T_C=parent.loc[times,"TA_USE"].to_numpy(float),
      candidate_T_C=new_T,
      original_selected_VPD_hPa=parent.loc[times,"VPD_USE"].to_numpy(float),
      candidate_VPD_hPa=new_V,
      original_ERA_T_C=era.TA_ERA.to_numpy(float),
      original_ERA_VPD_hPa=era.VPD_ERA.to_numpy(float),
      candidate_QBOT_kgkg=qbot,
      new_water_RH_pct=100*water/es(new_T),
      new_ice_RH_pct=100*water/esi(new_T),
      original_source_QC1_not_measured=True,
      science_approved=False))
    detail["episode"]=detail.native_time.map(
       lambda s:groups[pd.Timestamp(s)])
    stats=dict(source=method,changed_scope_HH=49,
       all_315360_water_QBOT_TBOT_closed=True,
       original_non49_data_identical=True,
       previously_approved_40_untouched=True,
       left_Jan05_27_plus_QC1_bridge_untouched=True,
       Jan09_Jan10_external_joins_T_above4=int(edge.after_T_jump_gt4C.sum()),
       Jan09_Jan10_external_joins_VPD_above4=int(edge.after_VPD_jump_gt4hPa.sum()),
       whole_Jan08_10_T_jumps_gt4=int((dp>4).sum()),
       whole_Jan08_10_VPD_jumps_gt4hPa=int((dv>4).sum()),
       max_outer_T_join_C=float(edge.T_after_abs_C.max()),
       candidate_is_independently_measured_tower=False,
       production_approved=False)
    print("\nUS-MOz JAN09 SOURCE VARIANT",method,flush=True)
    print(json.dumps(stats,indent=2),flush=True)
    print(edge.to_string(index=False),flush=True)
    return new.reset_index(drop=True),detail,edge,stats
def evaluate():
    site,lrec,pre=signed_inputs()
    target,group=core_times()
    before=pd.read_csv(must(P/CSVP),dtype={"time":str},low_memory=False)
    ensure(len(before)==315360 and list(before)==COLS,
       "actual signed Stage14G 315360x10 schema differs")
    ti=pd.to_datetime(before.time,format="%Y-%m-%d %H:%M:%S",errors="raise")
    exp=pd.date_range("2004-01-01","2021-12-31 23:30",freq="30min")
    exp=exp[~((exp.month==2)&(exp.day==29))]
    ensure(len(exp)==315360 and np.array_equal(ti.to_numpy(),exp.to_numpy()),
        "selected 18y source-native NOLEAP timestamp changed")
    before.index=pd.DatetimeIndex(ti)
    raw=raw_subset(site["primary"],["TA_F","VPD_F","TA_F_QC","VPD_F_QC"],
        target.union(PROTECTED).sort_values())
    era=raw_subset(site["era"],["TA_ERA","VPD_ERA"],target)
    all_qc=(raw.loc[target,"TA_F_QC"].eq(1)&raw.loc[target,"VPD_F_QC"].eq(1))
    ensure(bool(all_qc.all()),"one of selected 49 HH is not original QC1/QC1")
    special=raw.loc[PROTECTED,["TA_F_QC","VPD_F_QC"]]
    ensure((special.iloc[:3].eq(2)).all().all() and
       (special.iloc[3].eq(0)).all(),
       "protected three original QC2 + first true Jan10 measured QC0 changed")
    # Original ERA validity cannot be inferred from numeric selected QBOT;
    # verify the real paired native source T and VPD.
    ce=era.TA_ERA.to_numpy(float);cv=era.VPD_ERA.to_numpy(float)
    ensure(np.isfinite(ce).all() and np.isfinite(cv).all() and
           (cv>=0).all() and (cv<es(ce)).all(),
           "original FLUXNET paired ERA has invalid RH at one of the 49 QC1 HH")
    gr=map_CDS(load_CDS_full(lrec),target)
    gt=gr.T_C.to_numpy(float);gv=gr.VPD_hPa.to_numpy(float)
    # Independent (but both reanalysis-linked) ERA source comparison; NO
    # automatic preference for the variant with smoother numeric edges.
    comp=pd.DataFrame({"native_time":[str(x) for x in target],
      "original_FLUXNET_companion_T_C":ce,
      "original_FLUXNET_companion_VPD_hPa":cv,
      "CDS_ERA5Land_T_C":gt,"CDS_ERA5Land_VPD_hPa":gv,
      "abs_T_product_disagreement_C":np.abs(gt-ce),
      "abs_VPD_product_disagreement_hPa":np.abs(gv-cv),
      "scientific_independent_validation":False})
    variants={}
    for method,ct,cvp in [
      ("FLUXNET_COMPANION_ERA",ce,cv),
      ("CDS_ERA5LAND_FIXED_BIF_UTC_MINUS6",gt,gv)]:
        variants[method]=one_variant(before,target,group,raw.loc[target],era,ct,cvp,method)
    print("\nUS-MOz COMPLETE 49HH ORIGINAL T QC1 VPD QC1 | 3 original QC2 and true Jan10 QC0 preserved")
    print("US-MOz CROSS-PRODUCT RAW ERA-vs-CDS DISAGREEMENT SUMMARY")
    print(comp[["abs_T_product_disagreement_C",
                "abs_VPD_product_disagreement_hPa"]].describe().to_string(),flush=True)
    print("US-MOz IMPORTANT: 2 research candidates NOT measured truth; original and existing approved source unchanged",flush=True)
    summary=dict(version=VER,site="US-MOz",target_HH=len(target),
      source_parent_Stage14G_sha256=sha(P/CSVP),
      source_original_tower_sha256=sha(site["primary"]),
      source_original_FLUXNET_ERA_sha256=sha(site["era"]),
      source_verified_CDS_receipt_sha256=sha(EVD),
      source_Stage13L_parent_sha256=sha(S13L/SOURCE40),
      three_original_QC2_and_one_QC0_preserved=True,
      selected_49_both_raw_T_VPD_QC1=True,
      approved_40_untouched=True,
      preexisting_27_plus_1_untouched=True,
      new_production_or_SCIE_approvals=0,
      variations={k:v[3] for k,v in variants.items()},
      source_T_C_product_discrepancy_max=float(comp.abs_T_product_disagreement_C.max()),
      source_VPD_hPa_product_discrepancy_max=float(comp.abs_VPD_product_disagreement_hPa.max()),
      current_user_decision="Two separately versioned numerical source sensitivities ONLY",
      Postv5_DATM_AD400_Slurm=False)
    return variants,comp,summary
def main():
    p=argparse.ArgumentParser()
    o=p.add_mutually_exclusive_group(required=True)
    for name in ("self-test","check","run"):o.add_argument("--"+name,action="store_true")
    args=p.parse_args()
    selftest()
    if args.self_test:return
    variants,comp,summary=evaluate()
    if args.check:
        print("US-MOz JAN09 TWO SCENARIOS CHECK PASS | no output or input files changed",flush=True)
        return
    out=R/"science_trials"/("US_MOz_Jan09_49QC1_TWO_REANALYSIS_RESEARCH_ONLY_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    artifacts={"US_MOz_49HH_CDS_ERA5Land_vs_FLUXNET_companion_SOURCE.csv":comp}
    for k,(df,detail,edge,stats) in variants.items():
        artifacts[k+"_315360_FULL_RESEARCH_ONLY_NOT_DATM.csv"]=df
        artifacts[k+"_49_QC1_EXACT_CHANGE_LEDGER.csv"]=detail
        artifacts[k+"_SIX_NATIVE_ORIGINAL_BOUNDARIES.csv"]=edge
    outputs={}
    for name,d in artifacts.items():
        d.to_csv(out/name,index=False,float_format="%.17g")
        outputs[name]=sha(out/name)
    for k in variants:
        f=out/(k+"_315360_FULL_RESEARCH_ONLY_NOT_DATM.csv")
        z=pd.read_csv(must(f))
        ensure(len(z)==315360 and list(z)==COLS and not z[COLS[1:]].isna().any().any(),
           "serialized research candidate lost native 315360x10 source "+k)
    (out/"NOT_APPROVED_FOR_POSTV5_DATM_AD400").write_text(
        "These two scenarios reconstruct only 49 original QC1/QC1 Jan09-Jan10 slots, "
        "using alternate ERA sources with BIF UTC-6 and original site pressure. "
        "Neither ERA is independent tower truth. Do not mass replace other QC1 "
        "source hours or modify 3 original QC2, Jan10 measured QC0, the previously "
        "approved 40, or older 27+1 sensitivity. Edge continuity is not an "
        "observational science approval. No DATM/AD400/Slurm.\n")
    outputs["NOT_APPROVED_FOR_POSTV5_DATM_AD400"]=sha(out/"NOT_APPROVED_FOR_POSTV5_DATM_AD400")
    (out/"US_MOz_49QC1_two_methods_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    outputs["US_MOz_49QC1_two_methods_summary.json"]=sha(out/"US_MOz_49QC1_two_methods_summary.json")
    (out/"US_MOz_49QC1_SHA_receipt.json").write_text(json.dumps({
      "version":VER,"source_Stage14G_sha256":summary["source_parent_Stage14G_sha256"],
      "output_SHA256":outputs,"production_approval":False},indent=2)+"\n")
    print("US-MOz 49QC1 TWO-SOURCE ISOLATED RESEARCH DIR:",out,flush=True)
    print("US-MOz JAN09 TWO ALTERNATIVE SCIENCE SENSITIVITIES DONE | OLD 27+1+40 UNCHANGED | NO SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as e:
        print("US-MOz 49QC1 TWO-SOURCE FAIL CLOSED:",e,file=sys.stderr,flush=True)
        raise

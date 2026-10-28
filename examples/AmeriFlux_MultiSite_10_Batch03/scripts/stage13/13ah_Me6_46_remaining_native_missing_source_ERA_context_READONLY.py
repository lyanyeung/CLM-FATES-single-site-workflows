#!/usr/bin/env python3
"""Stage13AH: US-Me6 *all 46* missing VPD/QBOT native rows after successful AF.

Read entire SHA-verified original FLUXMET tower + same-release companion ERA,
latest exact AF research shadow, and actual Stage13AG group report. Show
original native time, tower T/VPD/QC, paired ERA T/VPD/RH, current selected,
adjacent ±1h source context and ±2h complete detail. Partition 17 held-run
HH vs 29 outside; classify missing clusters and conditional isolated repair
possibilities. *Never apply interpolation, era methods or source changes.*
"""
import argparse,hashlib,importlib.util,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VER="batch03-stage13ah-v2-20261028-Me6-all46-noleap-safe-source-context"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
HERE=Path(__file__).resolve().parent
VALIDATE=HERE/"13_validation_Me6_six_run_repair_candidates.py"
VALIDATE_BLOB="de62b7f6d1001fafa923163e565b2945bb2a8816"
AG=ROOT/"reports/stage13ag_Me6_5run_QC0_ERA_daily_before_after_REVIEW_ONLY_20261028T191352Z_e6cec200"
AG_REC="stage13ag_science_readonly_sha_receipt.json"
AG_SUM="stage13ag_readonly_group_science_summary.json"
AG_EXPECT={
 "five_run_group_source_QC0_and_ERA_method_HOLD.csv",
 "five_run_daily_source_tower_vs_ERA_context.csv",
 "five_run_start_end_2h_tower_ERA_original_boundaries.csv",
 "14_original_source_T_discrepancies_1h_before_after.csv",
 AG_SUM,"NO_SOURCE_METHOD_APPROVAL_OR_FORCING_MODEL_SUBMISSION"}
AF=ROOT/"science_trials/stage13af_Me6_20151112_1330_originalQC1_single_spike_RESEARCH_ONLY_20261028T172815Z_c5ca5d8d"
AF_CSV="US-Me6_STAGE13AF_20151112_1330_Run14_oneQC1_LINEAR_RESEARCH_ONLY_NOLEAP.csv"
AF_REC="stage13af_one_QC1_science_shadow_SHA_receipt.json"
AF_SHA="3df2fd258157f2a70d8d0b6dd0de865980bf6505c4da0e6a58e6058e2610b1b0"
AD_SHA="8ea065e690b35cdbf2722c436211ab43627dfdcb2e202f159be9d22a7396241b"
S_SHA="02e80edf89af35874a5cfb2c134e42fbe771b9b2ccc0899bfc4fe19bc2e18565"
H=pd.Timedelta(minutes=30)
COUNTS={14:469,15:95,16:30,17:137,18:47}
APPROVED={pd.Timestamp("2017-07-04 12:00"),pd.Timestamp("2015-11-12 13:30")} | \
         set(pd.date_range("2015-09-26 05:00",periods=4,freq="30min")) | \
         set(pd.date_range("2017-07-04 06:00",periods=5,freq="30min"))
def need(x,msg):
    if not bool(x):raise RuntimeError("STAGE13AH ORIGINAL SOURCE HOLD: "+str(msg))
def must(path):
    p=Path(path);need(p.is_file() and not p.is_symlink(),"file missing/symlink "+str(p));return p
def sha(path):
    h=hashlib.sha256()
    with must(path).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def gitblob(path):
    b=must(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def es(t):
    t=float(t)
    return 6.112*np.exp(17.67*t/(t+243.5)) if np.isfinite(t) else np.nan
def q_calc(v,t,p):
    v,t,p=float(v),float(t),float(p)
    sv=es(t)
    e=(sv-v)*100
    d=p-.378*e
    q=.622*e/d if np.isfinite(d) and d!=0 else np.nan
    good=bool(np.isfinite([v,t,p,sv,e,q]).all() and 50000<p<110000
              and 0<v<sv and 0<q<.08 and d>0)
    return q,good
def ts_index(series):
    z=series.astype(str).str.replace(r"[^0-9]","",regex=True).str[:12]
    x=pd.DatetimeIndex(pd.to_datetime(z,format="%Y%m%d%H%M",errors="raise"))
    need(x.is_unique and x.is_monotonic_increasing,"source time duplicates/nonmonotonic")
    return x
def selftest():
    need(sum(COUNTS.values())==778 and len(APPROVED)==11,
         "exact 778 original held QC1 and 11 separate existing protected HH")
    need(q_calc(7.513,5.54,95000)[1] and not q_calc(-1,5.54,95000)[1],
         "vapour-pressure at preserved tower temperature")
    pairs=[pd.Timestamp("2017-07-03 01:00"),pd.Timestamp("2017-07-03 01:30"),
           pd.Timestamp("2017-07-03 02:30")]
    need(pairs[1]-pairs[0]==H and pairs[2]-pairs[1]==2*H,
         "single vs multi-missing native adjacency")
    print("STAGE13AH SELF-TEST PASS | 46 source gaps, 17 inside and 29 outside held runs, protected 11 original HH; NO WRITES",flush=True)
def read_confirmed():
    need(gitblob(VALIDATE)==VALIDATE_BLOB,"original SHA-pinned six-run reader changed")
    spec=importlib.util.spec_from_file_location("me6_13ah_verified_upstream",must(VALIDATE))
    need(spec is not None and spec.loader is not None,"source reader module absent")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    need(mod.VER=="batch03-stage13_validation-v1-20261027-Me6-six-run-validated-repair-candidates",
         "upstream actual same-release source version changed")
    raw_small,selected,runs,provenance=mod.load_inputs()
    need(provenance.get("Stage13s_input_SHA256")==S_SHA,
         "old source Stage13S SHA changed")
    src,_,_,_=mod.predecessor().signed()
    need(sha(src["primary"])==provenance.get("tower_SHA256") and
         sha(src["era"])==provenance.get("ERA_SHA256"),
         "actual original tower and paired ERA source bytes changed")
    ar=json.loads(must(AG/AG_REC).read_text())
    need(ar.get("version")=="batch03-stage13ag-v1-20261028-Me6-five-run-group-context-after-AF"
         and ar.get("site")=="US-Me6"
         and ar.get("source_or_forcing_written") is False
         and ar.get("new_operator_approval") is False
         and set(ar.get("outputs_SHA256",{}))==AG_EXPECT,
         "actual Stage13AG original source group receipt changed")
    for name,digest in ar["outputs_SHA256"].items():
        need("/" not in name and "\\" not in name and sha(AG/name)==digest,
             "actual Stage13AG output SHA mismatch "+name)
    ag=json.loads(must(AG/AG_SUM).read_text())
    need(ag.get("site")=="US-Me6" and
         ag.get("full_site_latest_stage13af_missing_by_model_variable")==
            {"VPD_USE":46,"QBOT":46,"TA_USE":0,"PSRF":0} and
         ag.get("current_research_shadow_sha256")==AF_SHA and
         ag.get("source_halfhours")==778 and
         ag.get("full_run_method_approval") is False and
         ag.get("forcings_written") is False,
         "verified 46 missing / 778 held / no science approval changed")
    afr=json.loads(must(AF/AF_REC).read_text())
    need(afr.get("site")=="US-Me6" and
         afr.get("original_Stage13AD_SHA256")==AD_SHA and
         afr.get("separate_research_only_shadow") is True and
         afr.get("source_or_production_forcing_written") is False and
         afr.get("outputs_SHA256",{}).get(AF_CSV)==AF_SHA and
         sha(AF/AF_CSV)==AF_SHA,
         "current approved Stage13AF source SHA/immutable scope drift")
    latest=pd.read_csv(must(AF/AF_CSV),dtype={"time":str},low_memory=False)
    latest.index=ts_index(latest.time)
    need(len(latest)==280320 and not
         ((latest.index.month==2)&(latest.index.day==29)).any(),
         "exact 16-year NOLEAP source site chronology changed")
    # Original FLUXMET holds a complete calendar with leap days.
    # Drop only Feb 29 for the model's existing fixed NOLEAP site key.
    tcols=["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"]
    ecols=["TIMESTAMP_START","TA_ERA","VPD_ERA"]
    tower=pd.read_csv(must(src["primary"]),usecols=tcols,
                      dtype={"TIMESTAMP_START":str},low_memory=False)
    era=pd.read_csv(must(src["era"]),usecols=ecols,
                    dtype={"TIMESTAMP_START":str},low_memory=False)
    need(len(tower)==len(era) and
         tower.TIMESTAMP_START.tolist()==era.TIMESTAMP_START.tolist(),
         "original full 2009–2024 native tower and same-release ERA time mismatch")
    raw=tower.merge(era,on="TIMESTAMP_START",validate="one_to_one")
    raw.index=ts_index(raw.TIMESTAMP_START)
    keep=~((raw.index.month==2)&(raw.index.day==29))
    raw=raw.loc[keep].copy()
    for col in tcols[1:]+ecols[1:]:
        raw[col]=pd.to_numeric(raw[col],errors="coerce")
        raw.loc[raw[col]<=-9990,col]=np.nan
    need(raw.index.equals(latest.index),
         "original source 16-year clock does not exactly match AF NOLEAP chronology")
    # Independently cross-check original 2015/2017 upstream 35040 keys and values
    need(raw_small.index.isin(raw.index).all() and
         len(raw_small)==35040 and
         np.allclose(raw.loc[raw_small.index,["TA_F","VPD_F","TA_ERA","VPD_ERA"]],
                     raw_small[["TA_F","VPD_F","TA_ERA","VPD_ERA"]],
                     equal_nan=True,atol=1e-10,rtol=0),
         "original full source and independently audited 2015/17 source disagree")
    return raw,latest,runs,provenance
def analyze():
    raw,site,runs,prov=read_confirmed()
    for col in ("TA_USE","PSRF"):
        need(np.isfinite(site[col].to_numpy(float)).all(),
             "previously verified full site tower temp or pressure now missing")
    v=pd.to_numeric(site.VPD_USE,errors="raise")
    q=pd.to_numeric(site.QBOT,errors="raise")
    missing=~np.isfinite(v.to_numpy(float))
    need(np.array_equal(missing,~np.isfinite(q.to_numpy(float))) and
         missing.sum()==46,"full 46 VPD/QBOT matched native missing identities changed")
    miss=site.index[missing]
    need(not any(t in APPROVED for t in miss),
         "previous source science approved original center became missing")
    byrun={}
    inside=set()
    for gid,n in COUNTS.items():
        r=runs.loc[runs.source_full_run_id.eq(gid)]
        need(len(r)==1,"original run metadata changed "+str(gid))
        row=r.iloc[0]
        start=pd.Timestamp(row.source_original_QC1_start)
        end=pd.Timestamp(row.source_original_QC1_end)
        stamps=pd.date_range(start,end,freq="30min")
        need(len(stamps)==n and stamps.isin(raw.index).all()
             and (raw.loc[stamps,"VPD_F_QC"]==1).all(),
             "original exact source QC1 run chronology/QC changed")
        byrun[gid]=stamps
        inside.update(set(stamps)&set(miss))
    need(len(inside)==17 and len(miss.difference(pd.DatetimeIndex(sorted(inside))))==29,
         "actual 46 site holes must partition 17 held run / 29 outside")
    # Consecutive missing source record runs, not untrusted ERA candidate jumps.
    groups=[];idx_to_gap={}
    for k,t in enumerate(miss):
        if k==0 or t-miss[k-1]!=H:groups.append([])
        groups[-1].append(t)
    for gapid,grp in enumerate(groups,1):
        for t in grp:idx_to_gap[t]=(gapid,len(grp),grp[0],grp[-1])
    def runname(t):
        for gid,stamps in byrun.items():
            if t>=stamps[0] and t<=stamps[-1]:return str(gid)
        return "OUTSIDE_14_18"
    events=[];neighbors=[]
    cols=["TA_F","TA_F_QC","VPD_F","VPD_F_QC","TA_ERA","VPD_ERA"]
    for t in miss:
        gapid,ng,start,end=idx_to_gap[t]
        src=raw.loc[t];now=site.loc[t]
        isinside=(t in inside)
        around=[t+k*H for k in range(-4,5)]
        context_complete=all(a in raw.index for a in around)
        # At 2009/2024 edges or a fixed NOLEAP February boundary,
        # record missing neighbor provenance as NaN: never invent an
        # original source observation and never interpolate across it.
        prev=raw.reindex([t-H]).iloc[0];nxt=raw.reindex([t+H]).iloc[0]
        prev_sel=site.reindex([t-H]).iloc[0]
        next_sel=site.reindex([t+H]).iloc[0]
        zt=float(now.TA_USE);pp=float(now.PSRF)
        er_t=float(src.TA_ERA);er_v=float(src.VPD_ERA)
        rh_era=100*(1-er_v/es(er_t)) if np.isfinite([er_t,er_v]).all() else np.nan
        raw_era_v=es(zt)*(1-rh_era/100) if np.isfinite(rh_era) else np.nan
        era_q,era_phys=q_calc(raw_era_v,zt,pp) if np.isfinite(raw_era_v) else (np.nan,False)
        original_t_ok=(np.isfinite([zt,float(src.TA_F)]).all() and
                       np.isfinite(src.TA_F_QC) and float(src.TA_F_QC)==0 and abs(zt-float(src.TA_F))<1e-7)
        donor_ok=(np.isfinite([er_t,er_v,rh_era]).all() and
                  0<rh_era<100 and abs(zt-er_t)<=8 and original_t_ok
                  and era_phys and (np.isfinite(src.VPD_F_QC) and float(src.VPD_F_QC)!=0))
        pv=float(prev.VPD_F);nv=float(nxt.VPD_F)
        qcs=[float(prev.VPD_F_QC),float(src.VPD_F_QC),float(nxt.VPD_F_QC)]
        selection=[float(prev_sel.VPD_USE),float(next_sel.VPD_USE)]
        good_neighbors=(all(np.isfinite([pv,nv,*selection]))
          and all(float(a) in (0,1) for a in (qcs[0],qcs[2]))
          and np.isclose(pv,selection[0],atol=1e-7,rtol=0)
          and np.isclose(nv,selection[1],atol=1e-7,rtol=0)
          and all(q_calc(vv,float(tmp.TA_USE),float(tmp.PSRF))[1]
                  for vv,tmp in ((pv,prev_sel),(nv,next_sel))))
        context5=[t+k*H for k in (-2,-1,0,1,2)]
        window=raw.reindex(context5)
        tw=site.reindex(context5)
        t_tower=window.TA_F.to_numpy(float)
        t_qc=window.TA_F_QC.to_numpy(float)
        trust_t=(np.isfinite(t_tower).all() and np.all(t_qc==0) and
              np.allclose(tw.TA_USE.to_numpy(float),t_tower,atol=1e-7,rtol=0)
              and np.max(abs(np.diff(t_tower)))<=3.5)
        outer=np.array([float(window.VPD_F.iloc[j]) for j in (0,1,3,4)])
        pattern=(np.isfinite(outer).all() and
          abs(outer[1]-outer[0])<=2 and abs(outer[3]-outer[2])<=2 and
          abs(outer[2]-outer[1])<=2)
        interp=(pv+nv)/2 if good_neighbors else np.nan
        iq,iphys=q_calc(interp,zt,pp) if np.isfinite(interp) else (np.nan,False)
        adjacent_missing=(ng!=1 or
               not np.isfinite([prev_sel.VPD_USE,next_sel.VPD_USE]).all())
        local_steps=np.max(abs(np.diff([outer[0],outer[1],interp,outer[2],outer[3]]))) if (
             np.isfinite(interp) and np.isfinite(outer).all()) else np.nan
        isolated=(not adjacent_missing and good_neighbors and trust_t and pattern and
                  iphys and np.isfinite(local_steps) and local_steps<=4 and
                  (np.isfinite(src.VPD_F_QC) and float(src.VPD_F_QC) in (1,2)))
        era_steps=max(abs(raw_era_v-selection[0]),abs(raw_era_v-selection[1])) if (
                   donor_ok and np.isfinite(selection).all()) else np.nan
        era_screen=bool(donor_ok and not adjacent_missing and
                        np.isfinite(era_steps) and era_steps<=4)
        if not context_complete:status="HOLD_SOURCE_CHRONOLOGY_EDGE_NO_IMMEDIATE_CONTEXT"
        elif np.isfinite(src.VPD_F_QC) and float(src.VPD_F_QC)==0:status="HOLD_PROTECT_ORIGINAL_VPD_QC0_NO_REPLACEMENT"
        elif adjacent_missing:status="HOLD_MULTI_OR_NEIGHBOR_MISSING_SOURCE"
        elif isolated:status="REVIEW_ISOLATED_LINEAR_ONLY_NO_APPROVAL"
        elif era_screen:status="REVIEW_COMPANION_ERA_RH_ONLY_NO_APPROVAL"
        elif not original_t_ok:status="HOLD_ORIGINAL_T_QC_OR_SITE_MISMATCH"
        elif not donor_ok:status="HOLD_SOURCE_ERA_RH_T_OR_PHYSICS"
        else:status="HOLD_NATIVE_VPD_CONTINUITY_OR_QC"
        events.append({
          "native_time":str(t),"run_scope":runname(t),"is_one_of_17_within_five_runs":isinside,
          "missing_cluster_id":gapid,"missing_cluster_native_HH":ng,
          "full_original_plusminus_2h_source_context":context_complete,
          "source_tower_TA_F_C":float(src.TA_F),"source_tower_TA_F_QC":float(src.TA_F_QC),
          "source_tower_VPD_F_hPa":float(src.VPD_F),
          "source_tower_VPD_F_QC":float(src.VPD_F_QC),
          "source_companion_ERA_TA_C":er_t,"source_companion_ERA_VPD_hPa":er_v,
          "source_companion_ERA_RH_water_pct":rh_era,
          "current_site_TA_USE_C":zt,"current_site_PSRF_Pa":pp,
          "before_30min_tower_VPD_hPa":pv,"before_30min_tower_VPD_QC":qcs[0],
          "before_30min_ERA_VPD_hPa":float(prev.VPD_ERA),
          "before_30min_current_selected_VPD_hPa":selection[0],
          "after_30min_tower_VPD_hPa":nv,"after_30min_tower_VPD_QC":qcs[2],
          "after_30min_ERA_VPD_hPa":float(nxt.VPD_ERA),
          "after_30min_current_selected_VPD_hPa":selection[1],
          "hypothetical_isolated_linear_VPD_hPa":interp,
          "hypothetical_isolated_linear_QBOT_kgkg":iq,
          "hypothetical_companion_ERA_RH_at_tower_T_VPD_hPa":raw_era_v,
          "hypothetical_companion_ERA_RH_at_tower_T_QBOT_kgkg":era_q,
          "hypothetical_ERA_native_max_edge_hPa":era_steps,
          "original_tower_T_all_five_measured_QC0_and_stable":trust_t,
          "original_VPD_neighbor_qc0_or_qc1_not_always_measured_QC0":good_neighbors,
          "hypothetical_single_center_linear_gate_PASS":isolated,
          "hypothetical_companion_ERA_gate_PASS_only_numeric":era_screen,
          "science_review_category":status,
          "operator_new_approval":False})
        for i,a in enumerate(around):
            z=raw.reindex([a]).iloc[0];y=site.reindex([a]).iloc[0]
            neighbors.append({
              "missing_center":str(t),"run_scope":runname(t),
              "missing_cluster_id":gapid,"center_native_time":str(t),
              "neighbor_native_time":str(a),"relative_30min_steps":i-4,
              "original_source_time_exists":a in raw.index,
              "tower_TA_F_C":float(z.TA_F),"tower_TA_F_QC":float(z.TA_F_QC),
              "tower_VPD_F_hPa":float(z.VPD_F),"tower_VPD_F_QC":float(z.VPD_F_QC),
              "paired_source_ERA_TA_C":float(z.TA_ERA),
              "paired_source_ERA_VPD_hPa":float(z.VPD_ERA),
              "site_current_TA_USE_C":float(y.TA_USE),
              "site_current_VPD_USE_hPa":float(y.VPD_USE),
              "site_current_QBOT_kgkg":float(y.QBOT),
              "site_current_PSRF_Pa":float(y.PSRF),
              "originally_approved_2015_or_2017_record":a in APPROVED})
    tab=pd.DataFrame(events).sort_values("native_time")
    ctx=pd.DataFrame(neighbors)
    need(len(tab)==46 and tab.native_time.nunique()==46 and len(ctx)==414 and
         tab.is_one_of_17_within_five_runs.sum()==17 and
         (~tab.is_one_of_17_within_five_runs).sum()==29,
         "exact 46 native source rows and ±2h nine-point contexts incomplete")
    summary=tab.groupby(["run_scope","science_review_category"],dropna=False).size().reset_index(name="count")
    clusters=tab.groupby("missing_cluster_id").agg(
         first_native_time=("native_time","min"),
         last_native_time=("native_time","max"),
         length_HH=("native_time","size"),
         run_scope=("run_scope",lambda s:";".join(sorted(set(s))))
         ).reset_index()
    science={
      "version":VER,"site":"US-Me6","latest_AF_research_shadow_SHA256":AF_SHA,
      "Stage13AG_actual_science_receipt_SHA256":sha(AG/AG_REC),
      "original_unmodified_stage13s_SHA256":S_SHA,
      "last_census_stage13af_vpd_missing_HH":46,
      "within_five_held_original_QC1_runs_missing_HH":17,
      "outside_five_held_original_QC1_runs_missing_HH":29,
      "missing_clusters":len(clusters),
      "isolated_linear_only_research_review_count":
          int(tab.hypothetical_single_center_linear_gate_PASS.sum()),
      "companion_ERA_RH_only_numeric_review_count":
          int(tab.hypothetical_companion_ERA_gate_PASS_only_numeric.sum()),
      "QC0_source_tower_measurements_not_overwritten":True,
      "no_companion_ERA_is_independent_ERA5_land_claim":True,
      "no_automatic_user_science_approval":True,
      "original_files_modified":False,"research_shadow_modified":False,
      "Postv5":False,"DATM":False,"AD400":False,"Slurm":False}
    print("STAGE13AH ALL 46 EXACT SOURCE-NATIVE MISSING HH / ORIGINAL TOWER + COMPANION ERA / +/- 30 MIN",flush=True)
    chosen=["native_time","run_scope","missing_cluster_native_HH",
      "source_tower_TA_F_C","source_tower_TA_F_QC",
      "before_30min_tower_VPD_hPa","before_30min_tower_VPD_QC",
      "source_tower_VPD_F_hPa","source_tower_VPD_F_QC",
      "after_30min_tower_VPD_hPa","after_30min_tower_VPD_QC",
      "source_companion_ERA_VPD_hPa","hypothetical_isolated_linear_VPD_hPa",
      "hypothetical_companion_ERA_RH_at_tower_T_VPD_hPa","science_review_category"]
    print(tab[chosen].to_string(index=False),flush=True)
    print("STAGE13AH MISSING CLUSTER AND REVIEW GATE GROUPS",flush=True)
    print(clusters.to_string(index=False),flush=True)
    print(summary.to_string(index=False),flush=True)
    print("STAGE13AH SOURCE/APPROVAL SUMMARY",json.dumps(science,indent=2),flush=True)
    return tab,ctx,clusters,summary,science
def main():
    p=argparse.ArgumentParser()
    group=p.add_mutually_exclusive_group(required=True)
    for name in ("self-test","check","run"):group.add_argument("--"+name,action="store_true")
    args=p.parse_args()
    selftest()
    if args.self_test:return
    table,ctx,clusters,groups,science=analyze()
    if args.check:
        print("STAGE13AH 46 SOURCE-NATIVE ROWS READONLY CHECK PASS | ZERO WRITES",flush=True)
        return
    out=ROOT/"reports"/("stage13ah_US-Me6_46_native_humidity_missing_tower_ERA_context_READONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    data={
      "ALL_46_original_tower_ERA_current_VPD_QBOT_no_approval.csv":table,
      "ALL_46_original_before_after_2h_each_ERA_and_tower.csv":ctx,
      "46_missing_contiguous_original_native_clusters.csv":clusters,
      "46_missing_source_run_and_science_method_review_counts.csv":groups}
    for n,d in data.items():d.to_csv(out/n,index=False,float_format="%.17g")
    name="stage13ah_exact_46_source_science_summary.json"
    marker="NO_NEW_OPERATOR_APPROVAL_NO_SOURCE_OR_FORCING_MODEL_WRITES"
    (out/name).write_text(json.dumps(science,indent=2)+"\n")
    (out/marker).write_text("Signed original source and AF research shadow ONLY."
      " All numerical candidates are diagnostic, not approved corrections."
      " No source, research shadow, model, DATM or Slurm jobs changed.\n")
    receipt={"version":VER,"site":"US-Me6","new_method_approved":False,
        "source_or_forcing_written":False,
        "outputs_SHA256":{n:sha(out/n) for n in [*data,name,marker]}}
    (out/"stage13ah_readonly_sha_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print("STAGE13AH READONLY REPORT DIR:",out,flush=True)
    print("STAGE13AH ALL 46 MISSING ORIGINAL TOWER ERA BEFORE AFTER REVIEW COMPLETE; NO DATM/AD400/SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as e:
        print("STAGE13AH SOURCE SCIENCE STOP:",e,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

#!/usr/bin/env python3
"""US-Me6 Stage13AE: source-native five-run isolation vs sustained-anomaly review.

Verify original 13-method source and the actual Stage13AD full-site shadow.
Scan all 778 held QC1 source records and QC2 near five run boundaries;
show five-node original tower, paired ERA and latest selected observations,
classify SINGLE isolated source spikes only with guarded neighbors.
Output reproducible READONLY reports, NO new operator repair/forcing/jobs.
"""
import argparse,hashlib,importlib.util,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VER="batch03-stage13ae-v2-20261028-Me6-SHA-locked-full-Stage13S-explicit-source"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
HERE=Path(__file__).resolve().parent
VALIDATE=HERE/"13_validation_Me6_six_run_repair_candidates.py"
VALID_BLOB="de62b7f6d1001fafa923163e565b2945bb2a8816"
AD=ROOT/"science_trials/stage13ad_Me6_isolated_originalQC2_Jul04_1200_QC1_anchor_trial_20261028T170952Z_4ac00fee"
ADCSV="US-Me6_STAGE13AD_SingleQC2_20170704_1200_QC1_Neighbors_RESEARCH_ONLY_NOLEAP.csv"
ADREC="stage13ad_approved_conditional_trial_SHA_receipt.json"
AA=ROOT/"science_trials/stage13aa_Me6_Run12_4HH_QC0_LINEAR_APPROVED_RESEARCH_ONLY_20261028T162945Z_25df5b3a"
AACSV="US-Me6_STAGE13AA_Run12_4HH_APPROVED_QC0_LINEAR_RESEARCH_ONLY_NOLEAP.csv"
AASHA="0da1d24f9b84d4c4a126d9a9d39ed107023d24914ed9ab122a10de0345e8ee80"
SSHA="02e80edf89af35874a5cfb2c134e42fbe771b9b2ccc0899bfc4fe19bc2e18565"
# Do not look for S / S_CSV attributes in the 13_validation module:
# Stage13s lives in its Stage13x predecessor. Pin the original complete
# Stage13s source and verify its full-file SHA before loading all columns.
S=ROOT/"science_trials/stage13s_Me6_12x2015_235HH_ERA_RH_operator_approved_20261027T065056Z_6890a105"
S_CSV="US-Me6_STAGE13S_12x2015_QC1_235HH_ERA_RH_OPERATOR_APPROVED_RESEARCH_ONLY_NOLEAP.csv"
COUNTS={14:469,15:95,16:30,17:137,18:47}
HH=pd.Timedelta(minutes=30)
PREVIOUS=set(pd.date_range("2015-09-26 05:00",periods=4,freq="30min")) | \
         {pd.Timestamp("2017-07-04 12:00")} | \
         set(pd.date_range("2017-07-04 06:00",periods=5,freq="30min"))
HARD14=set(pd.to_datetime(["2015-11-07 03:00","2015-11-07 04:00",
"2015-11-07 04:30","2015-11-07 05:00","2015-11-07 08:00",
"2017-06-29 23:00","2017-06-29 23:30","2017-06-30 00:00",
"2017-06-30 00:30","2017-06-30 01:00","2017-06-30 01:30",
"2017-06-30 02:00","2017-06-30 02:30","2017-07-03 07:00"]))
MAX_NEIGHBOR_STEP=2.0
MAX_ANCHOR_GAP=2.0
MAX_SOURCE_RESIDUAL=4.0
MAX_T_STEP=3.5
MAX_REPAIRED_STEP=4.0
def need(ok,msg):
    if not bool(ok):raise RuntimeError("STAGE13AE SOURCE HOLD: "+str(msg))
def must(path):
    p=Path(path);need(p.is_file() and not p.is_symlink(),"missing/symlink "+str(p));return p
def sha(p):
    h=hashlib.sha256()
    with must(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def gitblob(p):
    b=must(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def es(t):
    t=float(t)
    return 6.112*np.exp(17.67*t/(t+243.5)) if np.isfinite(t) else float("nan")
def q_from_vpd(v,t,p):
    v,t,p=float(v),float(t),float(p)
    sv=es(t);vap=(sv-v)*100.0;den=p-.378*vap
    q=.622*vap/den if np.isfinite(den) and den!=0 else float("nan")
    good=bool(np.isfinite([v,t,p,sv,q]).all()
              and 50000<p<110000 and 0<v<sv and 0<q<.08 and den>0)
    return q,good
def native(s):
    k=pd.DatetimeIndex(pd.to_datetime(s.astype(str).str.replace(
        r"[^0-9]","",regex=True).str[:12],format="%Y%m%d%H%M",errors="raise"))
    need(k.is_unique and k.is_monotonic_increasing and len(k)==280320
         and not ((k.month==2)&(k.day==29)).any(),
         "unmodified source sixteen-year native noleap keys")
    return k
def selftest():
    need(sum(COUNTS.values())==778 and len(HARD14)==14 and len(PREVIOUS)==10,
         "five held runs, 14 exact science holds and ten protected original source times")
    vals=[27.711,28.983,21.840,29.150,28.664]
    candidate=(vals[1]+vals[3])/2
    need(np.isclose(candidate,29.0665,atol=1e-10,rtol=0)
         and np.max(np.abs(np.diff([vals[0],vals[1],candidate,vals[3],vals[4]])))<4,
         "original isolated spike regression")
    need(q_from_vpd(candidate,28.99,95000)[1]
         and not q_from_vpd(-1,28.99,95000)[1],
         "original water-specific humidity science physics")
    print("STAGE13AE SELF-TEST PASS | five held runs, exact protected 2015/2017, isolated original source vs candidate distinction; NO WRITES",flush=True)
def verified():
    need(gitblob(VALIDATE)==VALID_BLOB,
         "original 13-method source verification reader changed")
    spec=importlib.util.spec_from_file_location("me6_13_validation_for_13ae",must(VALIDATE))
    need(spec is not None and spec.loader is not None,"13-validation reader missing")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    need(mod.VER=="batch03-stage13_validation-v1-20261027-Me6-six-run-validated-repair-candidates",
         "13-method original provenance version mismatch")
    raw,selected_subset,runs,meta=mod.load_inputs()
    # Validation preprocessor reads only five fields; the research shadow
    # is a full native forcing CSV. Reload complete SHA-sealed Stage13S here
    # so every original variable/column can be differential-checked.
    need(sha(S/S_CSV)==SSHA, "original full Stage13S CSV source SHA changed")
    old=pd.read_csv(must(S/S_CSV),dtype={"time":str},low_memory=False)
    old.index=native(old.time)
    need(meta.get("Stage13s_input_SHA256")==SSHA,
         "original certified Stage13S source SHA mismatch")
    doc=json.loads(must(AD/ADREC).read_text())
    need(doc.get("site")=="US-Me6" and doc.get("separate_research_only_csv") is True
         and doc.get("forcings_production_written") is False
         and doc.get("parent_Stage13AA_SHA256")==AASHA
         and set(doc.get("output_SHA256",{}))=={
             ADCSV,"stage13ad_isolated_spike_science_and_approval_SCOPE.json",
             "RESEARCH_ONLY_QC1_ANCHORS_NOT_OBSERVED_QC0_NO_DATM"},
         "latest actual Stage13AD original source receipt or scope changed")
    for name,digest in doc["output_SHA256"].items():
        need("/" not in name and "\\" not in name and sha(AD/name)==digest,
             "latest source research shadow receipt file SHA changed "+name)
    need(sha(AA/AACSV)==AASHA,"preceding Stage13AA original approved four-HH shadow changed")
    latest=pd.read_csv(must(AD/ADCSV),dtype={"time":str},low_memory=False)
    latest.index=native(latest.time)
    need(len(old)==len(latest)==280320 and old.index.equals(latest.index)
         and list(old.columns)==list(latest.columns),
         "latest site shadow differs from original native clock/schema")
    for col in old.columns:
        if col=="time":need(old[col].equals(latest[col]),"source native clock changed")
        else:
            a=pd.to_numeric(old[col],errors="raise").to_numpy(float)
            b=pd.to_numeric(latest[col],errors="raise").to_numpy(float)
            mask=~np.isclose(a,b,atol=1e-12,rtol=0,equal_nan=True)
            changed=set(old.index[mask])
            if col in ("QBOT","VPD_USE"):
                need(changed==set(pd.date_range("2015-09-26 05:00",periods=4,freq="30min")) |
                     {pd.Timestamp("2017-07-04 12:00")},
                     "unexpected or missing exactly 5 new source repairs "+col)
            else:need(not changed,"unapproved site field changed "+col)
    need(raw.index.is_unique and raw.index.is_monotonic_increasing,
         "original raw 2015/2017 source native chronology mismatch")
    return raw,old,latest,runs,meta
def evaluate():
    raw,old,latest,runs,meta=verified()
    raw_index=raw.index
    scopes={}
    intended={}
    for gid,n in COUNTS.items():
        r=runs.loc[runs.source_full_run_id.eq(gid)]
        need(len(r)==1,"historical source run group absent "+str(gid))
        d=r.iloc[0];start=pd.Timestamp(d.source_original_QC1_start)
        end=pd.Timestamp(d.source_original_QC1_end)
        times=pd.date_range(start,end,freq="30min")
        need(len(times)==n and times.isin(raw_index).all()
             and (raw.loc[times,"VPD_F_QC"]==1).all(),
             "original held source QC1 native sequence changed "+str(gid))
        scopes[gid]=(start,end,times)
        for t in times:
            need(t not in intended,"source held QC1 scopes overlap")
            intended[t]=gid
    need(len(intended)==778,"all five original held run HH not included")
    extras={}
    for gid,(first,last,ts) in scopes.items():
        for boundary in (first-HH,last+HH):
            need(boundary in raw.index and int(raw.at[boundary,"VPD_F_QC"]) in (0,1,2),
                 "original immediate source boundary QC absent")
        for t in pd.date_range(first-5*HH,first-HH,freq="30min").append(
                 pd.date_range(last+HH,last+5*HH,freq="30min")):
            if t in raw_index and float(raw.at[t,"VPD_F_QC"])==2 and t not in intended:
                extras.setdefault(t,set()).add(gid)
    alltargets=sorted(set(intended)|set(extras))
    records=[]
    for t in alltargets:
        gid=intended.get(t)
        if gid is None:gid=sorted(extras[t])[0]
        ids=[t+HH*j for j in (-2,-1,0,1,2)]
        if not set(ids).issubset(set(raw_index)):
            continue
        rr=raw.loc[ids];ss=latest.loc[ids]
        v=rr.VPD_F.to_numpy(float)
        qc=rr.VPD_F_QC.to_numpy(float)
        tt=rr.TA_F.to_numpy(float)
        tqc=rr.TA_F_QC.to_numpy(float)
        selected_t=ss.TA_USE.to_numpy(float)
        selected_v=ss.VPD_USE.to_numpy(float)
        ps=ss.PSRF.to_numpy(float)
        eras=rr.VPD_ERA.to_numpy(float)
        erat=rr.TA_ERA.to_numpy(float)
        measured_t_ok=bool(np.isfinite(tt).all()
              and np.all(tqc==0) and np.allclose(tt,selected_t,atol=1e-7,rtol=0)
              and np.max(abs(np.diff(tt)))<=MAX_T_STEP)
        neighbor_qc=bool(np.isin(qc[[0,1,3,4]],[0,1]).all())
        physical_flanks=bool(all(q_from_vpd(v[j],tt[j],ps[j])[1] for j in (0,1,3,4)))
        anchors_original=bool(np.isfinite(selected_v[[0,1,3,4]]).all() and
             np.allclose(v[[0,1,3,4]],selected_v[[0,1,3,4]],rtol=0,atol=1e-7))
        isolated=False;pred=float("nan");qpred=float("nan");maxstep=float("nan")
        if np.isfinite(v[[0,1,3,4]]).all():
            pred=(v[1]+v[3])/2
            qpred,physical_pred=q_from_vpd(pred,tt[2],ps[2])
            maxstep=float(np.max(abs(np.diff([v[0],v[1],pred,v[3],v[4]]))))
            spike=bool(np.isfinite(v[2]) and abs(v[2]-pred)>=MAX_SOURCE_RESIDUAL)
            locally_contiguous=bool(
                abs(v[1]-v[0])<=MAX_NEIGHBOR_STEP and
                abs(v[4]-v[3])<=MAX_NEIGHBOR_STEP and
                abs(v[3]-v[1])<=MAX_ANCHOR_GAP)
            original_unchanged=bool(np.isclose(selected_v[2],v[2],atol=1e-7,rtol=0,equal_nan=True))
            isolated=(spike and locally_contiguous and measured_t_ok and
                neighbor_qc and physical_flanks and anchors_original and
                physical_pred and maxstep<=MAX_REPAIRED_STEP and
                original_unchanged and t not in PREVIOUS and qc[2] in (1,2))
        if t in PREVIOUS: decision="PREVIOUSLY_PROTECTED_DO_NOT_EDIT"
        elif isolated:
            decision=("REVIEW_SOURCE_QC0_ANCHORED_SINGLE_SPIKE" if
                      qc[1]==qc[3]==0 else
                      "REVIEW_QC1_ANCHORED_SINGLE_SPIKE_NO_AUTO_APPROVAL")
        elif gid==14 and t in HARD14:decision="HOLD_LONG_EVENT_SITE_ERA_T_MISMATCH"
        elif t in HARD14:decision="HOLD_SOURCE_T_GRID_DISAGREEMENT_GT8C"
        else:decision="NO_ISOLATED_SOURCE_SPIKE_PASS_KEEP_ORIGINAL_HOLD"
        entry={
          "run_id":gid,"native_time":str(t),
          "original_source_center_scope":"HELD_QC1_RUN" if t in intended else "NEAR_RUN_QC2_BOUNDARY",
          "decision":decision,
          "center_original_tower_VPD_QC":qc[2],
          "five_native_source_tower_TA_F_C":",".join(str(x) for x in tt),
          "five_native_source_tower_TA_QC":",".join(str(x) for x in tqc),
          "five_original_source_tower_VPD_F_hPa":",".join(str(x) for x in v),
          "five_original_source_tower_VPD_QC":",".join(str(x) for x in qc),
          "before_60min_source_tower_VPD_hPa":v[0],
          "before_30min_source_tower_VPD_hPa":v[1],
          "center_source_tower_VPD_hPa":v[2],
          "after_30min_source_tower_VPD_hPa":v[3],
          "after_60min_source_tower_VPD_hPa":v[4],
          "before_30min_source_ERA_VPD_hPa":eras[1],
          "center_source_ERA_VPD_hPa":eras[2],
          "after_30min_source_ERA_VPD_hPa":eras[3],
          "before_30min_source_tower_T_C":tt[1],
          "center_source_tower_T_C":tt[2],
          "after_30min_source_tower_T_C":tt[3],
          "before_30min_source_ERA_T_C":erat[1],
          "center_source_ERA_T_C":erat[2],
          "after_30min_source_ERA_T_C":erat[3],
          "before_current_research_VPD_hPa":selected_v[1],
          "center_current_research_VPD_hPa":selected_v[2],
          "after_current_research_VPD_hPa":selected_v[3],
          "hypothetical_one_center_interpolated_VPD_hPa":pred,
          "hypothetical_one_center_rederived_QBOT_kgkg":qpred,
          "hypothetical_five_native_max_step_hPa":maxstep,
          "original_site_T_QC0_five_times_and_consistent":measured_t_ok,
          "flanking_original_VPD_QC0_OR_QC1":neighbor_qc,
          "flanking_tower_VPD_at_site_TP_water_physically_valid":physical_flanks,
          "flanking_tower_VPD_matches_selected":anchors_original,
          "direct_measured_QC0_VPD_both_immediate_neighbors":bool(qc[1]==0 and qc[3]==0),
          "source_center_T_minus_ERA_T_C":tt[2]-erat[2],
          "center_original_site_T_vs_ERA_GT8C":bool(np.isfinite([tt[2],erat[2]]).all()
                                               and abs(tt[2]-erat[2])>8),
          "method_operator_approved_for_this_center":False}
        records.append(entry)
    table=pd.DataFrame(records)
    need(len(table)>=778
         and set(intended).issubset(set(pd.to_datetime(table.native_time)))
         and (table.center_original_tower_VPD_QC.isin((1,2))).all(),
         "full held original source QC1 coverage/center metadata changed")
    c=table.loc[table.decision.str.startswith("REVIEW_")].copy()
    totals=table.groupby(["run_id","original_source_center_scope","decision"]).size().reset_index(name="count")
    summary={"version":VER,"site":"US-Me6","original_full_held_run_counts":COUNTS,
       "five_original_QC1_run_HH":778,"additional_QC2_near_original_run_boundary":len(extras),
       "review_screened_source_centers":len(table),
       "new_strict_isolated_source_spike_REVIEW_candidates":len(c),
       "QC0_both_side_candidates":int(c.direct_measured_QC0_VPD_both_immediate_neighbors.sum()),
       "QC1_or_mixed_neighbors_candidates":int((~c.direct_measured_QC0_VPD_both_immediate_neighbors).sum()),
       "original_14_site_ERA_T_disagreements_protected":True,
       "previous_2015_235_and_4HH_2017_5HH_and_20170704_1200_protected":True,
       "Stage13AD_latest_shadow_sha256":sha(AD/ADCSV),
       "original_Stage13S_SHA256":SSHA,
       "candidate_operator_approval":False,"source_or_forcing_written":False,
       "Postv5":False,"DATM":False,"AD400":False,"Slurm":False}
    print("STAGE13AE RUN14-18 SOURCE-OBSERVATION CONTEXT / SINGLE SPIKE CLASSIFICATION",flush=True)
    print(totals.to_string(index=False),flush=True)
    print("STAGE13AE STRICT NEW ISOLATED SOURCE SPIKE REVIEW CANDIDATES",flush=True)
    cols=["run_id","native_time","center_original_tower_VPD_QC",
        "before_60min_source_tower_VPD_hPa","before_30min_source_tower_VPD_hPa",
        "center_source_tower_VPD_hPa","after_30min_source_tower_VPD_hPa",
        "after_60min_source_tower_VPD_hPa",
        "before_30min_source_ERA_VPD_hPa","center_source_ERA_VPD_hPa",
        "after_30min_source_ERA_VPD_hPa",
        "hypothetical_one_center_interpolated_VPD_hPa",
        "hypothetical_five_native_max_step_hPa",
        "direct_measured_QC0_VPD_both_immediate_neighbors","decision"]
    print(c[cols].to_string(index=False) if len(c) else "NONE: no further isolated source center satisfies strict original neighbor and physics gates",flush=True)
    print("STAGE13AE SCREEN SUMMARY",json.dumps(summary,indent=2),flush=True)
    return table,c,totals,summary
def main():
    p=argparse.ArgumentParser()
    modes=p.add_mutually_exclusive_group(required=True)
    for m in ("self-test","check","run"):modes.add_argument("--"+m,action="store_true")
    args=p.parse_args()
    selftest()
    if args.self_test:return
    allrows,c,totals,s=evaluate()
    if args.check:
        print("STAGE13AE READONLY CHECK PASS | all five held run source flanks audited; no shadow writes",flush=True)
        return
    out=ROOT/"reports"/("stage13ae_Me6_five_held_runs_source_isolated_spike_scan_READONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    files={
      "all_Run14_18_original_source_5node_context_and_flags.csv":allrows,
      "strict_isolated_source_spike_candidate_REVIEW_ONLY.csv":c,
      "five_run_source_anomaly_decision_counts.csv":totals}
    for name,data in files.items():data.to_csv(out/name,index=False,float_format="%.17g")
    sn="stage13ae_summary.json";marker="NO_NEW_SOURCE_METHOD_APPROVAL_NO_FORCING_OR_MODEL"
    (out/sn).write_text(json.dumps(s,indent=2)+"\n")
    (out/marker).write_text("Exact original source and existing research shadow. "
       "Candidate interpolation values are unapproved and NOT applied. "
       "Never infer original QC1 is directly measured QC0. No DATM/spinup.\n")
    receipt={"version":VER,"site":"US-Me6","forcing_or_model_written":False,
         "outputs_SHA256":{x:sha(out/x) for x in [*files,sn,marker]}}
    (out/"stage13ae_readonly_sha_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print("STAGE13AE READONLY REPORT DIR:",out,flush=True)
    print("STAGE13AE SOURCE ORIGINAL FIVE-RUN ISOLATED REVIEW COMPLETE | NO SHADOW/FORCING/DATM/SLURM",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE13AE SCIENCE STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc();raise SystemExit(2)

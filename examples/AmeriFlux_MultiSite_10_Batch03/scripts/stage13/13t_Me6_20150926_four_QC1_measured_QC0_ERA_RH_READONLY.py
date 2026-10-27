#!/usr/bin/env python3
"""Stage13t US-Me6 September 26 2015 four native humidity QC1 source HOLDs.

After source-verified Stage13s research-only success, diagnose the one
short ORIGINAL 2015 QC1 full run still HOLD (Stage13r ID 12):
2015-09-26 05:00,05:30,06:00,06:30.
Its original measured VPD_F_QC0 bookends are 04:30 and 07:00 but the
paired ERA RH-at-retained-T full interval had a 4.800355hPa jump.

Compare original tower + companion ERA, actual signed Stage12ac and
latest signed Stage13s shadow; rederive full 6-node ERA RH candidate,
node-to-node VPD jumps and source measured QC0 anchors. Include a
separate HYPOTHETICAL QC0-anchored straight-line VPD preview for
diagnostic comparison only, not as scientifically approved replacement.

NO interpolations adopted, NO original source/forcing edits, NO model jobs.
--self-test no reads/writes; --check read-only; --run sign source
diagnostic CSV+JSON in NEW reports directory (not forcing).
"""
import argparse, hashlib, importlib.util, json, subprocess, sys, traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
VERSION="batch03-stage13t-v1-20261027-Me6-four-20150926-QC1-QC0-source-science"
HERE=Path(__file__).resolve().parent
PREV=HERE/"13r_Me6_33_full_original_QC1_runs_QC0_ERA_RH_OPERATOR_SCOPE_READONLY.py"
PREV_BLOB="5a8dc69f5fb65015a9b7c9096153935684f466a8"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
RREPORT=ROOT/"reports/stage13r_Me6_original_full_QC1_run_and_original_QC0_ERA_RH_READONLY_20261027T004033Z_5eefea7b"
LAST=ROOT/"science_trials/stage13s_Me6_12x2015_235HH_ERA_RH_operator_approved_20261027T065056Z_6890a105"
AC=ROOT/"science_trials/stage12ac_USER_APPROVED_Me6_20170704_0600_0800_ERA_RH_20261025T232237Z_534eb248"
LAST_NAME="US-Me6_STAGE13S_12x2015_QC1_235HH_ERA_RH_OPERATOR_APPROVED_RESEARCH_ONLY_NOLEAP.csv"
LAST_RECEIPT="stage13s_Me6_operator_235HH_SHA_receipt.json"
AC_NAME="US-Me6_STAGE12AC_USER_APPROVED_OVERLAY_INCOMPLETE_NOLEAP.csv"
START=pd.Timestamp("2015-09-26 05:00:00")
END=pd.Timestamp("2015-09-26 06:30:00")
HH=pd.Timedelta(minutes=30)
INTERVAL=pd.date_range(START,END,freq="30min")
BEFORE=START-HH
AFTER=END+HH
BOUND=(BEFORE,*INTERVAL,AFTER)
CONTEXT=pd.date_range(BEFORE-pd.Timedelta(hours=3),
                      AFTER+pd.Timedelta(hours=3),freq="30min")
JUMP_LIMIT=4.

def must(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise RuntimeError("Stage13t source missing/unsafe symlink: "+str(p))
    return p

def digest(p):
    h=hashlib.sha256()
    with must(p).open("rb") as fh:
        for x in iter(lambda:fh.read(1<<20),b""):
            h.update(x)
    return h.hexdigest()

def require(c,message):
    if not bool(c):
        raise RuntimeError("STAGE13T READONLY SOURCE SCIENCE STOP: "+message)

def near(a,b,atol=1e-8):
    return bool(np.isfinite([float(a),float(b)]).all() and
                np.isclose(float(a),float(b),atol=atol,rtol=0))

def load_prev():
    p=must(PREV)
    blob=subprocess.run(["git","hash-object",str(p)],check=True,
                        capture_output=True,text=True).stdout.strip()
    require(blob==PREV_BLOB,"Stage13r previous original scientific source blob changed")
    spec=importlib.util.spec_from_file_location("stage13r_signed_stage13t",p)
    require(spec is not None and spec.loader is not None,"cannot load original Stage13r")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    require(mod.VER=="batch03-stage13r-v1-20261027-Me6-original-full-QC1-run-survey"
            and mod.ROOT==ROOT and mod.AC==AC and mod.Q==ROOT/"reports/stage13q_Me6_33_original_ERA_RH_group_source_review_20261027T002737Z_445444f6",
            "original Stage13r source parameters changed")
    return mod

def selftest():
    require(len(INTERVAL)==4 and len(BOUND)==6 and
            all(BOUND[i+1]-BOUND[i]==HH for i in range(5)),
            "original measured QC0 + four QC1 halfhour source cadence")
    require(len(CONTEXT)==18 and
            CONTEXT[0]==BEFORE-pd.Timedelta(hours=3),
            "source context window changed")
    a=1.0;b=6.0
    proposed=[a+(b-a)*i/5 for i in range(6)]
    require(len(proposed)==6 and np.allclose(np.diff(proposed),1),
            "QC0 anchor candidate should interpolate exactly for audit only")
    require(JUMP_LIMIT==4 and START.year==2015,
            "original hold 4hPa safety gate changed")
    print("STAGE13T SELF-TEST PASS | 4 source QC1 + 2 true QC0, ERA-RH versus anchor-diagnostic-only, no writes",flush=True)

def force(path):
    df=pd.read_csv(must(path),dtype={"time":str},low_memory=False)
    native=pd.to_datetime(df.time.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12),
                          format="%Y%m%d%H%M",errors="raise")
    require(len(df)==280320 and native.is_unique and native.is_monotonic_increasing,
            "full Me6 16-year NOLEAP original site input changed")
    require(set(CONTEXT).issubset(set(native)),"original Me6 2015 native context missing")
    df.index=pd.DatetimeIndex(native,name="native_time")
    return df

def audit():
    prev=load_prev()
    spec,centers,_,_=prev.verified()
    signed=json.loads(must(RREPORT/"stage13r_source_original_QC1_SHA_receipt.json").read_text())
    require(signed.get("site")=="US-Me6" and
            signed.get("source_full_original_QC1_runs")==18 and
            signed.get("model_forcing_written") is False,
            "Stage13r actual signed original 18 QC1 segment evidence missing")
    outputs=signed.get("outputs_SHA256",{})
    target="US-Me6_source_original_full_QC1_runs_grouped_OPERATOR_APPROVAL_NEEDED.csv"
    require(outputs.get(target)==digest(RREPORT/target),
            "Stage13r original science report tampered")
    group=pd.read_csv(must(RREPORT/target),low_memory=False)
    r=group.loc[group.source_full_run_id.eq(12)]
    require(len(r)==1 and
            r.iloc[0].source_original_QC1_start==str(START) and
            r.iloc[0].source_original_QC1_end==str(END) and
            int(r.iloc[0].original_QC1_halfhour_count)==4 and
            int(r.iloc[0].previously_method_approved_source_centers)==1 and
            not bool(r.iloc[0].full_run_meets_all_source_QC0_ERA_RH_boundary_gates_preview) and
            near(float(r.iloc[0].max_30min_VPD_step_hPa_ERA_RH_full_run_preview),
                 4.800355,0.000001),
            "Stage13r original specific four-HH QC0-bound 4.800355hPa HOLD changed")
    receipt=json.loads(must(LAST/LAST_RECEIPT).read_text())
    require(receipt.get("version")=="batch03-stage13s-v1-20261027-Me6-12-full-2015-QC1-runs-235HH" and
            receipt.get("approved_original_source_halfhours")==235 and
            receipt.get("all_12_entire_native_2015_original_QC1_runs_science_PASS") is True and
            receipt.get("output_SHA256",{}).get(LAST_NAME)==digest(LAST/LAST_NAME) and
            receipt.get("immutable_original_Stage12ac_SHA256")==digest(AC/AC_NAME),
            "Stage13s actual successful research-only shadow or source SHA missing")
    originals=force(AC/AC_NAME)
    current=force(LAST/LAST_NAME)
    require(current.time.equals(originals.time) and
            list(current.columns)==list(originals.columns),
            "Stage13s candidate native time/full field schema mismatch")
    for t in CONTEXT:
        aa=originals.loc[t]
        bb=current.loc[t]
        require(str(aa["time"])==str(bb["time"]),
                "original selected native source time changed "+str(t))
        for field in originals.columns:
            if field=="time":continue
            a=float(aa[field]);b=float(bb[field])
            require((np.isnan(a) and np.isnan(b)) or
                    np.isclose(a,b,rtol=1e-14,atol=1e-12),
                    "user-approved Stage13s improperly affected unapproved 2015 Sep26 source "+
                    str(t)+" "+field)
    source_cols=["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"]
    era_cols=["TIMESTAMP_START","TA_ERA","VPD_ERA"]
    tower=pd.read_csv(must(spec["primary"]),dtype={"TIMESTAMP_START":str},
                      usecols=source_cols,low_memory=False)
    era=pd.read_csv(must(spec["era"]),dtype={"TIMESTAMP_START":str},
                    usecols=era_cols,low_memory=False)
    ks={t.strftime("%Y%m%d%H%M") for t in CONTEXT}
    tower=tower.loc[tower.TIMESTAMP_START.isin(ks)]
    era=era.loc[era.TIMESTAMP_START.isin(ks)]
    require(len(tower)==len(era)==len(CONTEXT) and
            tower.TIMESTAMP_START.is_unique and era.TIMESTAMP_START.is_unique and
            set(tower.TIMESTAMP_START)==set(era.TIMESTAMP_START)==ks,
            "Original source tower / companion ERA 2015 Sep26 exact context missing")
    src=tower.merge(era,on="TIMESTAMP_START",validate="one_to_one")
    src.index=pd.DatetimeIndex(pd.to_datetime(src.TIMESTAMP_START,format="%Y%m%d%H%M"))
    for name in (*source_cols[1:],*era_cols[1:]):
        src[name]=pd.to_numeric(src[name],errors="coerce")
        src.loc[src[name]<=-9990,name]=np.nan
    for t in (BEFORE,AFTER):
        require(src.at[t,"VPD_F_QC"]==0 and
                near(src.at[t,"VPD_F"],originals.at[t,"VPD_USE"],1e-7),
                "original source measured VPD QC0 bookend not retained "+str(t))
    for t in INTERVAL:
        require(src.at[t,"VPD_F_QC"]==1 and src.at[t,"TA_F_QC"]==0 and
                near(src.at[t,"TA_F"],originals.at[t,"TA_USE"],1e-7),
                "original 4HH VPD QC1 / valid measured site temperature changed "+str(t))
    entries=[]
    for t in CONTEXT:
        siteT=float(originals.at[t,"TA_USE"])
        pressure=float(originals.at[t,"PSRF"])
        raw=src.loc[t]
        v,q,rh,phys=prev.src_rh_at_site(siteT,pressure,
                  float(raw.TA_ERA),float(raw.VPD_ERA))
        entries.append({
            "native_time":str(t),
            "in_original_4HH_QC1_HOLD_scope":bool(t in INTERVAL),
            "true_measured_QC0_bookend":bool(t in (BEFORE,AFTER)),
            "original_tower_TA_F_C":float(raw.TA_F),
            "original_tower_TA_F_QC":float(raw.TA_F_QC),
            "original_tower_VPD_F_hPa":float(raw.VPD_F),
            "original_tower_VPD_F_QC":float(raw.VPD_F_QC),
            "companion_ERA_T_C":float(raw.TA_ERA),
            "companion_ERA_VPD_hPa":float(raw.VPD_ERA),
            "companion_ERA_RH_pct":rh,
            "retained_original_site_TA_USE_C":siteT,
            "retained_original_PSRF_Pa":pressure,
            "unchanged_Stage13s_selected_VPD_hPa":float(current.at[t,"VPD_USE"]),
            "unchanged_Stage13s_selected_QBOT_kgkg":float(current.at[t,"QBOT"]),
            "HYPOTHETICAL_ERA_RH_at_siteT_VPD_hPa":v,
            "HYPOTHETICAL_ERA_RH_at_siteT_QBOT_kgkg":q,
            "paired_ERA_T_RH_QBOT_physics_status":phys
        })
    data=pd.DataFrame(entries)
    included=data.loc[data.native_time.isin({str(x) for x in BOUND})].copy()
    require(len(included)==6,"Original specific 6-node core source sequence incomplete")
    assert len(BOUND)==6
    chosen=[]
    for t in BOUND:
        row=included.loc[included.native_time.eq(str(t))].iloc[0]
        if t in (BEFORE,AFTER):
            chosen.append(float(row.unchanged_Stage13s_selected_VPD_hPa))
        else:
            chosen.append(float(row.HYPOTHETICAL_ERA_RH_at_siteT_VPD_hPa))
    linear=[chosen[0]+(chosen[-1]-chosen[0])*i/5 for i in range(6)]
    edge=[]
    for i in range(5):
        a,b=BOUND[i],BOUND[i+1]
        edge.append({
          "source_native_from":str(a),"source_native_to":str(b),
          "candidate_ERA_RH_with_measured_QC0_step_hPa":abs(chosen[i+1]-chosen[i]),
          "old_Stage13s_selected_VPD_step_hPa":
             abs(float(current.at[b,"VPD_USE"])-float(current.at[a,"VPD_USE"])),
          "HYPOTHETICAL_anchor_linear_VPD_step_hPa":
             abs(linear[i+1]-linear[i]),
          "ERA_RH_candidate_meets_preexisting_4hPa_threshold":
             bool(abs(chosen[i+1]-chosen[i])<=JUMP_LIMIT),
          "both_bookend_measured_tower_VPD_values_unchanged":True,
          "linear_method_NOT_USER_APPROVED":True
        })
    step=pd.DataFrame(edge)
    maxERA=float(step.candidate_ERA_RH_with_measured_QC0_step_hPa.max())
    require(near(maxERA,4.800355,0.000001) and
            int((step.candidate_ERA_RH_with_measured_QC0_step_hPa>JUMP_LIMIT).sum())>=1,
            "Stage13r original HOLD not reproduced from current SHA verified tower/ERA")
    for idx,t in enumerate(BOUND):
        data.loc[data.native_time.eq(str(t)),"HYPOTHETICAL_QC0_bookend_linear_VPD_hPa"]=linear[idx]
        # Interior hypothetical moisture depends on original T and PSRF.
        if t in INTERVAL:
            row=included.loc[included.native_time.eq(str(t))].iloc[0]
            es=prev.water_es(float(row.retained_original_site_TA_USE_C))
            ea=(es-linear[idx])*100
            q=.622*ea/(float(row.retained_original_PSRF_Pa)-.378*ea)
            phys=bool(0<linear[idx]<es and 0<q<.08)
            data.loc[data.native_time.eq(str(t)),"HYPOTHETICAL_linear_VPD_QBOT_physics_PASS"]=phys
            data.loc[data.native_time.eq(str(t)),"HYPOTHETICAL_QC0_bookend_linear_QBOT_kgkg"]=q
    summary={
      "version":VERSION,"site":"US-Me6","original_Stage13r_held_full_run_ID":12,
      "exact_original_QC1_native_times":[str(x) for x in INTERVAL],
      "original_measured_tower_VPD_QC0_bookends":[str(BEFORE),str(AFTER)],
      "all_original_source_records_and_Sep26_Stage13s_shadow_unchanged":True,
      "original_sealed_Stage13s_research_shadow_SHA256":digest(LAST/LAST_NAME),
      "original_signed_Stage13r_source_receipt_SHA256":digest(RREPORT/"stage13r_source_original_QC1_SHA_receipt.json"),
      "original_tower_SHA256":digest(spec["primary"]),
      "original_companion_ERA_SHA256":digest(spec["era"]),
      "source_ERA_RH_at_siteT_max_native_jump_hPa":maxERA,
      "source_ERA_RH_candidate_over_4hPa_edges":int((step.candidate_ERA_RH_with_measured_QC0_step_hPa>4).sum()),
      "hypothetical_QC0_anchor_linear_max_jump_hPa":float(step.HYPOTHETICAL_anchor_linear_VPD_step_hPa.max()),
      "hypothetical_QC0_anchor_linear_science_method_NOT_approved":True,
      "operator_has_NOT_approved_run_12_source_4HH_repair":True,
      "model_or_forcing_modified":False,"DATM_ready":False,"Slurm_jobs":False
    }
    print("STAGE13T ORIGINAL FOUR SOURCE QC1 HH + TWO MEASURED QC0 BOUNDARIES",flush=True)
    print(included[["native_time","original_tower_VPD_F_QC",
        "original_tower_VPD_F_hPa","companion_ERA_RH_pct",
        "unchanged_Stage13s_selected_VPD_hPa",
        "HYPOTHETICAL_ERA_RH_at_siteT_VPD_hPa"]].to_string(index=False),flush=True)
    print("STAGE13T ORIGINAL NATIVE 30-MINUTE EDGE-LEVEL CONFLICT",flush=True)
    print(step.to_string(index=False),flush=True)
    print("STAGE13T SCIENCE HOLD STATUS",json.dumps(summary,indent=2),flush=True)
    return data,step,summary

def main():
    ap=argparse.ArgumentParser()
    x=ap.add_mutually_exclusive_group(required=True)
    for mode in ("self-test","check","run"):x.add_argument("--"+mode,action="store_true")
    o=ap.parse_args()
    print("STAGE13T ME6 2015SEP26 ORIGINAL 4HH SOURCE QC1 HOLD | "+VERSION,flush=True)
    selftest()
    if o.self_test:return
    data,edges,summary=audit()
    if o.check:
        print("STAGE13T READONLY CHECK PASS | original QC0, Stage13s source and ERA edge diagnosis; held 4HH; NO WRITES",flush=True)
        return
    folder=ROOT/"reports"/("stage13t_Me6_20150926_four_QC1_original_QC0_ERA_RH_READONLY_"+
             datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    folder.mkdir(parents=True,exist_ok=False)
    a="original_source_QC_ERA_RH_siteT_VPD_QBOT_native_context_20150926.csv"
    b="five_source_native_30min_edges_ERA_RH_vs_QC0_anchor_preview.csv"
    c="stage13t_Sep26_four_QC1_HOLD_explanation.json"
    d="READONLY_NO_FORCING_OR_2015SEP26_OPERATOR_REPAIR_APPROVAL"
    data.to_csv(folder/a,index=False,float_format="%.17g")
    edges.to_csv(folder/b,index=False,float_format="%.17g")
    (folder/c).write_text(json.dumps(summary,indent=2)+"\n")
    (folder/d).write_text(
        "Source-anchored linear VPD is DIAGNOSTIC ONLY, NOT valid scientific"
        " operator approval, and no replacement method for these 4 native"
        " source QC1 halfhours has been granted. Preserve whole Stage13s"
        " approved 235 original 2015 native timestamps and Stage12ac original"
        " July2017 five; no DATM/Slurm/AD400 or original forcing writes.\n")
    receipt={"version":VERSION,"site":"US-Me6",
       "stage13s_signed_existing_shadow_SHA256":digest(LAST/LAST_NAME),
       "Stage13r_original_signed_receipt_SHA256":digest(RREPORT/"stage13r_source_original_QC1_SHA_receipt.json"),
       "new_science_or_operator_repair_authorization":False,
       "new_model_forcing_written":False,"postv5":False,"DATM":False,"Slurm":False,
       "files_SHA256":{x:digest(folder/x) for x in (a,b,c,d)}}
    (folder/"stage13t_Me6_four_QC1_original_QC0_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE13T READONLY SCIENCE REPORT DIR:",folder,flush=True)
    print("STAGE13T ME6 20150926 SOURCE QC0 AND ERA-RH FIVE EDGES DIAGNOSTIC COMPLETE; NO FORCING WRITES",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("STAGE13T READONLY SOURCE STOP:",e,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

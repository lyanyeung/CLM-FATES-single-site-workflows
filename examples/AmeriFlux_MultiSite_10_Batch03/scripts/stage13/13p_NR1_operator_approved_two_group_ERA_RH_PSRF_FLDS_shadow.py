#!/usr/bin/env python3
"""Stage13p US-NR1 — signed, user-approved two groups, research shadow only.

Groups: 6 native 2022-09-10 VPD_USE/QBOT pairs from original paired ERA RH;
5 native 2004-12-03 PSRF/FLDS field changes across 4 original QC2 times.
Reuse ORIGINAL signed Stage12ak/Stage12al trial numerics, not any US-Kon
forcings. Original Stage12af-approved 2022 T remains unchanged.

The original 12ak/12al helpers independently recompute tower/ERA SHA,
QC2 source/anchor and six humidity RH/QBOT + seven VPD edges, all source
timestamps. Every previous trial and Stage12af receipt and output SHA
is authenticated. Science gates are WHOLE-GROUP fail-closed; no partial
source export. Remaining 234 NR1 VPD/QBOT gaps are NOT repaired.
--self-test: no source I/O, no writes
--check: full original source science provenance and candidate, no writes
--apply: same gate then new independent 490560-row full NOLEAP NR1 CSV,
         exact 17 numeric-field deltas, readback QA and signed SHA receipt
No original data, Kon, PFT, ZBOT, DATM, model case or Slurm changes.
"""
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import pandas as pd
import numpy as np

sys.dont_write_bytecode=True
VERSION="batch03-stage13p-v1-20261026-NR1-two-approved-source-groups"
HERE=Path(__file__).resolve().parent
AK_SCRIPT=HERE/"12ak_Kon_NR1_seven_nonhumidity_pressure_longwave_SCOPED_TRIAL.py"
AL_SCRIPT=HERE/"12al_NR1_six_native_ERA_RH_on_12ak_nonhumidity_science_trial.py"
AK_BLOB="6c91b342009b3308fabbb42ed75504f3162540db"
AL_BLOB="664953766caec968eeac223c102592296c06e76e"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AF=ROOT/"science_trials/stage12af_NR1_20220910_user_approved_three_T_only_20261026T013349Z_34ff1cda"
AK=ROOT/"science_trials/stage12ak_7_nonhumidity_source_interpolation_PROPOSALS_ONLY_20261026T031747Z_61471fd7"
AL=ROOT/"science_trials/stage12al_NR1_20220910_six_original_native_ERA_RH_RESEARCH_ONLY_20261026T032328Z_f8c3ff27"
AF_NAME="US-NR1_STAGE12AF_USER_APPROVED_T_ONLY_INCOMPLETE_NOLEAP.csv"
AK_NAME="US-NR1_STAGE12AK_NONHUMIDITY_PROPOSAL_ONLY_INCOMPLETE_NOLEAP.csv"
AL_NAME="US-NR1_STAGE12AL_NONHUMIDITY_PLUS_6_ERA_RH_RESEARCH_ONLY_INCOMPLETE_NOLEAP.csv"
OUT="US-NR1_STAGE13P_APPROVED_2022_ERA_RH_AND_2004_PSRF_FLDS_RESEARCH_ONLY_NOLEAP.csv"
DECISION_SCHEMA="batch03-stage13p-NR1-two-science-groups-operator-approved-v1"
DATES6=("202209100600","202209100630","202209100700",
        "202209100730","202209100800","202209100830")
FIVE=(
 ("200412032200","FLDS",191.566),
 ("200412032230","FLDS",191.503),
 ("200412032230","PSRF",69935.75),
 ("200412032300","PSRF",69929.50),
 ("200412032330","PSRF",69923.25)
)
VALID_FIELDS=("VPD_USE","QBOT","PSRF","FLDS")
EXPECTED_N=490560

def must(path):
    p=Path(path)
    if not p.is_file() or p.is_symlink():
        raise RuntimeError("Missing original signed evidence or symlink: "+str(p))
    return p

def sha(path):
    h=hashlib.sha256()
    with must(path).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def require(x,message):
    if not bool(x):raise RuntimeError("STAGE13P SCIENCE STOP/HOLD: "+message)

def valcmp(a,b,tol=1e-9):
    return bool(np.isfinite([float(a),float(b)]).all() and
                np.isclose(float(a),float(b),atol=tol,rtol=0))

def module(path,expected_blob,expected_version):
    p=must(path)
    result=subprocess.run(["git","hash-object",str(p)],check=True,
                          capture_output=True,text=True).stdout.strip()
    require(result==expected_blob,"signed prior source script Git blob changed: "+p.name)
    s=importlib.util.spec_from_file_location("batch03_"+p.stem,p)
    require(s is not None and s.loader is not None,"original signed prior science module loader")
    m=importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    require(getattr(m,"VERSION",None)==expected_version,
            "prior signed source science version changed "+p.name)
    return m

def selftest():
    require(len(DATES6)==6 and len(set(DATES6))==6,"exact six original source times")
    require(len(FIVE)==5 and len({(t,f) for t,f,_ in FIVE})==5,
            "exact five unique QC2 source model values")
    require(len({t for t,f,_ in FIVE})==4,"exact four original native 2004 times")
    require(len(set(DATES6)|{t for t,f,_ in FIVE})==10,
            "exact ten distinct 2004/2022 native times")
    h=pd.to_datetime(list(DATES6),format="%Y%m%d%H%M")
    require(all(h[i+1]-h[i]==pd.Timedelta(minutes=30) for i in range(5)),
            "six original native time cadence altered")
    p=np.array([69.942,69.93575,69.9295,69.92325,69.917])
    require(np.max(np.abs(np.diff(p)))<.007,"tiny signed original pressure correction step")
    t=1.241
    es=6.112*np.exp(17.67*t/(t+243.5))
    v=1.873343;ea=(es-v)*100
    q=.622*ea/(70000-.378*ea)
    require(0<v<es and 0<q<.08,"scientific ERA RH transfer thermodynamics")
    require(234+6==240,"unresolved NR1 source hold inventory")
    print("STAGE13P SELF-TEST PASS | 6 humidity HH, 5 QC2 field corrections across 4 HH, 17 full-source deltas, NO WRITES",flush=True)

def approval(path):
    d=json.loads(must(path).read_text())
    require(d.get("schema")==DECISION_SCHEMA and d.get("site")=="US-NR1" and
            d.get("status","").startswith("USER_APPROVED_TWO_STRICT_GROUPS"),
            "explicit group approval JSON absent")
    require(d.get("Postv5_approved") is False and d.get("DATM_ready") is False and
            d.get("Slurm_jobs_authorized") is False and
            d.get("spinup_authorized") is False,
            "invalid model-release gate in operator approval")
    groups=d.get("groups",[])
    require(len(groups)==2 and groups[0].get("native_keys")==list(DATES6) and
            groups[0].get("original_source_VPD_F_QC_required")==1,
            "operator six native humidity approvals changed")
    require(groups[1].get("required_original_source_QC")==2 and
            len(groups[1].get("model_field_updates",[]))==5,
            "operator five source QC2 nonhumidity approvals changed")
    for obj,(k,f,v) in zip(groups[1]["model_field_updates"],FIVE):
        require(obj.get("native_key")==k and obj.get("field")==f and
                valcmp(obj.get("value"),v,1e-9),
                "one 2004 site PSRF/FLDS operator value no longer approved")
    require(d.get("expected_result",{}).get("NR1_remaining_VPD_QBOT_missing")==234 and
            d.get("expected_result",{}).get("new_NR1_field_value_changes")==17,
            "operator status/gap target changed")
    e=d.get("signed_evidence",{})
    require(e.get("original_Stage12ak_script_git_blob")==AK_BLOB and
            e.get("original_Stage12al_script_git_blob")==AL_BLOB and
            e.get("Stage12ak_science_trial_dir")==str(AK) and
            e.get("Stage12al_science_trial_dir")==str(AL) and
            e.get("Stage12af_approved_temperature_source_dir")==str(AF),
            "operator source receipts/drives changed")
    return d

def sealed_outputs(folder,receipt_name,expected_original_version=None):
    rec=json.loads(must(folder/receipt_name).read_text())
    if expected_original_version is not None:
        require(rec.get("version")==expected_original_version,
                "prior source science report version changed")
    outputs=rec.get("output_SHA256",{})
    require(isinstance(outputs,dict) and len(outputs)>=1,
            "missing full original signed source science output manifest")
    for name,digest in outputs.items():
        require("/" not in name and "\\" not in name and sha(folder/name)==digest,
                "original source trial signed output file changed "+name)
    return rec

def audit(decision_path):
    approved=approval(decision_path)
    ak=module(AK_SCRIPT,AK_BLOB,
      "batch03-stage12ak-v1-20261026-nonhumidity-KON-NR1-eight-variable-proposals")
    al=module(AL_SCRIPT,AL_BLOB,
      "batch03-stage12al-v1-20261026-NR1-six-ERA-RH-research-only")
    af_rec=sealed_outputs(AF,"stage12af_three_temperature_SHA_receipt.json")
    ak_rec=sealed_outputs(AK,"stage12ak_research_proposal_SHA_receipt.json",
        "batch03-stage12ak-v1-20261026-nonhumidity-KON-NR1-eight-variable-proposals")
    al_rec=sealed_outputs(AL,"stage12al_NR1_six_ERA_RH_science_only_SHA_receipt.json",
        "batch03-stage12al-v1-20261026-NR1-six-ERA-RH-research-only")
    require(af_rec.get("three_T_interpolation_operator_approved") is True and
            al_rec.get("input_Stage12af_receipt_sha256")==
                  sha(AF/"stage12af_three_temperature_SHA_receipt.json") and
            al_rec.get("input_Stage12ak_receipt_sha256")==
                  sha(AK/"stage12ak_research_proposal_SHA_receipt.json") and
            al_rec.get("NR1_old_VPD_missing")==240 and
            al_rec.get("NR1_research_only_new_VPD_missing")==234 and
            al_rec.get("six_contiguous_original_source_ERA_RH_humidity_candidates")==6,
            "signed original stage12af/ak/al approval/chain mismatch")
    # Rerun both existing fully signed original scientific audits,
    # rather than trusting copied trial-file numerics.
    original_all,ak_ledger=ak.audit()
    selected,humidity_ledger,edges=al.audit()
    require(len(ak_ledger)==8 and
            len(ak_ledger.loc[ak_ledger.site.eq("US-NR1")])==5 and
            len(humidity_ledger)==6 and len(edges)==7,
            "original 8/5 nonhumidity and 6 humidity audit counts unexpected")
    prev=pd.read_csv(must(AF/AF_NAME),dtype={"time":str},low_memory=False)
    trial=pd.read_csv(must(AL/AL_NAME),dtype={"time":str},low_memory=False)
    need_ak=original_all["US-NR1"]["selected"]
    require(len(prev)==EXPECTED_N and len(selected)==EXPECTED_N and
            len(trial)==EXPECTED_N and len(need_ak)==EXPECTED_N,
            "NR1 source not 490560 NOLEAP rows")
    require(prev.time.equals(selected.time) and trial.time.equals(selected.time)
            and need_ak.time.equals(selected.time) and
            list(prev.columns)==list(selected.columns) and
            list(trial.columns)==list(selected.columns),
            "original selected Stage12af/ak/al source timeline or schema not equal")
    # The exact original Stage12al complete trial should match
    # freshly recomputed derived science within safe machine precision.
    for field in selected.columns:
        if field=="time":continue
        a=pd.to_numeric(selected[field],errors="coerce").to_numpy(float)
        b=pd.to_numeric(trial[field],errors="coerce").to_numpy(float)
        require(np.allclose(a,b,rtol=1e-14,atol=1e-9,equal_nan=True),
                "recomputed scientific candidate differs from SEALED Stage12al "+field)

    # Confirm 2004 group exact values and original Stage12ak candidate
    # (including native source QC2 and flanking original-source QC2 evidence
    # already retested by original ak.audit()).
    keys=al.key(selected.time)
    require(keys.is_unique and keys.is_monotonic_increasing,
            "site native time duplicates or wrong order")
    locations={str(k):i for i,k in enumerate(keys)}
    actual_nonhumid=ak_ledger.loc[ak_ledger.site.eq("US-NR1")]
    authorized={(k,f) for k,f,_ in FIVE}
    require({(str(x.native_key),str(x.variable)) for x in actual_nonhumid.itertuples()}==authorized,
            "original Stage12ak signed five field/time values differ")
    for k,f,v in FIVE:
        i=locations[k]
        require(pd.isna(prev.iloc[i][f]) and
                valcmp(selected.iloc[i][f],v,1e-6) and
                valcmp(need_ak.iloc[i][f],v,1e-6),
                "2004 QC2 group original missing or interpolated pressure/longwave does not match "+k+" "+f)
    require(set(humidity_ledger.native_key.astype(str))==set(DATES6) and
            set(approval(decision_path)["groups"][0]["native_keys"])==set(DATES6),
            "2022 source humidity individual time/QC scientific group changed")
    vpd_ledger=[]
    for k in DATES6:
        i=locations[k]
        a=humidity_ledger.loc[humidity_ledger.native_key.astype(str).eq(k)]
        require(len(a)==1 and int(a.iloc[0].original_vpd_source_QC)==1,
                "original source VPD source QC1 record mismatch "+k)
        require(pd.isna(prev.VPD_USE.iloc[i]) and pd.isna(prev.QBOT.iloc[i]),
                "previous signed Stage12af source six humidity records not held "+k)
        v=float(selected.VPD_USE.iloc[i])
        q=float(selected.QBOT.iloc[i])
        require(valcmp(v,float(a.iloc[0].numerical_research_candidate_VPD_hPa),1e-9) and
                valcmp(q,float(a.iloc[0].numerical_research_candidate_QBOT_kgkg),1e-9)
                and 0<v<12 and 0<q<.08,
                "source humidity science VPD/QBOT changed "+k)
        vpd_ledger.append({"native_key":k,"VPD_USE_hPa":v,"QBOT_kgkg":q,
                           "original_VPD_F_QC":1,
                           "paired_ERA_RH_percent":float(a.iloc[0].paired_native_source_ERA_RH_pct)})
    require(max(float(x.trial_absolute_jump_hPa) for x in edges.itertuples())<4 and
            all(float(x.trial_absolute_jump_hPa)>=0 for x in edges.itertuples()),
            "source ERA humidity seven native-neighbor VPD steps invalid")
    require(int(selected.VPD_USE.isna().sum())==234 and
            int(selected.QBOT.isna().sum())==234 and
            int(selected[["TBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE"]].isna().any(axis=1).sum())==0,
            "new candidate incorrectly claims NR1 humidity completion or nonhumidity source gaps remain")
    # Compare against LAST separately operator-approved Stage12af NR1 source,
    # not the unapproved combined Stage12ak/12al sources. Only 17 expected
    # per-field 2014/2022 cells may change; everything else numeric equal.
    allowed={"VPD_USE":set(DATES6),"QBOT":set(DATES6),
             "PSRF":{k for k,f,v in FIVE if f=="PSRF"},
             "FLDS":{k for k,f,v in FIVE if f=="FLDS"}}
    diff_counts={}
    for field in selected.columns:
        if field=="time":continue
        before=pd.to_numeric(prev[field],errors="coerce").to_numpy(float)
        after=pd.to_numeric(selected[field],errors="coerce").to_numpy(float)
        changed=~np.isclose(before,after,rtol=0,atol=1e-9,equal_nan=True)
        actual=set(keys[changed])
        if field in allowed:
            require(actual==allowed[field],
                    "unapproved target field/time delta vs prior approved Stage12af: "+field)
            diff_counts[field]=len(actual)
        else:
            require(not actual,
                    "unapproved original other model field changed vs prior Stage12af: "+field)
    require(diff_counts=={"VPD_USE":6,"QBOT":6,"PSRF":3,"FLDS":2},
            "exact source field delta counts unexpectedly changed")
    report={
      "version":VERSION,"site":"US-NR1",
      "prior_Stage12af_approved_source_SHA256":sha(AF/AF_NAME),
      "original_Stage12ak_NR1_recomputed_source_data_signed":True,
      "original_Stage12al_NR1_recomputed_source_data_signed":True,
      "original_Stage12ak_science_receipt_SHA256":sha(AK/"stage12ak_research_proposal_SHA_receipt.json"),
      "original_Stage12al_science_receipt_SHA256":sha(AL/"stage12al_NR1_six_ERA_RH_science_only_SHA_receipt.json"),
      "operator_science_decision_SHA256":sha(decision_path),
      "native_rows":len(selected),"NR1_2004_nonhumidity_approved_field_edits":5,
      "NR1_2022_approved_humidity_native_rows":6,
      "NR1_original_2022_approved_site_temperatures_preserved":True,
      "original_other_US_NR1_source_times_unchanged":True,
      "NO_US_Kon_files_written":True,
      "actual_model_field_value_changes_vs_original_Stage12af":diff_counts,
      "seven_2022_native_humidity_jumps_max_hPa":
          max(float(x.trial_absolute_jump_hPa) for x in edges.itertuples()),
      "still_missing_NR1_VPD_and_QBOT_native_rows":234,
      "reanalysis_RH_not_independent_site_measurement":True,
      "postv5_approved":False,"DATM_ready":False,"spinup_authorized":False,
      "slurm_jobs_submitted":False,
      "science_state":"APPROVED_GROUP_SCIENCE_REPRODUCED_NOT_PRODUCTION_RELEASED"
    }
    return prev,selected,pd.DataFrame(vpd_ledger),actual_nonhumid,edges,report

def apply(approval_path,prev,selected,humid,nonhumid,edges,report):
    # NEW file only; recheck approved value identity and full-source delta
    # before and after on-disk CSV readback.
    folder=ROOT/"science_trials"/(
      "stage13p_NR1_6ERA_RH_5_PSRF_FLDS_OPERATOR_APPROVED_"+
      datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    folder.mkdir(parents=True,exist_ok=False)
    incomplete=folder/"INCOMPLETE_SOURCE_EXPORT_DO_NOT_USE"
    incomplete.write_text("No model/DATM release. Original/inputs not modified.\n")
    selected.to_csv(folder/OUT,index=False,float_format="%.17g")
    reopened=pd.read_csv(must(folder/OUT),dtype={"time":str},low_memory=False)
    require(len(reopened)==EXPECTED_N and list(reopened.columns)==list(prev.columns)
            and reopened.time.equals(prev.time),
            "exported full NR1 490560-row time/schema changed")
    for field in selected.columns:
        if field=="time":continue
        actual=pd.to_numeric(reopened[field],errors="coerce").to_numpy(float)
        expected=pd.to_numeric(selected[field],errors="coerce").to_numpy(float)
        require(np.allclose(actual,expected,atol=1e-9,rtol=1e-14,equal_nan=True),
                "full 490560-row candidate CSV roundtrip altered model field "+field)
    humid_name="exact_six_20220910_paired_source_ERA_RH_VPD_QBOT.csv"
    nonhumid_name="exact_five_20041203_source_QC2_PSRF_FLDS.csv"
    edges_name="seven_20220910_original_source_adjacent_VPD_edges.csv"
    report_name="stage13p_signed_science_summary.json"
    humid.to_csv(folder/humid_name,index=False,float_format="%.17g")
    nonhumid.to_csv(folder/nonhumid_name,index=False,float_format="%.17g")
    edges.to_csv(folder/edges_name,index=False,float_format="%.17g")
    (folder/report_name).write_text(json.dumps(report,indent=2)+"\n")
    marker="NOT_POSTV5_DATM_AD400_SLURM_READY"
    (folder/marker).write_text(
      "Exactly 6 original 2022 source-native paired ERA RH humidity rows"
      " and 5 original 2004 QC2 pressure/longwave model fields selected"
      " from SHA-signed Stage12af/ak/al, keeping three earlier operator"
      " approved TA interpolations. All other original NR1 model source"
      " fields/times unchanged. No original raw FLUXMET, ERA, US-Kon,"
      " PFT, ZBOT, Slurm, DATM or model configuration touched."
      " 234 original NR1 VPD/QBOT native rows remain missing.\n")
    files=[OUT,humid_name,nonhumid_name,edges_name,report_name,marker]
    receipt={"version":VERSION,
       "operator_decision_SHA256":sha(approval_path),
       "source_last_approved_Stage12af_SHA256":sha(AF/AF_NAME),
       "original_Stage12ak_SHA_receipt":sha(AK/"stage12ak_research_proposal_SHA_receipt.json"),
       "original_Stage12al_SHA_receipt":sha(AL/"stage12al_NR1_six_ERA_RH_science_only_SHA_receipt.json"),
       "native_rows":EXPECTED_N,
       "approved_exact_site_only":"US-NR1","model_field_change_counts":
          report["actual_model_field_value_changes_vs_original_Stage12af"],
       "remaining_NR1_humidity_native_source_gaps":234,
       "Postv5":False,"DATM":False,"AD400":False,"Slurm":False,
       "files_SHA256":{name:sha(folder/name) for name in files}}
    (folder/"stage13p_operator_approved_NR1_SHA_receipt.json").write_text(
      json.dumps(receipt,indent=2)+"\n")
    incomplete.unlink()
    require(sha(AF/AF_NAME)==report["prior_Stage12af_approved_source_SHA256"],
            "original user-approved Stage12af changed after export")
    print("STAGE13P TWO SOURCE GROUPS PASS; NR1 6 HUMIDITY + 5 NONHUMIDITY FIELDS SUCCESS",folder,flush=True)
    print("STAGE13P ORIGINAL 490560 NOLEAP ROWS; ACTUAL CHANGES",report["actual_model_field_value_changes_vs_original_Stage12af"],flush=True)
    print("STAGE13P NR1 STILL HAS 234 VPD/QBOT SCIENCE HOLDS; NO MODEL / DATM / KON CHANGES",flush=True)

def main():
    p=argparse.ArgumentParser()
    group=p.add_mutually_exclusive_group(required=True)
    for cmd in ("self-test","check","apply"):group.add_argument("--"+cmd,action="store_true")
    p.add_argument("--approval",type=Path)
    args=p.parse_args()
    print("STAGE13P NR1 APPROVED TWO SOURCE GROUPS | "+VERSION,flush=True)
    selftest()
    if args.self_test:return
    if args.approval is None:p.error("--approval Stage13p exact user decision JSON required")
    previous,new,humid,nonhumid,edges,summary=audit(args.approval)
    print("STAGE13P SCIENCE",json.dumps(summary,indent=2),flush=True)
    print("STAGE13P SIX REANALYSIS RH",humid.to_string(index=False),flush=True)
    print("STAGE13P FIVE NONHUMIDITY",nonhumid.to_string(index=False),flush=True)
    if args.check:
        print("STAGE13P READONLY CHECK PASS | 6 source RH, five QC2 PSRF/FLDS, 17 exact field changes; NO WRITES",flush=True)
        return
    apply(args.approval,previous,new,humid,nonhumid,edges,summary)

if __name__=="__main__":
    try: main()
    except Exception as exc:
        print("STAGE13P SCIENCE STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

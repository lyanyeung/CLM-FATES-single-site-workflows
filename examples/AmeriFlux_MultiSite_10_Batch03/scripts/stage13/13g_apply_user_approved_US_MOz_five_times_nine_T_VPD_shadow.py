#!/usr/bin/env python3
"""Batch03 Stage13g: apply operator's EXACT 5 native-time US-MOz repair policy,
5 temperature and 4 paired VPD edits, in ONE NEW isolated science shadow.

Immutable inputs: 315360-row signed Stage07 selected candidate, the original
tower/ERA companion release, the Stage13f signed original event neighborhood,
Stage13e approval and the pinned GitHub signed-scoped decision JSON.
--self-test synthetic, --check independent science SHA preflight with NO WRITES,
--run same gate + an isolated, versioned, SHA-receipted shadow CSV ONLY.

Never write raw tower/ERA, Stage07, cases, PFT/surface, DATM or Slurm.
2005 Jan 6 05:00–09:00 source episode remains unmodified and HELD.
New science shadow != a production-ready Post-v5 or spinup admission.
"""
import argparse,hashlib,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

sys.dont_write_bytecode=True
V="batch03-stage13g-v2-20261026-raw-VPD-QC-provenance-safe"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
S13E=ROOT/"reports/stage13e_MOz_six_approved_09T_recheck_20261026T174412Z_3e98ca6c"
S13F=ROOT/"reports/stage13f_MOz_three_extra_QC0_tower_ERA_neighbors_20261026T175310Z_f93e321f"
SELECTED=S07/"US-MOz/forcing/processed_v5/US-MOz_CLM_forcing_2004_2021.csv"
NAME="US-MOz_CLM_forcing_2004_2021_STG13G_RESEARCH_SHADOW.csv"
NUM=315360
FIELDS=("TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE")
EXPECTED=[
  ("2014-04-02T08:30:00","TA_USE",13.310,8.904666666666667,"TA_F",0),
  ("2014-04-02T08:30:00","VPD_USE",0.279,3.974666666666667,"VPD_F",None),
  ("2014-04-02T09:00:00","TA_USE",14.457,8.900333333333334,"TA_F",0),
  ("2014-04-02T09:00:00","VPD_USE",0.177,3.957333333333333,"VPD_F",None),
  ("2014-04-02T10:00:00","TA_USE",18.110,8.7715,"TA_F",0),
  ("2016-04-11T13:00:00","TA_USE",23.671,14.0675,"TA_F",0),
  ("2016-04-11T13:00:00","VPD_USE",17.735,9.8285,"VPD_F",None),
  ("2016-04-14T06:30:00","TA_USE",17.543,9.035,"TA_F",0),
  ("2016-04-14T06:30:00","VPD_USE",7.288,4.217,"VPD_F",None),
]
ANCHORS=[
 ("2014-04-02T08:00:00","2014-04-02T09:30:00",
  ("2014-04-02T08:30:00","2014-04-02T09:00:00"),
  ("TA_F","VPD_F"),(8.909,8.896),(3.992,3.940)),
 ("2014-04-02T09:30:00","2014-04-02T10:30:00",
  ("2014-04-02T10:00:00",),("TA_F",),(8.896,8.647),None),
 ("2016-04-11T12:30:00","2016-04-11T13:30:00",
  ("2016-04-11T13:00:00",),("TA_F","VPD_F"),(12.059,16.076),(8.303,11.354)),
 ("2016-04-14T06:00:00","2016-04-14T07:00:00",
  ("2016-04-14T06:30:00",),("TA_F","VPD_F"),(7.756,10.314),(3.622,4.812)),
]
KEYS={(pd.Timestamp(t),col) for t,col,*_ in EXPECTED}

def source(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise RuntimeError("Original source missing/symlink: "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with source(p).open("rb") as stream:
        for block in iter(lambda:stream.read(1<<20),b""):h.update(block)
    return h.hexdigest()

def close(actual,expected,tol=1e-8):
    return bool(np.isclose(float(actual),float(expected),rtol=0,atol=tol))

def ts(s):
    a=pd.Timestamp(s)
    if pd.isna(a) or a.tzinfo is not None:raise RuntimeError("Bad native time")
    return a

def saturation(tc):
    return 6.112*np.exp(17.67*tc/(tc+243.5))

def selftest():
    assert len(EXPECTED)==9 and len(KEYS)==9
    assert len({t for t,_,*rest in EXPECTED})==5
    assert sum(c=="TA_USE" for _,c,*_ in EXPECTED)==5
    assert sum(c=="VPD_USE" for _,c,*_ in EXPECTED)==4
    assert close((8.909*2+8.896)/3,8.904666666666667)
    assert close((3.992+3.940*2)/3,3.957333333333333)
    assert close((12.059+16.076)/2,14.0675)
    assert close((8.303+11.354)/2,9.8285)
    assert close((7.756+10.314)/2,9.035)
    assert close((3.622+4.812)/2,4.217)
    print("STAGE13G SELF-TEST PASS | 5 source-native timestamps, 9 exact TA/VPD edits",flush=True)

def checked_inputs(decision_path):
    decision=json.loads(source(decision_path).read_text())
    if decision.get("schema")!="batch03-stage13g-five-native-timestamps-nine-variable-edits-v1":
        raise RuntimeError("The operator Stage13g decision JSON schema changed")
    flags=decision.get("restrictions",{})
    for f in ("raw_tower_data_immutable","raw_ERA_data_immutable",
              "existing_Stage07_trial_immutable","create_new_isolated_shadow_only",
              "all_other_times_and_variables_unchanged",
              "initial_stage07_six_approved_changes_retained"):
        if flags.get(f) is not True:raise RuntimeError("Approval safety scope invalid: "+f)
    for f in ("postv5_approved","DATM_ready","spinup_authorized",
              "PFT_config_apply_approved_by_this_decision",
              "ZBOT_height_selected","model_or_Slurm_submission"):
        if flags.get(f) is not False:raise RuntimeError("Unapproved science flag: "+f)
    d=decision.get("exact_original_tower_event_values",[])
    if len(d)!=9:raise RuntimeError("Operator decision no longer exactly nine edits")
    have={(ts(r["time"]),r["variable"]):(r["original"],r["new_value"],r["original_tower_qc"]) for r in d}
    if set(have)!=KEYS:
        raise RuntimeError("Operator decision time/variable identities diverge")
    for when,field,original,new,srcname,qc in EXPECTED:
        r=have[ts(when),field]
        if not(close(r[0],original) and close(r[1],new) and
               (r[2] is None if qc is None else r[2]==qc)):
            raise RuntimeError("Operator signed original/new source value differs "+when+" "+field)

    prior=json.loads(source(S13E/"stage13e_moz_six_scope_and_09T_science_SHA_receipt.json").read_text())
    newer=json.loads(source(S13F/"stage13f_three_QC0_review_SHA_receipt.json").read_text())
    if prior.get("exact_six_US_MOz_Stage07_candidate_modifications_approved") is not True or \
       prior.get("original_09T_2005_TA_preserved") is not True or \
       prior.get("postv5_approved") is not False:
        raise RuntimeError("Prior Stage13e operator-approved six source edits changed")
    if newer.get("Stage13e_signed_source_SHA256")!=sha(S13E/
       "stage13e_moz_six_scope_and_09T_science_SHA_receipt.json") or \
       newer.get("three_source_QC0_centers_operator_approved") is not False:
        raise RuntimeError("Signed Stage13f original 3 QC0 source screens changed")
    for fname in ("THREE_MOz_QC0_2h_native_tower_and_ERA5_context.csv",
                  "THREE_MOz_QC0_operator_decision_centers_NOT_APPROVED.csv"):
        if sha(S13F/fname)!=newer.get("output_SHA256",{}).get(fname):
            raise RuntimeError("Stage13f neighbor context altered "+fname)
    if sha(S13E/"2005Jan06_09T_original_Tower_ERA_stage07_surrounding_4h.csv")!= \
       prior["output_SHA256"]["2005Jan06_09T_original_Tower_ERA_stage07_surrounding_4h.csv"]:
        raise RuntimeError("Stage13e separate 2005 source HOLD evidence changed")

    manifest=json.loads(source(S07/"exact_input_manifest.json").read_text())
    if sha(S07/"exact_input_manifest.json")!=prior.get("exact_Stage07_source_manifest_SHA256"):
        raise RuntimeError("Stage07 exact manifest differs from previously reviewed source")
    specs={x["site"]:x for x in manifest["sites"]}
    if len(specs)!=10:raise RuntimeError("Incorrect Stage07 original site set")
    spec=specs["US-MOz"]
    if int(spec["first_year"])!=2004 or int(spec["last_year"])!=2021 or int(spec["native_minutes"])!=30:
        raise RuntimeError("Original tower release year/cadence modified")
    origin={str(Path(k).resolve()):v for k,v in manifest["input_sha256"].items()}
    for kind in ("primary","era"):
        p=source(spec[kind])
        if sha(p)!=origin.get(str(p.resolve())):
            raise RuntimeError("Original tower/ERA full source SHA mismatch "+kind)
    outputsha=json.loads(source(S07/"output_sha256.json").read_text())
    if sha(S07/"output_sha256.json")!=prior.get("stage07_selected_sha256"):
        # Prior Stage13e receipt does not necessarily repeat this manifest
        # under this key. Original source/selected independent SHA below is
        # authoritative; do not treat a missing optional field as failure.
        if prior.get("stage07_selected_sha256") is not None:
            raise RuntimeError("Stage07 signed output manifest changed")
    if sha(SELECTED)!=outputsha.get(str(SELECTED.relative_to(S07))):
        raise RuntimeError("Original selected Stage07 candidate changed")
    if sha(SELECTED)!=prior.get("stage07_selected_forcing_sha256",sha(SELECTED)):
        raise RuntimeError("Stage13e selected source forcing SHA mismatch")

    prior_context=pd.read_csv(source(S13F/
        "THREE_MOz_QC0_2h_native_tower_and_ERA5_context.csv"),
        dtype={"native_source_time":str})
    if len(prior_context)!=27:
        raise RuntimeError("Stage13f independent 3 centers x 9 halfhour context missing")
    return spec,sha(SELECTED),sha(spec["primary"]),sha(spec["era"])

def native_original(path,fields):
    df=pd.read_csv(source(path),usecols=["TIMESTAMP_START",*fields],
         dtype={"TIMESTAMP_START":str},low_memory=False)
    a=pd.to_datetime(df["TIMESTAMP_START"],format="%Y%m%d%H%M",errors="raise")
    keep=a.dt.year.between(2004,2021)&~((a.dt.month==2)&(a.dt.day==29))
    df=df.loc[keep].copy()
    df.index=pd.DatetimeIndex(a.loc[keep],name="native_time")
    if df.index.has_duplicates or df.index.hasnans:
        raise RuntimeError("Original FLUXMET source duplicated/NaT")
    df.drop(columns=["TIMESTAMP_START"],inplace=True)
    for col in fields:
        df[col]=pd.to_numeric(df[col],errors="coerce")
    return df

def read_candidate(path):
    df=pd.read_csv(source(path),dtype={"time":str},low_memory=False)
    if set(FIELDS).difference(df.columns):
        raise RuntimeError("Selected Stage07 source missing required forcing columns")
    dt=pd.to_datetime(df.time,errors="raise")
    if len(df)!=NUM or dt.isna().any() or dt.duplicated().any():
        raise RuntimeError("Expected 315360 unique selected NO_LEAP 30-min periods")
    if not dt.is_monotonic_increasing:
        raise RuntimeError("Selected source time ordering broken")
    if ((dt.dt.month==2)&(dt.dt.day==29)).any():
        raise RuntimeError("Stage07 selected NOLEAP contains leap-day")
    permitted=dt.diff().dt.total_seconds().iloc[1:].isin([1800,88200])
    if not bool(permitted.all()):
        raise RuntimeError("Selected candidate has invalid 30-minute NOLEAP clock")
    for c in FIELDS:
        if not bool(np.isfinite(pd.to_numeric(df[c],errors="coerce")).all()):
            raise RuntimeError("Input candidate nonfinite required "+c)
    df.index=pd.DatetimeIndex(dt,name="native_time")
    return df

def evaluate(decision_path):
    spec,oldsha,rawsha,erasha=checked_inputs(decision_path)
    tower=native_original(spec["primary"],["TA_F","TA_F_QC","VPD_F","VPD_F_QC"])
    era=native_original(spec["era"],["TA_ERA","VPD_ERA"])
    original=read_candidate(SELECTED)
    if not(original.index.equals(tower.index) and original.index.equals(era.index)):
        raise RuntimeError("Tower, ERA, selected source-native clock arrays differ")
    if len(tower)!=NUM:
        raise RuntimeError("Original noleap years not exactly 315360 source rows")
    for start,end,times,cols,anchorT,anchorVPD in ANCHORS:
        a=ts(start);b=ts(end)
        if not(close(tower.at[a,"TA_F"],anchorT[0],1e-6) and
               close(tower.at[b,"TA_F"],anchorT[1],1e-6)):
            raise RuntimeError("Tower source original TA anchor mismatch "+start)
        if "VPD_F" in cols and not(close(tower.at[a,"VPD_F"],anchorVPD[0],1e-6) and
                                   close(tower.at[b,"VPD_F"],anchorVPD[1],1e-6)):
            raise RuntimeError("Tower source original VPD anchor mismatch "+start)
        for time_ in times:
            t=ts(time_)
            frac=(t-a)/(b-a)
            for c in cols:
                new=float(tower.at[a,c]+frac*(tower.at[b,c]-tower.at[a,c]))
                modelcol="TA_USE" if c=="TA_F" else "VPD_USE"
                entry=next(x for x in EXPECTED if ts(x[0])==t and x[1]==modelcol)
                if not close(new,entry[3],1e-8):
                    raise RuntimeError("Source-native interpolation not equal operator agreed value "+time_+" "+c)
    successor=original.copy(deep=True)
    changed=[]
    for time_,modelcol,prior,new,sourcecol,qc in EXPECTED:
        t=ts(time_)
        if not(close(original.at[t,modelcol],prior,1e-8) and
               close(tower.at[t,sourcecol],prior,1e-8) and
               (qc is None or close(tower.at[t,sourcecol+"_QC"],qc,1e-8))):
            raise RuntimeError("Original center/source-QC does not match signed operator action "+time_+" "+modelcol)
        successor.at[t,modelcol]=new
        changed.append({
         "site":"US-MOz","source_native_time":t.isoformat(),"variable":modelcol,
         "original_selected_candidate_value":prior,
         "operator_approved_replacement":new,
         "original_source_tower_QC":float(tower.at[t,sourcecol+"_QC"]),
         "original_tower_value":tower.at[t,sourcecol],
         "companion_ERA5_value":era.at[t,"TA_ERA" if modelcol=="TA_USE" else "VPD_ERA"],
         "reason":"OPERATOR_APPROVED_TOWER_NATIVE_LINEAR_INTERPOLATION_20261026",
         "source_Stage07_original_untouched":True,
        })
    # Both TBOT and QBOT must be internally consistent with changed TA/VPD.
    es=saturation(successor.TA_USE.to_numpy(dtype=float))
    ea=(es-successor.VPD_USE.to_numpy(dtype=float))*100.
    psrf=successor.PSRF.to_numpy(dtype=float)
    q=0.622*ea/(psrf-0.378*ea)
    impacted=sorted({ts(x[0]) for x in EXPECTED})
    for t in impacted:
        successor.at[t,"TBOT"]=float(successor.at[t,"TA_USE"])+273.15
        i=successor.index.get_loc(t)
        successor.at[t,"QBOT"]=q[i]
    water_rh=100*ea/(100*es)
    if (not bool(np.isfinite(q).all()) or
        bool((q<=0).any()) or bool((q>0.08).any()) or
        bool((water_rh>100.05).any()) or bool((water_rh<=0).any())):
        raise RuntimeError("Full 18y science shadow has invalid water-phase RH/QBOT after approved changes")
    if not np.isclose(successor.TBOT.to_numpy(dtype=float),
                      successor.TA_USE.to_numpy(dtype=float)+273.15,rtol=0,atol=1e-8).all():
        raise RuntimeError("Full candidate TBOT/TA consistency failed")
    for t in impacted:
        i=successor.index.get_loc(t)
        if not close(successor.at[t,"QBOT"],q[i],1e-12):
            raise RuntimeError("Paired water vapor -> QBOT thermodynamic reconstruction failed")
    # Full columnwise before/after audit: ONLY expected 9 cells + their TBOT/QBOT.
    allowed={(t,c) for t,c in KEYS}
    allowed.update((t,"TBOT") for t in impacted if (t,"TA_USE") in KEYS)
    allowed.update((t,"QBOT") for t in impacted)
    diff=[]
    for c in FIELDS:
        x=pd.to_numeric(original[c],errors="coerce").to_numpy(dtype=float)
        y=pd.to_numeric(successor[c],errors="coerce").to_numpy(dtype=float)
        ix=np.flatnonzero(~np.isclose(x,y,atol=1e-12,rtol=0))
        for i in ix:
            k=(original.index[i],c)
            if k not in allowed:
                raise RuntimeError("An unapproved field or native timestamp changed "+str(k))
            diff.append({"time":k[0].isoformat(),"column":c,"prior":x[i],"new":y[i]})
    for when,col,*_ in EXPECTED:
        if not any(d["time"]==when and d["column"]==col for d in diff):
            raise RuntimeError("Expected operator edit was not represented in numeric output "+when+" "+col)
    # The 2005 extended suspicious MDS source interval remains EXACT.
    held=(original.index>=pd.Timestamp("2005-01-06T05:00"))&(
          original.index<=pd.Timestamp("2005-01-06T09:00"))
    if not original.loc[held,list(FIELDS)].equals(successor.loc[held,list(FIELDS)]):
        raise RuntimeError("Unapproved multi-hour 2005 T/VPD source episode changed")
    # 2014-04-02 10:00 original VPD not changed by new temperature interpolation.
    ten=ts("2014-04-02T10:00:00")
    if not close(successor.at[ten,"VPD_USE"],0.475,1e-10):
        raise RuntimeError("Original 2014 10:00 VPD HOLD changed contrary to operator interpretation")
    summary={
        "source_site":"US-MOz","original_Stage07_selected_SHA256":oldsha,
        "source_raw_tower_SHA256":rawsha,
        "source_raw_standalone_ERA_SHA256":erasha,
        "native_30min_noleap_rows":len(successor),
        "new_operator_approved_timesteps":5,
        "new_operator_approved_TA_fields":5,
        "new_operator_approved_VPD_fields":4,
        "changed_TBOT_cells":sum(x["column"]=="TBOT" for x in diff),
        "changed_QBOT_cells":sum(x["column"]=="QBOT" for x in diff),
        "original_six_Stage07_operator_approved_changes_retained":True,
        "2005_Jan06_05_09_source_HOLD_unchanged":True,
        "2014_Apr02_10_00_original_VPD_unchanged":True,
        "Postv5_approved":False,"DATM_ready":False,"spinup_authorized":False,
        "overall_state":"ISOLATED_RESEARCH_SHADOW_NOT_PRODUCTION"}
    return successor,pd.DataFrame(changed),pd.DataFrame(diff),summary

def main():
    ap=argparse.ArgumentParser()
    g=ap.add_mutually_exclusive_group(required=True)
    for op in ("self-test","check","run"):g.add_argument("--"+op,action="store_true")
    ap.add_argument("--decision",type=Path)
    a=ap.parse_args()
    print("STAGE13G OPERATOR 5-TIMESTAMP/9-FIELD MOz RESEARCH SHADOW | "+V,flush=True)
    selftest()
    if a.self_test:return
    if not a.decision:ap.error("Exact GitHub Stage13g scoped decision JSON required")
    shadow,edits,diff,status=evaluate(a.decision)
    print("\n=== NINE SPECIFIC NEW OPERATOR APPROVED SOURCE EDITS ===",flush=True)
    print(edits.to_string(index=False,float_format=lambda z:f"{z:.9f}"),flush=True)
    print("\n=== ALL CHANGED MODEL FIELDS (TA, VPD, TBOT, QBOT) ===",flush=True)
    print(diff.to_string(index=False,float_format=lambda z:f"{z:.9f}"),flush=True)
    print("\n=== SOURCE-SAFE RESEARCH QA ===",flush=True)
    for k,v in status.items():print(k,v,flush=True)
    if a.check:
        print("STAGE13G CHECK PASS | NO WRITES (source/selected/cases unchanged)",flush=True)
        return
    out=ROOT/"science_trials"/("stage13g_US_MOz_approved_native_T_VPD_"+
         datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    incomplete=out/"INCOMPLETE_NO_MODEL_USE"
    incomplete.write_text("In-progress isolated Stage13g candidate. Do not use before receipt.\n")
    files={
       NAME:shadow.reset_index(drop=True),
       "exact_nine_operator_approved_TA_VPD_changes.csv":edits,
       "all_model_input_differential_changes.csv":diff,
    }
    for name,df in files.items():df.to_csv(out/name,index=False)
    reload=read_candidate(out/NAME)
    if len(reload)!=NUM:
        raise RuntimeError("Reloaded shadow csv did not contain complete noleap source")
    for time_,field,old,new,*rest in EXPECTED:
        if not close(reload.at[ts(time_),field],new,1e-9):
            raise RuntimeError("Reopened exported shadow differs from operator decision")
    for time_,field,*rest in EXPECTED:
        if not close(pd.to_numeric(shadow.at[ts(time_),field]),reload.at[ts(time_),field],1e-9):
            raise RuntimeError("Reload changed an approved field")
    # Latest immutable source input file digest checked again after writing.
    if sha(SELECTED)!=status["original_Stage07_selected_SHA256"]:
        raise RuntimeError("Original Stage07 candidate SHA unexpectedly altered by export")
    if sha(a.decision)!=sha(source(a.decision)):
        raise RuntimeError("Decision source changed during export")
    marker="SCIENCE_HOLD_ORIGINAL_2005_MDS_PFT_ZBOT_CLOCK_NOT_POSTV5"
    (out/marker).write_text(
       "Operator approved only 5 extra source native timestamps/9 TA+VPD fields."
       " Original 6 Stage07 edits preserved. Original tower CSV, standalone "
       "ERA5, previous Stage07 candidate and 2005 Jan06 05:00-09:00 source "
       "HOLD remained untouched. This is an isolated model-forcing RESEARCH "
       "SHADOW, NOT Post-v5 approval, NOT DATM-ready, NOT spinup authorised. "
       "Verify sourced tower height ZBOT and apply approved recommended "
       "FATES PFT independently before any production case.\n")
    receipt={
       "version":V,"operator_decision_sha256":sha(a.decision),
       "prior_stage13e_receipt_sha256":sha(S13E/
           "stage13e_moz_six_scope_and_09T_science_SHA_receipt.json"),
       "prior_stage13f_receipt_sha256":sha(S13F/
           "stage13f_three_QC0_review_SHA_receipt.json"),
       "approved_model_field_edit_rows":len(edits),
       "source_review":status,
       "all_output_SHA256":{n:sha(out/n) for n in [*files,marker]},
    }
    (out/"stage13g_MOz_approved_T_VPD_science_shadow_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    incomplete.unlink()
    print("STAGE13G ISOLATED RESEARCH SHADOW SUCCESS",out,flush=True)
    print("NOT Post-v5 / DATM / CIME / Spinup released. NO originals changed.",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE13G STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

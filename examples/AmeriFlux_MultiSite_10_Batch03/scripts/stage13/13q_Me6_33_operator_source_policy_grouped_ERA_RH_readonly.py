#!/usr/bin/env python3
"""Stage13q: US-Me6 33 previously method-approved humidity VPD/QBOT HOLDs.

Source-native companion ERA RH at unchanged measured tower/site temperature.
This Stage is READ-ONLY: it groups all 33 original Stage12g source-native
HOLD positions into contiguous 30min episodes and rigorously audits paired
source ERA humidity, original QC0 tower TA and QC1 VPD provenance, physical
water RH/QBOT and full episode edge continuity. It uses the signed Stage12ae
75-case x 5 native record evidence and immutable Stage12ac site input.

No new forcing, no original file changes, no US-Kon or NR1 changes, no model.
--self-test: source-free synthetic tests
--check: source-pinned group audit, stdout only
--run: same with SHA-sealed *READ-ONLY EVIDENCE* CSV and JSON, no forcing
"""
import argparse,hashlib,json,sys,traceback
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VER="batch03-stage13q-v1-20261026-Me6-33-original-ERA-RH-episodes-readonly"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AE=R/"reports/stage12ae_all_42_pending_original_tower_ERA_ERA5Land_neighbors_20261026T011243Z_c5cc64fe"
AC=R/"science_trials/stage12ac_USER_APPROVED_Me6_20170704_0600_0800_ERA_RH_20261025T232237Z_534eb248"
G=R/"science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f"
S=R/"qcv5_native_trial_20261022T024559Z_36c46e58"
AE_CONTEXT="75_high_priority_cases_x_five_native_halfhours_all_three_source_comparisons.csv"
AE_SUMMARY="75_cases_center_prev_next_source_value_jumps.csv"
AE_RECEIPT="stage12ae_review_only_SHA_receipt.json"
AC_FILE="US-Me6_STAGE12AC_USER_APPROVED_OVERLAY_INCOMPLETE_NOLEAP.csv"
AC_REC="stage12ac_user_approved_5HH_SHA_receipt.json"
G_REC="stage12g_research_only_sha_receipt.json"
G_LEDGER="2810_original_missing_year_source_review_after_stage12g.csv"
HH=pd.Timedelta(minutes=30)
LIMIT=4.
SOURCE_T_MAX=8.
SITE="US-Me6"

def must(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise RuntimeError("Missing signed original file or unexpected symlink "+str(p))
    return p

def sha(p):
    h=hashlib.sha256()
    with must(p).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()

def require(c,msg):
    if not bool(c):
        raise RuntimeError("STAGE13Q SOURCE AUDIT STOP: "+msg)

def key(s):
    return s.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)

def sat(T):
    return 6.112*np.exp(17.67*float(T)/(float(T)+243.5))

def derive(T,p,eraT,eraV):
    vals=[T,p,eraT,eraV]
    if not np.isfinite(vals).all() or not (50000.<float(p)<110000.):
        return float("nan"),float("nan"),float("nan"),"INVALID_T_P_ERA"
    esera=sat(eraT)
    rh=100*(1-float(eraV)/esera)
    es=sat(T)
    v=es*(1-rh/100)
    ea=(es-v)*100
    q=.622*ea/(float(p)-.378*ea)
    good=(0<rh<100 and 0<v<es and 0<q<.08 and abs(float(T)-float(eraT))<=SOURCE_T_MAX)
    return v,q,rh,("SOURCE_PHYSICS_PASS" if good else "SOURCE_PHYSICS_HOLD")

def selftest():
    assert pd.Timestamp("2017-07-04 06:00")+HH==pd.Timestamp("2017-07-04 06:30")
    v,q,r,why=derive(1.24,70000,1.78,2.01)
    assert why=="SOURCE_PHYSICS_PASS" and 0<r<100 and 0<q<.08
    _,_,_,why=derive(1.24,70000,1.78,40)
    assert why=="SOURCE_PHYSICS_HOLD"
    assert LIMIT==4 and SITE=="US-Me6"
    print("STAGE13Q SELF-TEST PASS | 33 exact original Me6 center science groups; original paired ERA and QC0 source, NO FORCING WRITES",flush=True)

def signed_sources():
    a=json.loads(must(AE/AE_RECEIPT).read_text())
    b=json.loads(must(AC/AC_REC).read_text())
    g=json.loads(must(G/G_REC).read_text())
    require(a.get("version")=="batch03-stage12ae-v1-20261026-42-pending-33-approved-source-context" and
            a.get("pending_human_review")==42 and
            a.get("Me6_previous_source_policy_approved_awaiting_application")==33 and
            a.get("Postv5_approved")==0 and a.get("DATM_ready")==0 and
            a.get("stage12ac_receipt_SHA256")==sha(AC/AC_REC) and
            a.get("source_G_receipt_SHA256")==sha(G/G_REC),
            "Stage12ae original signed 75-center science report incorrect")
    for name,digest in a.get("output_SHA256",{}).items():
        require("/" not in name and sha(AE/name)==digest,
                "Stage12ae SHA report altered "+name)
    require(a.get("output_SHA256",{}).get(AE_CONTEXT)==sha(AE/AE_CONTEXT) and
            a.get("output_SHA256",{}).get(AE_SUMMARY)==sha(AE/AE_SUMMARY),
            "Stage12ae native evidence incomplete")
    require(b.get("version")=="batch03-stage12ac-v1-20261025-operator-approved-five-HH-ERA-RH" and
            b.get("two_old_G_HOLDs_released_in_NEW_derived_overlay_only") is True and
            b.get("Postv5_approved")==0 and b.get("DATM_ready")==0 and
            b.get("output_SHA256",{}).get(AC_FILE)==sha(AC/AC_FILE),
            "Stage12ac existing approved five HH source changed")
    require(g.get("original_233_physics_holds_untouched") is True and
            g.get("output_sha256",{}).get(G_LEDGER)==sha(G/G_LEDGER),
            "Original Stage12g protection or missing year source changed")
    manifest=json.loads(must(S/"exact_input_manifest.json").read_text())
    sites=[x for x in manifest["sites"] if x.get("site")==SITE]
    require(len(sites)==1 and int(sites[0]["native_minutes"])==30,
            "Original Stage07 Me6 halfhour provenance/clock changed")
    spec=sites[0]
    expected={str(Path(x).resolve()):y for x,y in manifest["input_sha256"].items()}
    for t in ("primary","era"):
        p=must(spec[t])
        require(sha(p)==expected.get(str(p.resolve())),
                "Original tower/ERA FLUXNET immutable source SHA changed "+t)
    return spec

def episodes(ts):
    ts=sorted(pd.Timestamp(x) for x in ts)
    groups=[]
    for t in ts:
        if not groups or t-groups[-1][-1]!=HH:groups.append([t])
        else:groups[-1].append(t)
    return groups

def audit():
    spec=signed_sources()
    context=pd.read_csv(must(AE/AE_CONTEXT),
        dtype={"TIMESTAMP_START":str,"center_native_key":str,"site":str},low_memory=False)
    summary=pd.read_csv(must(AE/AE_SUMMARY),
        dtype={"native_key":str,"site":str},low_memory=False)
    srcsummary=summary.loc[
        summary.site.eq(SITE)&
        summary.audit_class.eq("ME6_POLICY_USER_APPROVED_NOT_YET_APPLIED_33")].copy()
    centers=context.loc[context.site.eq(SITE)&
        context.relative_halfhours.eq(0)&
        context.audit_class.eq("ME6_POLICY_USER_APPROVED_NOT_YET_APPLIED_33")].copy()
    require(len(srcsummary)==33 and len(centers)==33 and
            centers.center_native_key.is_unique and
            set(centers.center_native_key)==set(srcsummary.native_key),
            "Exactly 33 previously method-approved Me6 original science holds changed")
    ledger=pd.read_csv(must(G/G_LEDGER),dtype={"site":str,"native_key":str},low_memory=False)
    relevant=ledger.loc[ledger.site.eq(SITE)&ledger.reason.eq("HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA")]
    target=set(centers.center_native_key)
    require(len(target)==33 and target.issubset(set(relevant.native_key)) and
            not target.intersection({"201707040700","201707040730"}),
            "Stage12ac prior 2017 five records collide with 33 science group")
    forcing=pd.read_csv(must(AC/AC_FILE),dtype={"time":str},low_memory=False)
    allkeys=key(forcing.time)
    require(len(forcing)>100000 and allkeys.is_unique and
            allkeys.is_monotonic_increasing and target.issubset(set(allkeys)),
            "Stage12ac original full Me6 NOLEAP chronology altered")
    forcing.index=pd.DatetimeIndex(
        pd.to_datetime(allkeys,format="%Y%m%d%H%M",errors="raise"))
    context.index=pd.DatetimeIndex(
        pd.to_datetime(context.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise"))
    # Independently re-read original tower and paired ERA at all source centers
    # and immediate native before/after times and cross-check signed Stage12ae.
    wanted=set(target)
    for rawkey in target:
        t=pd.to_datetime(rawkey,format="%Y%m%d%H%M")
        wanted.update((t+dt).strftime("%Y%m%d%H%M") for dt in (-HH,HH))
    tower=pd.read_csv(must(spec["primary"]),dtype={"TIMESTAMP_START":str},
        usecols=["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"],low_memory=False)
    era=pd.read_csv(must(spec["era"]),dtype={"TIMESTAMP_START":str},
        usecols=["TIMESTAMP_START","TA_ERA","VPD_ERA"],low_memory=False)
    tower=tower.loc[tower.TIMESTAMP_START.isin(wanted)]
    era=era.loc[era.TIMESTAMP_START.isin(wanted)]
    require(tower.TIMESTAMP_START.is_unique and era.TIMESTAMP_START.is_unique and
            set(tower.TIMESTAMP_START)==wanted and
            set(era.TIMESTAMP_START)==wanted,
            "Original full source-native Me6 tower/ERA neighbor time missing")
    raw=tower.merge(era,on="TIMESTAMP_START",validate="one_to_one")
    raw.index=pd.DatetimeIndex(
        pd.to_datetime(raw.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise"))
    for col in ("TA_F","TA_F_QC","VPD_F","VPD_F_QC","TA_ERA","VPD_ERA"):
        raw[col]=pd.to_numeric(raw[col],errors="coerce")
        raw.loc[raw[col]<=-9990,col]=np.nan
    center_data=[]
    for k in sorted(target):
        t=pd.to_datetime(k,format="%Y%m%d%H%M")
        actual=raw.loc[t]
        signed=centers.loc[centers.center_native_key.eq(k)].iloc[0]
        reasons=[]
        for f in ("TA_F","VPD_F","TA_ERA","VPD_ERA"):
            if not np.isclose(float(actual[f]),float(signed[f]),rtol=0,atol=1e-6,equal_nan=True):
                raise RuntimeError("Stage12ae original signed center source field not identical "+k+" "+f)
        if not(np.isclose(float(actual.VPD_F_QC),float(signed.VPD_F_QC),rtol=0,atol=1e-8)):
            raise RuntimeError("Stage12ae original signed QC code disagrees with FLUXMET "+k)
        siteT=float(forcing.at[t,"TA_USE"])
        p=float(forcing.at[t,"PSRF"])
        v,q,rh,physics=derive(siteT,p,float(actual.TA_ERA),float(actual.VPD_ERA))
        if physics!="SOURCE_PHYSICS_PASS":reasons.append(physics)
        if float(actual.TA_F_QC)!=0 or not np.isclose(siteT,float(actual.TA_F),atol=1e-7,rtol=0):
            reasons.append("TOWER_T_NOT_ORIGINAL_MEASURED_QC0_OR_CHANGED")
        if float(actual.VPD_F_QC)!=1: reasons.append("SOURCE_VPD_QC_NOT_1")
        if np.isfinite(float(forcing.at[t,"VPD_USE"])) or np.isfinite(float(forcing.at[t,"QBOT"])):
            reasons.append("SCOPE_ALREADY_FINITE_OR_EXISTING_HUMIDITY_CHANGE")
        center_data.append({
          "native_key":k,"native_time":str(t),
          "original_tower_TA_C":float(actual.TA_F),
          "original_tower_TA_F_QC":float(actual.TA_F_QC),
          "original_tower_VPD_F_QC":float(actual.VPD_F_QC),
          "original_tower_VPD_hPa":float(actual.VPD_F),
          "original_paired_ERA_T_C":float(actual.TA_ERA),
          "original_paired_ERA_VPD_hPa":float(actual.VPD_ERA),
          "original_paired_ERA_RH_pct":float(rh),
          "preserved_site_TA_USE_C":siteT,
          "original_site_PSRF_Pa":p,
          "old_Stage12ac_VPD_USE_hPa":float(forcing.at[t,"VPD_USE"]),
          "hypothetical_source_ERA_RH_VPD_USE_hPa":float(v),
          "hypothetical_source_ERA_RH_QBOT_kgkg":float(q),
          "individual_source_qc_thermo_pass":len(reasons)==0,
          "individual_source_HOLD_reason":";".join(reasons) if reasons else "NONE",
          "reanalysis_is_not_tower_observed_humidity":True,
          "model_values_approved_not_yet_applied":True
        })
    detail=pd.DataFrame(center_data)
    group_table=[]
    for number,parts in enumerate(episodes(target),1):
        before=parts[0]-HH;after=parts[-1]+HH
        section=detail.loc[pd.to_datetime(detail.native_time).isin(parts)]
        reasons=[]
        if len(section)!=len(parts) or not section.individual_source_qc_thermo_pass.all():
            reasons.append("GROUP_HAS_ORIGINAL_SOURCE_QC_OR_PHYSICS_HOLD")
        # Apply only the values hypothesized for this contiguous group, in
        # memory, preserving existing selected source neighbors otherwise.
        model=[]
        for t in [before,*parts,after]:
            if t in parts:
                row=section.loc[pd.to_datetime(section.native_time).eq(t)]
                require(len(row)==1,"Contiguous source event table center mismatch")
                model.append(float(row.iloc[0].hypothetical_source_ERA_RH_VPD_USE_hPa))
            else:
                model.append(float(forcing.at[t,"VPD_USE"]))
        steps=np.abs(np.diff(model))
        if not np.isfinite(steps).all() or not np.all(steps<=LIMIT):
            reasons.append("GROUP_VPD_TRANSITION_GT4HPA_OR_UNRESOLVED_NEIGHBOR_HOLD")
        for boundary in (before,after):
            qc=float(raw.at[boundary,"VPD_F_QC"])
            if qc==0:
                if not np.isclose(float(raw.at[boundary,"VPD_F"]),
                                  float(forcing.at[boundary,"VPD_USE"]),atol=1e-7,rtol=0):
                    reasons.append("ORIGINAL_MEASURED_QC0_BOUNDARY_CHANGED")
        group_table.append({
          "episode_id":number,"first_native_time":str(parts[0]),
          "last_native_time":str(parts[-1]),
          "original_source_QC1_HH":len(parts),
          "all_individual_QC0_T_original_ERA_source_pass":bool(section.individual_source_qc_thermo_pass.all()),
          "left_boundary_original_VPD_QC":float(raw.at[before,"VPD_F_QC"]),
          "right_boundary_original_VPD_QC":float(raw.at[after,"VPD_F_QC"]),
          "left_selected_old_VPD_hPa":float(forcing.at[before,"VPD_USE"]),
          "right_selected_old_VPD_hPa":float(forcing.at[after,"VPD_USE"]),
          "max_including_native_boundaries_VPD_step_hPa":
              float(np.max(steps)) if np.isfinite(steps).all() else float("nan"),
          "source_science_could_be_applied_as_whole_group":not reasons,
          "source_HOLD_reason":";".join(reasons) if reasons else "NONE",
          "operator_original_policy_scope_not_automatic_forcing_permission":True
        })
    groups=pd.DataFrame(group_table)
    require(len(detail)==33 and groups.original_source_QC1_HH.sum()==33,
            "All 33 Me6 original source-native center approvals not accounted")
    print("STAGE13Q ORIGINAL 33 CENTERS SCIENCE",detail[
        ["native_key","original_tower_TA_F_QC","original_tower_VPD_F_QC",
         "original_paired_ERA_RH_pct","hypothetical_source_ERA_RH_VPD_USE_hPa",
         "individual_source_qc_thermo_pass","individual_source_HOLD_reason"]
         ].to_string(index=False),flush=True)
    print("STAGE13Q GROUPED 33 Me6 ORIGINAL QC1 SOURCE SCIENCE",groups.to_string(index=False),flush=True)
    print("STAGE13Q RESULT",json.dumps({
       "total_33_source_centers":33,
       "contiguous_30min_original_source_groups":len(groups),
       "science_source_pass_centers":int(detail.individual_source_qc_thermo_pass.sum()),
       "science_source_hold_centers":int((~detail.individual_source_qc_thermo_pass).sum()),
       "entire_bounded_source_groups_pass":int(groups.source_science_could_be_applied_as_whole_group.sum()),
       "groups_held_for_source_provenance_or_unapproved_neighbors":int((~groups.source_science_could_be_applied_as_whole_group).sum()),
       "new_forcing_written":False,"DATM_ready":False,"Slurm_jobs":False},indent=2),flush=True)
    return detail,groups,spec

def main():
    p=argparse.ArgumentParser()
    mode=p.add_mutually_exclusive_group(required=True)
    for name in ("self-test","check","run"):mode.add_argument("--"+name,action="store_true")
    args=p.parse_args()
    print("STAGE13Q ME6 PREVIOUS 33 METHOD-APPROVED SCIENCE HOLDS | "+VER,flush=True)
    selftest()
    if args.self_test:return
    details,groups,spec=audit()
    if args.check:
        print("STAGE13Q READONLY CHECK PASS | 33 source audit, group PASS/HOLD classified; NO forcing or model writes",flush=True)
        return
    out=R/"reports"/("stage13q_Me6_33_original_ERA_RH_group_source_review_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    one="US-Me6_33_original_native_source_QC_ERA_RH_VPD_QBOT.csv"
    two="US-Me6_33_contiguous_original_source_QC1_episode_group_PASS_HOLD.csv"
    note="READONLY_ONLY_NOT_FORCING_OR_MODEL"
    details.to_csv(out/one,index=False,float_format="%.17g")
    groups.to_csv(out/two,index=False,float_format="%.17g")
    (out/note).write_text(
      "Operator approved Me6 33 source-method scope previously; original"
      " SHA tower and companion ERA, 30min source QC and candidate physics"
      " and full source-neighbor VPD group edges reviewed. This DOES NOT"
      " authorize extending repairs outside exact 33 source native times."
      " No forcing, original file, PFT, ZBOT, DATM or Slurm changes.\n")
    files=[one,two,note]
    receipt={"version":VER,"site":"US-Me6",
        "original_Stage12ae_receipt_SHA256":sha(AE/AE_RECEIPT),
        "original_Stage12ac_approved_source_SHA256":sha(AC/AC_FILE),
        "original_published_primary_tower_SHA256":sha(spec["primary"]),
        "original_published_companion_ERA_SHA256":sha(spec["era"]),
        "33_source_original_native_provenance_cases_reviewed":33,
        "total_episodic_group_count":len(groups),
        "science_preview_groups_PASS":int(groups.source_science_could_be_applied_as_whole_group.sum()),
        "model_or_forcing_written":False,
        "output_SHA256":{name:sha(out/name) for name in files}}
    (out/"stage13q_readonly_original_source_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE13Q READONLY REPORT DIR:",out,flush=True)
    print("STAGE13Q READONLY REPORT COMPLETE; NO FORCING / DATM / SLURM CHANGES",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("STAGE13Q SCIENCE STOP:",e,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

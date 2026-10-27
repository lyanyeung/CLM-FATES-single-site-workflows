#!/usr/bin/env python3
"""Stage13w Me6 14 source-failure mechanism + four 2017 QC2-boundary groups.

Always READONLY source-science. Sources: SHA-sealed ACTUAL Stage13u and
Stage13v IRIDIS6 reports, themselves derived from signed original tower
FLUXMET/paired ERA/Stage13s source manifests. Precise failing physical
clause, no ad hoc threshold relaxation or unapproved forcing.
--self-test standalone; --check read only; --run writes only SHA report.
"""
import argparse,hashlib,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True
VERSION="batch03-stage13w-v1-20261027-Me6-14-physics-fail-2017-QC2-boundary"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
U=ROOT/"reports/stage13u_Me6_six_held_source_QC1_runs_BATCH_SCIENCE_ONLY_20261027T074748Z_9e23952f"
V=ROOT/"reports/stage13v_Me6_14_source_QC1_failures_BATCH_READONLY_20261027T083537Z_7151cdf8"
U_RECEIPT="stage13u_six_held_source_runs_SHA_receipt.json"
V_RECEIPT="stage13v_sha_receipt.json"
U_ROWS="782_original_native_QC1_records_tower_ERA_PSRF_RH_QBOT_review.csv"
U_GROUPS="six_held_original_source_QC1_runs_GROUPED_review.csv"
U_INFO="stage13u_Me6_six_runs_grouped_approval_decision_evidence.json"
V_BAD="14_original_source_failed_ERA_physics_HH.csv"
V_GROUPS="science_valid_QC1_contiguous_groups_PROPOSALS_ONLY.csv"
V_SUMMARY="six_remaining_source_QC1_full_runs_science_HOLD.csv"
V_INFO="stage13v_science_review_summary.json"
EXPECTED={14:5,15:8,17:1}
NUM={12:4,14:469,15:95,16:30,17:137,18:47}
SUSPECT_2017=(15,16,17,18)

def need(condition,message):
    if not bool(condition):raise RuntimeError("STAGE13W SIGNED SOURCE HOLD: "+str(message))

def must(path):
    p=Path(path)
    need(p.is_file() and not p.is_symlink(),"missing original signed report or symlink "+str(p))
    return p

def digest(path):
    h=hashlib.sha256()
    with must(path).open("rb") as fh:
        for b in iter(lambda:fh.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def boolean(s):
    a=s.astype(str).str.strip().str.lower()
    need(a.isin(["true","false"]).all(),"invalid signed bool field")
    return a.eq("true").to_numpy()

def es(t):
    return 6.112*np.exp(17.67*float(t)/(float(t)+243.5))

def physics(ta,pa,era_t,era_v):
    val=np.asarray([ta,pa,era_t,era_v],dtype=float)
    if not np.isfinite(val).all():
        return dict(source_complete=False,pressure_valid=False,
                    measured_site_ERA_t_difference_C=float("nan"),
                    site_ERA_temperature_difference_le_8C=False,
                    ERA_RH_pct=float("nan"),ERA_RH_valid=False,
                    site_VPD_hPa=float("nan"),VPD_within_site_saturation=False,
                    site_QBOT_kgkg=float("nan"),QBOT_physically_valid=False,
                    all_source_physics_valid=False)
    t,p,et,ev=map(float,val)
    RH=100*(1-ev/es(et))
    siteSat=es(t)
    siteV=siteSat*(1-RH/100)
    partial=(siteSat-siteV)*100
    den=p-0.378*partial
    q=(0.622*partial/den) if den!=0 else float("nan")
    pv=50000<p<110000
    tpass=abs(t-et)<=8
    rhpass=bool(np.isfinite(RH) and 0<RH<100)
    vpass=bool(np.isfinite(siteV) and 0<siteV<siteSat)
    qpass=bool(np.isfinite(q) and 0<q<0.08)
    return dict(source_complete=True,pressure_valid=pv,
        measured_site_ERA_t_difference_C=abs(t-et),
        site_ERA_temperature_difference_le_8C=tpass,
        ERA_RH_pct=float(RH),ERA_RH_valid=rhpass,
        site_VPD_hPa=float(siteV),VPD_within_site_saturation=vpass,
        site_QBOT_kgkg=float(q),QBOT_physically_valid=qpass,
        all_source_physics_valid=bool(pv and tpass and rhpass and vpass and qpass))

def selftest():
    p=physics(8,95000,9,2)
    need(p["all_source_physics_valid"] and p["site_ERA_temperature_difference_le_8C"],
         "plausible T and RH source physics")
    p2=physics(8,95000,-10,2)
    need(not p2["site_ERA_temperature_difference_le_8C"],
         "strict original site vs ERA 8C temperature gate")
    need(boolean(pd.Series([True,False,"True","False"])).tolist()==[True,False,True,False],
         "original source string or bool reader")
    need(sum(NUM.values())==782 and sum(EXPECTED.values())==14,
         "six-run 782/14 original source scope")
    print("STAGE13W SELF-TEST PASS | strict 14 source-physics mechanisms, 2017 source QC2 boundaries, NO WRITES",flush=True)

def sealed(root,name,wanted,expected_set):
    a=json.loads(must(root/name).read_text())
    need(a.get("version")==wanted and a.get("site")=="US-Me6",
         "sealed original report version/site mismatch")
    outputs=a.get("outputs_SHA256",{})
    need(set(outputs)==set(expected_set),
         "original output science SHA manifest set changed "+str(root))
    for n,h in outputs.items():
        need("/" not in n and "\\" not in n and digest(root/n)==h,
             "signed report output changed: "+n)
    return a

def audit():
    u=sealed(U,U_RECEIPT,
        "batch03-stage13u-v1-20261027-Me6-six-original-QC1-held-runs-batch-triage",
        [U_ROWS,U_GROUPS,U_INFO,"SOURCE_EVIDENCE_ONLY_NO_OPERATOR_APPROVAL_OR_MODEL_FORCING"])
    v=sealed(V,V_RECEIPT,
        "batch03-stage13v-v1-Me6-14-exact-original-science-failures",
        [V_BAD,V_GROUPS,V_SUMMARY,V_INFO,"SOURCE_ONLY_NO_QC1_NEIGHBOR_APPROVAL_OR_FORCING"])
    need(u.get("forcings_generated") is False and u.get("unapproved_source_neighbors_still_unapproved")==761 and
         v.get("forcing_generated") is False and v.get("operator_new_approval") is False and
         v.get("stage13u_source_receipt_SHA256")==digest(U/U_RECEIPT),
         "source original Stage13u/Stage13v signatures/approval missing")
    uinfo=json.loads(must(U/U_INFO).read_text())
    vinfo=json.loads(must(V/V_INFO).read_text())
    need(uinfo.get("original_source_QC1_native_halfhours_examined")==782 and
         uinfo.get("source_paired_ERA_RH_QBOT_physical_and_T_gate_count")==768 and
         uinfo.get("operator_previously_approved_Stage12ac_five_2017_records_protected")==5 and
         vinfo.get("failed_original_ERA_source_native_HH")==14 and
         vinfo.get("contiguous_source_valid_subepisodes_for_scientific_review")==11 and
         vinfo.get("subepisodes_two_original_measured_QC0_anchors")==1,
         "actual original signed stage13u/v result drift")
    rows=pd.read_csv(must(U/U_ROWS),dtype={"native_time":str},low_memory=False)
    original_groups=pd.read_csv(must(U/U_GROUPS),low_memory=False)
    failed=pd.read_csv(must(V/V_BAD),dtype={"native_time":str},low_memory=False)
    candidates=pd.read_csv(must(V/V_GROUPS),low_memory=False)
    need(len(rows)==782 and rows.native_time.is_unique and len(failed)==14 and
         failed.native_time.is_unique and len(original_groups)==6 and len(candidates)==11 and
         set(failed.native_time).issubset(set(rows.native_time)),
         "original exact native source 782/14/11 row identities changed")
    signed_failed=rows.loc[~boolean(rows.source_physics_and_retained_T_gate_PASS)].copy()
    need(set(signed_failed.native_time)==set(failed.native_time) and
         signed_failed.groupby("full_run_id").size().to_dict()==EXPECTED,
         "exact original 14 physical failure native source timestamps changed")
    detail=[]
    for raw in signed_failed.itertuples(index=False):
        x=physics(raw.retained_stage13s_site_T_C,
            raw.stage13s_retained_site_PSRF_Pa,
            raw.original_paired_ERA_T_C,
            raw.original_paired_ERA_VPD_hPa)
        need(not x["all_source_physics_valid"],
             "source physical exception no longer fails "+str(raw.native_time))
        a=float(raw.paired_ERA_RH_percent)
        if np.isfinite(a):need(np.isclose(a,x["ERA_RH_pct"],atol=1e-7,rtol=0),
             "original RH signed report vs exact thermodynamics mismatch")
        reasons=[]
        if not x["source_complete"]:reasons.append("SOURCE_T_P_ERA_VALUE_MISSING")
        if not x["pressure_valid"]:reasons.append("SITE_PSRF_OUT_OF_PHYSICAL_RANGE")
        if not x["site_ERA_temperature_difference_le_8C"]:reasons.append("SITE_ERA_T_DELTA_GT8C")
        if not x["ERA_RH_valid"]:reasons.append("PAIRED_ERA_RH_NOT_0_100")
        if not x["VPD_within_site_saturation"]:reasons.append("SOURCE_VPD_NOT_0_TO_ES_SITE")
        if not x["QBOT_physically_valid"]:reasons.append("QBOT_NOT_0_TO_0p08_KGKG")
        need(len(reasons)>=1,"14 exact failed source physics cause not determined")
        detail.append({
            "source_original_full_run_id":int(raw.full_run_id),
            "native_time":str(raw.native_time),
            "retained_site_T_C":float(raw.retained_stage13s_site_T_C),
            "original_ERA_T_C":float(raw.original_paired_ERA_T_C),
            "abs_site_minus_ERA_T_C":x["measured_site_ERA_t_difference_C"],
            "original_ERA_VPD_hPa":float(raw.original_paired_ERA_VPD_hPa),
            "reconstructed_ERA_RH_percent":x["ERA_RH_pct"],
            "original_retained_PSRF_Pa":float(raw.stage13s_retained_site_PSRF_Pa),
            "reconstructed_site_VPD_hPa":x["site_VPD_hPa"],
            "reconstructed_site_QBOT_kgkg":x["site_QBOT_kgkg"],
            "strict_T_minus_ERA_le_8C":x["site_ERA_temperature_difference_le_8C"],
            "strict_RH_0_100":x["ERA_RH_valid"],
            "strict_site_VPD_within_saturation":x["VPD_within_site_saturation"],
            "strict_QBOT_0_0p08":x["QBOT_physically_valid"],
            "exact_physics_HOLD_causes":";".join(reasons),
            "original_site_stage13s_forcing_unchanged":True,
            "scientific_repair_method_NOT_authorized":True
        })
    diag=pd.DataFrame(detail)
    bounds=[]
    for gid in (15,16,17,18):
        r=original_groups.loc[original_groups.full_source_run_id.eq(gid)]
        need(len(r)==1 and
             int(r.iloc[0].native_pre_boundary_VPD_QC)==2 and
             int(r.iloc[0].native_post_boundary_VPD_QC)==2 and
             not bool(r.iloc[0].both_direct_bookends_original_measured_QC0),
             "original 2017 QC2 no-direct-QC0-boundary premise changed")
        z=r.iloc[0]
        bounds.append({
            "source_2017_full_run_id":gid,
            "native_QC1_HH":int(z.original_QC1_native_HH),
            "source_direct_left_VPD_QC":int(z.native_pre_boundary_VPD_QC),
            "source_direct_right_VPD_QC":int(z.native_post_boundary_VPD_QC),
            "source_direct_measured_QC0_both_bookends":False,
            "remote_measured_QC0_left_distance_native_HH":
                int(z.native_HH_to_nearest_measured_QC0_before),
            "remote_measured_QC0_right_distance_native_HH":
                int(z.native_HH_to_nearest_measured_QC0_after),
            "full_ERA_RH_candidate_max_30min_VPD_jump_hPa":
                float(z.ERA_candidate_full_run_max_30min_VPD_step_hPa),
            "full_ERA_RH_candidate_4hPa_violating_edges":
                int(z.ERA_candidate_native_VPD_edges_gt4hPa),
            "existing_2017_July04_Stage12ac_rows_preserved":
                int(z.previously_Stage12ac_approved_2017_native_rows),
            "remote_QC0_NOT_immediate_source_anchor":True,
            "blanket_source_QC2_neighbor_replacement_NOT_authorized":True
        })
    boundary=pd.DataFrame(bounds)
    need(int(boundary.existing_2017_July04_Stage12ac_rows_preserved.sum())==5 and
         len(boundary)==4 and len(diag)==14,
         "exact 5 old July2017 source protects or 14 failed list changed")
    summary={
        "version":VERSION,"site":"US-Me6",
        "actual_Stage13u_signed_receipt_SHA256":digest(U/U_RECEIPT),
        "actual_Stage13v_signed_receipt_SHA256":digest(V/V_RECEIPT),
        "original_source_782_QC1_halfhours":782,
        "physically_valid_original_ERA_RH_QBOT_native_HH":768,
        "original_source_14_physics_failed_HH":14,
        "valid_contiguous_provisional_subgroups":11,
        "original_both_measured_QC0_bounded_groups":1,
        "original_2017_runs_both_native_edges_QC2":4,
        "previously_approved_Stage12ac_2017_time_rows_protected":5,
        "other_original_QC1_neighbors_not_authorized":761,
        "failure_cause_frequency":diag.exact_physics_HOLD_causes.value_counts().to_dict(),
        "original_forcing_changed":False,
        "new_operator_science_authorization":False,
        "postv5":False,"DATM":False,"AD400":False,"Slurm":False}
    print("STAGE13W EXACT FOURTEEN ORIGINAL SOURCE PHYSICS FAILURE CAUSES",flush=True)
    print(diag[["source_original_full_run_id","native_time","abs_site_minus_ERA_T_C",
        "reconstructed_ERA_RH_percent","exact_physics_HOLD_causes"]].to_string(index=False),flush=True)
    print("STAGE13W FOUR 2017 SOURCE QC2 EDGE CONFLICTS",flush=True)
    print(boundary.to_string(index=False),flush=True)
    print("STAGE13W SOURCE-ONLY BATCH DECISION SUPPORT",json.dumps(summary,indent=2),flush=True)
    return diag,boundary,summary

def main():
    p=argparse.ArgumentParser()
    mode=p.add_mutually_exclusive_group(required=True)
    for name in ("self-test","check","run"):mode.add_argument("--"+name,action="store_true")
    cmd=p.parse_args()
    print("STAGE13W ME6 ORIGINAL 14 HOLD SCIENCE MECHANISMS | "+VERSION,flush=True)
    selftest()
    if cmd.self_test:return
    failed,boundary,summary=audit()
    if cmd.check:
        print("STAGE13W READONLY CHECK PASS | exact 14 cause table, four 2017 QC2-boundary reviews; NO WRITES",flush=True)
        return
    out=ROOT/"reports"/("stage13w_Me6_14_exact_physics_causes_and_2017_QC2_BOUNDARIES_READONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    a="14_original_native_QC1_exact_ERA_RH_T_QBOT_science_failures.csv"
    b="four_2017_original_source_QC2_edges_no_immediate_QC0.csv"
    c="stage13w_original_source_batch_decision_support.json"
    marker="NO_OPERATOR_APPROVAL_NO_FORCING_OR_MODEL_JOBS"
    failed.to_csv(out/a,index=False,float_format="%.17g")
    boundary.to_csv(out/b,index=False,float_format="%.17g")
    (out/c).write_text(json.dumps(summary,indent=2)+"\n")
    (out/marker).write_text(
        "Exact original source failures and QC2 edges. Source ERA RH is not"
        " tower-observed humidity. This report does NOT approve a new"
        " source correction of any held 2015/2017 QC1 records, does not"
        " alter previous Stage13s 235 source-native repairs or 2017 Stage12ac"
        " five original operator-approved values, and writes no model.\n")
    receipt={"version":VERSION,"site":"US-Me6",
        "stage13u_input_signed_sha":digest(U/U_RECEIPT),
        "stage13v_input_signed_sha":digest(V/V_RECEIPT),
        "forcings_written":False,"operator_approved":False,
        "outputs_SHA256":{f:digest(out/f) for f in (a,b,c,marker)}}
    (out/"stage13w_readonly_science_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE13W SCIENCE READONLY REPORT DIR:",out,flush=True)
    print("STAGE13W ME6 14 SOURCE PHYSICS CAUSES AND 4 QC2 EDGE GROUPS VERIFIED; NO FORCING/DATM/SLURM",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE13W SCIENCE STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

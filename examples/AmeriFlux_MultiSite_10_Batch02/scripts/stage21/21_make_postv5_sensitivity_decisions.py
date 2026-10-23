#!/usr/bin/env python3
"""Stage21 - READ-ONLY candidate decision ledger for AmeriFlux Batch02.

Conservatively partition all 4884 Stage20 rows. Never infer scientific approval:
(1) preserve Stage11's 14 original HOLDs;
(2) hold all US-Ho1 until tower UTC offset is confirmed from original metadata;
(3) hold any remaining row for which Td-transfer creates negative water VPD;
(4) put remaining numerically valid ERA5 water-RH transfer values into a
    NON-APPROVED, EXPERIMENT-ONLY overlay candidate table.

No original or model forcing file, DATM, CIME, Slurm job or Git state is altered.
The overlay table contains suggested point values only, NOT model-ready forcing.
Do not start spinups from this table. QC0 proximity is a warning, not approval.

--check: no writes; --write-plan: isolated report in HOME.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

STAGE20 = Path.home() / "AmeriFlux_Batch02_stage20_physical_evidence_review_20261023T021238Z_d7a70a5f"
CSV = "all_4884_phase_transfer_QC_sensitivity.csv"
EXPECTED = {"US-EML":1327, "US-GLE":295, "US-Ho1":917, "US-ICh":169, "US-ICt":2176}
HOLD_COUNTS = {"US-EML":1, "US-GLE":3, "US-Ho1":0, "US-ICh":0, "US-ICt":10}
STAGE17_SHA = "84f680fb67030d374bb8a02abd4fce5a4a2c5d4abe7c59a30acf7bb5948488d4"
RISK_TEMP_DIFF_C = 5.0
RISK_METHOD_DIFF_VPD_HPA = 0.5

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda:f.read(1<<20),b""):h.update(part)
    return h.hexdigest()

def saturation_water(temp):
    temp=np.asarray(temp,dtype=float)
    return 6.112*np.exp(17.67*temp/(temp+243.5))

def bool_field(frame,field):
    s=frame[field]
    if pd.api.types.is_bool_dtype(s):return s.astype(bool)
    if s.astype(str).str.lower().isin(("true","false")).all():
        return s.astype(str).str.lower().eq("true")
    raise ValueError("Unrecognized boolean values in "+field)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--write-plan",action="store_true")
    p.add_argument("--stage20-root",type=Path,default=STAGE20)
    p.add_argument("--output-root",type=Path)
    args=p.parse_args()
    root=args.stage20_root.expanduser().resolve(strict=True)
    if not (root/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Stage20 HOLD marker absent")
    manifest=json.loads((root/"manifest.json").read_text())
    if manifest.get("schema")!="STAGE20_PHASE_TRANSFER_EVIDENCE_REVIEW_v1" or \
       manifest.get("stage17_plan_sha256")!=STAGE17_SHA or \
       manifest.get("scientific_status")!="ALL_4884_HOLD_NO_DATM_APPROVAL" or \
       manifest.get("number_targets")!=4884 or \
       manifest.get("number_original_holds")!=14 or \
       manifest.get("number_approved")!=0 or \
       manifest.get("US_Ho1_timezone_status")!="PROVISIONAL_MINUS5_BADM_PENDING":
        raise ValueError("Stage20 study identity/approval has changed")
    stage19=Path(manifest["stage19_root"]).resolve(strict=True)
    if sha(stage19/"manifest.json")!=manifest["stage19_manifest_sha256"] or \
       sha(stage19/"all_4884_ERA5_RH_VPD_QBOT_sensitivity.csv")!=manifest["stage19_input_csv_sha256"]:
        raise ValueError("Stage19 input differs from Stage20 reviewed inputs")
    input_csv=root/CSV
    a=pd.read_csv(input_csv,parse_dates=["local"])
    if len(a)!=4884 or a.duplicated(["site","local"]).any() or \
       a.groupby("site").size().to_dict()!=EXPECTED or \
       a.groupby(["site","year"]).ngroups!=42 or \
       not (a.local.dt.year==a.year).all():
        raise ValueError("Stage20 CSV row identity/count changed")
    for name in ("original_Stage11_HOLD_preserved","Td_transfer_negative_water_VPD",
                 "Td_transfer_numeric_bad","sensitivity_numeric_valid",
                 "nearby_QC0_24h_any","ERA5_ice_RH_above100_subzero",
                 "scientific_approval","raw_tower_T_equals_Stage11_retained_T"):
        a[name]=bool_field(a,name)
    if a.groupby("site")["original_Stage11_HOLD_preserved"].sum().to_dict()!=HOLD_COUNTS or \
       int(a.Td_transfer_negative_water_VPD.sum())!=431 or \
       a.Td_transfer_numeric_bad.any() or \
       (~a.sensitivity_numeric_valid).any() or \
       a.scientific_approval.any() or \
       (~a.raw_tower_T_equals_Stage11_retained_T).any():
        raise ValueError("Stage20 physical or original-HOLD totals changed")
    # Reproduce RH-transfer against Stage20's unchanged retained tower T/P.
    t=a.retained_TA_C.to_numpy(float)
    pa=a.retained_PA_kPa.to_numpy(float)
    rh=a.ERA5_RH_water_pct.to_numpy(float)
    e=saturation_water(t)*rh/100
    check_vpd=saturation_water(t)-e
    check_q=.622*(e*100)/(pa*1000-.378*e*100)
    if not np.allclose(check_vpd,a.sensitivity_VPD_hPa.to_numpy(float),rtol=1e-8,atol=1e-8) or \
       not np.allclose(check_q,a.sensitivity_QBOT_kgkg.to_numpy(float),rtol=1e-8,atol=1e-10):
        raise ValueError("Stage20 RH-transfer reproduction failed")
    if not (np.isfinite(check_vpd)&(check_vpd>=-.005)&
            np.isfinite(check_q)&(check_q>0)&(check_q<.08)).all():
        raise ValueError("Nonphysical RH transfer candidate")
    a["hold_original14"]=a.original_Stage11_HOLD_preserved
    a["hold_historical_timezone"]=a.site.eq("US-Ho1")
    a["hold_Td_water_supersat"]=a.Td_transfer_negative_water_VPD
    a["warning_no_QC0_within24h"]=~a.nearby_QC0_24h_any
    a["warning_ice_RH_gt100"]=a.ERA5_ice_RH_above100_subzero
    a["warning_large_ERA_tower_temperature_diff"]=a.ERA_minus_tower_T_C.abs()>RISK_TEMP_DIFF_C
    a["warning_large_Td_vs_RH_method_VPD_diff"]=a.Td_minus_RH_transfer_water_VPD_hPa.abs()>RISK_METHOD_DIFF_VPD_HPA
    a["experiment_status"]=np.select(
        [a.hold_original14,a.hold_historical_timezone,a.hold_Td_water_supersat],
        ["HOLD_ORIGINAL_STAGE11","HOLD_HO1_TIMEZONE_UNVERIFIED",
         "HOLD_TD_TRANSFER_SUPERSAT_CONFLICT"],
        default="EXPERIMENT_ONLY_RH_TRANSFER_UNAPPROVED")
    eligible=a.experiment_status.eq("EXPERIMENT_ONLY_RH_TRANSFER_UNAPPROVED")
    a["model_forcing_approved"]=False
    a["model_run_authorised"]=False
    a["candidate_method"]="ERA5_WATER_RH_AT_RETAINED_TOWER_T_AND_P"
    # Additional caution flags are indicators, never model-approval decisions.
    values=["site","local","year","experiment_status","candidate_method",
            "retained_TA_C","retained_PA_kPa","ERA5_RH_water_pct",
            "sensitivity_VPD_hPa","sensitivity_QBOT_kgkg",
            "ERA5_temporal_method","warning_no_QC0_within24h",
            "warning_ice_RH_gt100","warning_large_ERA_tower_temperature_diff",
            "warning_large_Td_vs_RH_method_VPD_diff",
            "model_forcing_approved","model_run_authorised"]
    decision=a[values].copy()
    by_site=(a.groupby(["site","experiment_status"]).size()
               .unstack(fill_value=0).reset_index())
    print("========== STAGE21 EXPERIMENT-ONLY DECISION LEDGER ==========")
    print("Original Stage20:",len(a),"/4884; original Stage11 HOLDs:",
          int(a.hold_original14.sum()),"/14")
    print("EXPERIMENT-ONLY RH-transfer CANDIDATES:",
          int(eligible.sum()),"NOT APPROVED FOR FORCING")
    print("HOLD ORIGINAL STAGE11:",int(a.experiment_status.eq(
          "HOLD_ORIGINAL_STAGE11").sum()))
    print("HOLD HO1 TZ:",int(a.experiment_status.eq(
          "HOLD_HO1_TIMEZONE_UNVERIFIED").sum()))
    print("HOLD Td-TRANSFER CONFLICT (not already held):",int(a.experiment_status.eq(
          "HOLD_TD_TRANSFER_SUPERSAT_CONFLICT").sum()))
    print("QC0-unavailable in 24h:",int(a.warning_no_QC0_within24h.sum()))
    print("RH_ice over100 caution:",int(a.warning_ice_RH_gt100.sum()))
    print("Large |T_ERA-T_tower| >",RISK_TEMP_DIFF_C,"C:",
          int(a.warning_large_ERA_tower_temperature_diff.sum()))
    print(by_site.to_string(index=False))
    if args.check:
        print("STAGE21 CHECK ONLY: no output, forcing or model changes")
        return 0
    path=(args.output_root.expanduser().resolve() if args.output_root else
          Path.home()/("AmeriFlux_Batch02_stage21_postv5_candidate_decisions_"+
          datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8]))
    for protected in (root,stage19,Path("/iridisfs/scratch/ly3n24/CLM_FATES")):
        protected=protected.resolve()
        if path==protected or path in protected.parents or protected in path.parents:
            raise ValueError("Unsafe output path")
    if path.exists() or path.is_symlink():
        raise ValueError("Stage21 output path already exists")
    path.mkdir(parents=True,exist_ok=False)
    (path/"DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "Stage21: NO forcing approval. EXPERIMENT_ONLY is a review candidate, not a model input.\n")
    decision.to_csv(path/"all_4884_stage21_repair_decision_ledger.csv",index=False)
    decision.loc[eligible].to_csv(
        path/"RH_transfer_experiment_candidates_NOT_FOR_DATM.csv",index=False)
    decision.loc[~eligible].to_csv(
        path/"HOLD_rows_requiring_followup.csv",index=False)
    by_site.to_csv(path/"site_decision_summary.csv",index=False)
    (path/"manifest.json").write_text(json.dumps(dict(
        schema="STAGE21_EXPERIMENT_ONLY_DECISION_v1",
        stage20_report=str(root),
        stage20_csv_sha256=sha(input_csv),
        stage20_manifest_sha256=sha(root/"manifest.json"),
        script_sha256=sha(Path(__file__)),
        total=4884,original_stage11_HOLD=14,
        candidate_experiment_only=int(eligible.sum()),
        held_rows=int((~eligible).sum()),
        scientific_approved=0,
        original_forcing_changed=False,
        model_forcing_ready=False,
        method="ERA5_WATER_RH_AT_RETAINED_TOWER_T_AND_P",
        US_Ho1_timezone="PROVISIONAL_BLOCKED",
        shared_ERA5_grid_US_ICh_ICt=True,
        note="Candidate point values only; not a native forcing or permission to launch model."),indent=2)+"\n")
    print("STAGE21 REPORT:",path)
    print("Forcing/DATM/CIME/Slurm: UNCHANGED. All original anomalies scientifically on HOLD.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Stage22: read-only risk screening of all 4,884 Stage21 records.
All rows remain unapproved. Creates isolated HOME CSV reports only.
No original forcing, DATM, CIME, Slurm or CDS changes.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

ROOT=Path.home()/"AmeriFlux_Batch02_stage21_postv5_candidate_decisions_20261023T022056Z_b754ce13"
L="all_4884_stage21_repair_decision_ledger.csv"
S="all_4884_phase_transfer_QC_sensitivity.csv"
C="EXPERIMENT_ONLY_RH_TRANSFER_UNAPPROVED"
EXPECTED={"US-EML":1327,"US-GLE":295,"US-Ho1":917,"US-ICh":169,"US-ICt":2176}

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()

def boolean(series):
    s=series.astype(str).str.lower()
    if not s.isin(["true","false"]).all():
        raise ValueError("Non-boolean data")
    return s.eq("true")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--check",action="store_true")
    g.add_argument("--write-report",action="store_true")
    args=p.parse_args()
    if not (ROOT/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Stage21 HOLD marker missing")
    m=json.loads((ROOT/"manifest.json").read_text())
    expected={"schema":"STAGE21_EXPERIMENT_ONLY_DECISION_v1",
              "total":4884,"candidate_experiment_only":3947,
              "held_rows":937,"scientific_approved":0,
              "model_forcing_ready":False}
    if any(m.get(k)!=v for k,v in expected.items()):
        raise ValueError("Stage21 manifest unexpectedly changed")
    root20=Path(m["stage20_report"]).resolve(strict=True)
    if digest(root20/S)!=m["stage20_csv_sha256"] or (
       digest(root20/"manifest.json")!=m["stage20_manifest_sha256"]):
        raise ValueError("Stage20 input checksum changed")
    a=pd.read_csv(ROOT/L,parse_dates=["local"])
    b=pd.read_csv(root20/S,parse_dates=["local"])
    for x in (a,b):
        if len(x)!=4884 or x.duplicated(["site","local"]).any() or (
            x.groupby("site").size().to_dict()!=EXPECTED):
            raise ValueError("Source site/time identity differs")
    use=["site","local","ERA_minus_tower_T_C",
         "Td_minus_RH_transfer_water_VPD_hPa",
         "nearby_QC0_T_and_VPD_24h_n",
         "ERA5_ice_RH_above100_subzero"]
    x=a.merge(b[use],on=["site","local"],how="inner",validate="one_to_one")
    if len(x)!=4884:raise ValueError("Unmatched Stage20/21 row")
    status=x.experiment_status.value_counts().to_dict()
    if status!={C:3947,"HOLD_ORIGINAL_STAGE11":14,
       "HOLD_HO1_TIMEZONE_UNVERIFIED":917,
       "HOLD_TD_TRANSFER_SUPERSAT_CONFLICT":6}:
        raise ValueError("Stage21 HOLD classifications changed")
    if boolean(x.model_forcing_approved).any() or (
       boolean(x.model_run_authorised).any()):
        raise ValueError("Unexpected model approval")
    x["qc0_nearby"]=x.nearby_QC0_T_and_VPD_24h_n.gt(0)
    x["large_T_difference"]=x.ERA_minus_tower_T_C.abs().gt(5.0)
    x["large_method_difference"]=x.Td_minus_RH_transfer_water_VPD_hPa.abs().gt(0.5)
    x["ice_supersaturation_caution"]=boolean(x.ERA5_ice_RH_above100_subzero)
    if int((~x.qc0_nearby).sum())!=4701 or (
       int(x.large_T_difference.sum())!=3524):
        raise ValueError("Known Stage21 QC0/temperature counts changed")
    candidate=x.experiment_status.eq(C)
    high=x.large_T_difference|x.large_method_difference
    x["risk_tier"]=np.select([
       ~candidate,candidate&high,candidate&~high&~x.qc0_nearby,
       candidate&~high&x.qc0_nearby],
       ["HOLD","C_LARGE_DISAGREEMENT","B_NO_QC0_NEARBY",
        "A_QC0_NEARBY"],default="ERROR")
    if x.risk_tier.eq("ERROR").any():raise ValueError("Unclassified rows")
    x["scientific_approval"]=False
    x["model_forcing_ready"]=False
    summary=pd.crosstab(x.site,x.risk_tier)
    print("STAGE22: All 4884 classified; candidates=",int(candidate.sum()),
          "HOLD=",int((~candidate).sum()))
    print("RISK TIERS:",x.risk_tier.value_counts().to_dict())
    print("Candidate large temperature gap:",int((candidate&x.large_T_difference).sum()))
    print("Candidate lacks nearby QC0:",int((candidate&~x.qc0_nearby).sum()))
    print(summary.to_string())
    print("Science-approved=0, model-ready=0")
    if args.check:
        print("CHECK ONLY: no files written")
        return 0
    out=Path.home()/("AmeriFlux_Batch02_stage22_risk_screen_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
        "_"+uuid4().hex[:8])
    if out.exists():raise ValueError("Existing output")
    out.mkdir(parents=True,exist_ok=False)
    (out/"DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "All Stage22 values remain unapproved diagnostics.\n")
    fields=["site","local","year","experiment_status","risk_tier",
            "ERA5_RH_water_pct","sensitivity_VPD_hPa","sensitivity_QBOT_kgkg",
            "ERA_minus_tower_T_C","Td_minus_RH_transfer_water_VPD_hPa",
            "qc0_nearby","large_T_difference","large_method_difference",
            "ice_supersaturation_caution","scientific_approval","model_forcing_ready"]
    x[fields].to_csv(out/"4884_risk_decisions_NOT_FOR_DATM.csv",index=False)
    x.loc[candidate,fields].to_csv(
        out/"3947_point_candidates_NOT_MODEL_READY.csv",index=False)
    x.loc[~candidate,fields].to_csv(out/"937_original_holds.csv",index=False)
    summary.to_csv(out/"site_tier_counts.csv")
    (out/"manifest.json").write_text(json.dumps(dict(
       stage21_manifest_sha256=digest(ROOT/"manifest.json"),
       stage21_ledger_sha256=digest(ROOT/L),
       script_sha256=digest(Path(__file__)),
       n_candidates=3947,n_holds=937,n_approved=0,
       model_ready=False,scientific_status="ALL_HOLD"),indent=2)+"\n")
    print("STAGE22 REPORT:",out)
    print("NO original forcing, model input, CIME or Slurm jobs modified")
    return 0

if __name__=="__main__":
    raise SystemExit(main())

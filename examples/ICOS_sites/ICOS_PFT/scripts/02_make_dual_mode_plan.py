#!/usr/bin/env python3
"""Create a conservative planning manifest only. Never touches IRIDIS cases or Slurm."""
import argparse
import csv
from pathlib import Path
E=Path(__file__).resolve().parents[1]/"38_site_PFT_evidence.csv"
C={"NUMERIC_SPECIES","NUMERIC_AREA","NUMERIC_TEMPORAL","NUMERIC_BASAL_AREA","NUMERIC_VEGETATED_COVER","TOTAL_COVER_ONLY","NUMERIC_COVER_CONFLICT","NUMERIC_GROUND_COVER","NUMERIC_CONFLICT"}
AREA={"NL-Loo","ES-LJu","DE-Tha"}
def main():
 p=argparse.ArgumentParser();p.add_argument("--output",type=Path,default=Path.home()/"ICOS_PFT_Observed22_dual_plan.tsv");a=p.parse_args()
 with E.open(newline="",encoding="utf8") as f: observations=list(csv.DictReader(f))
 rows=[]
 for o in observations:
  if o["evidence_class"] not in C:continue
  for mode in ("FULL","FIXNC"):
   site=o["site"]
   readiness=("AREA_REVIEW_REQUIRED" if site in AREA else "HOLD_NOT_MEASURED_AREA")
   rows.append({"site":site,"batch":o["batch"],"mode":mode,"proposed_case":site+"_OBSPFT_"+mode+"26","evidence_class":o["evidence_class"],"observed_denominator":o["observed_denominator"],"fixed_area_status":readiness if mode=="FIXNC" else "NOT_PRESCRIBED","case_status":"PLAN_ONLY_NOT_CREATED","submission_authorized":"NO","source":o["literature_or_station_url"]})
 if len(rows)!=44:raise SystemExit("FAIL expected 22 sites x 2 modes (44 proposed cases)")
 a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open("w",newline="",encoding="utf8") as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter="\t");w.writeheader();w.writerows(rows)
 print("PLAN ONLY: 44 prospective configurations across 22 sites. ZERO cases/jobs created.")
 print(a.output)
if __name__=="__main__":main()

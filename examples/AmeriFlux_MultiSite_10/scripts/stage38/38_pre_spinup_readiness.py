#!/usr/bin/env python3
"""Stage38: conservative READ-ONLY Batch01 production readiness preflight.
Read only existing on-disk scientific reports and PFT candidate TSV.
Does not equate Stage21 numerical PASS with science approval and does not
build DATM, modify surface/CIME, or submit Slurm jobs.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
from datetime import datetime,timezone

BASE=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
SITES=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
SRC=Path(__file__).resolve().parents[2]
CAND=SRC.parent/"AmeriFlux_sites"/"metadata"/"Batch01_EC_FATES_PFT_experiment_candidates_v4_20261023.tsv"
PARAM=Path("/iridisfs/scratch/ly3n24/CLM_FATES/CTSM/src/fates/parameter_files/fates_params_default.json")
ISSUES={
"QC_V5_SCIENTIFIC_APPROVAL":"518 official QC0 revisions, unverified low RH episodes and 3 scoped US-Bar winter records",
"ZBOT_CA_CBO":"Multiple temperature heights; TA_F sensor crosswalk not established",
"ZBOT_CA_MAN":"Multiple temperature heights; TA_F sensor crosswalk not established",
"ZBOT_OTHER_SITES":"Static/dynamic source mapping and event-date uncertainty remain candidate status",
"PFT_FATES_INITIALIZATION":"Ten EC PFT targets documented; no case-specific FATES active-PFT/biogeography/init mechanism validated",
"PFT_TOWER_PERCENT_BASIS":"Stand tree fractions, stem counts, basal area and model cover are non-interchangeable",
"SURFACE_SITE_REPRESENTATIVENESS":"CA-Cbo, CA-TP1/3/4 and US-Aud require host surface/landunit decisions",
"DATM_NOLEAP_SITE_SERIES":"No verified final 30-minute continuous physical DATM with ZBOT for all ten sites",
"CIME_SMOKE_RESTART":"No site-specific prepared/compiled/smoke-validated/restart-validated cases",
}
def read(path):
 with path.open(newline="",encoding="utf-8") as f:
  r=csv.DictReader(f,delimiter="\t");return list(r)
def main():
 ap=argparse.ArgumentParser()
 op=ap.add_mutually_exclusive_group(required=True)
 op.add_argument("--check",action="store_true")
 op.add_argument("--report",action="store_true")
 ap.add_argument("--pft-table",type=Path,default=CAND)
 ap.add_argument("--report-root",type=Path,default=BASE)
 a=ap.parse_args()
 rows=read(a.pft_table)
 expected={"BR-Ma2","CA-Ca3","CA-Cbo","CA-LP1","CA-Man","CA-TP1","CA-TP3","CA-TP4","US-Aud","US-Bar"}
 if len(rows)!=10 or {x["site"] for x in rows}!=expected:raise SystemExit("Invalid ten-site candidate PFT list")
 if not PARAM.is_file():raise SystemExit("FATES parameter file missing")
 j=json.loads(PARAM.read_text());n=int(j["dimensions"]["fates_pft"])
 names=[str(v) for v in j["parameters"]["fates_pftname"]["data"]]
 if len(names)!=n:raise SystemExit("Invalid FATES PFT list")
 for row in rows:
  f=row["exact_FATES_PFTs_and_slot"].split(";")
  for name in f:
   if name.startswith("BARE_GROUND:"):continue
   bit=name.split(":")
   if len(bit)<2 or not bit[0].isdigit() or int(bit[0])>n or bit[1].split(" [")[0]!=names[int(bit[0])-1]:
    raise SystemExit("PFT target mismatch: "+row["site"]+" "+name)
 latest={}
 for prefix in ("stage21","stage25","stage31","stage32","stage33","stage34","stage35","stage36"):
  candidates=sorted(x for x in a.report_root.glob(prefix+"_*") if x.is_dir())
  latest[prefix]=str(candidates[-1]) if candidates else "NOT_FOUND"
 print("STAGE38 PFT: 10/10 crosswalk names/slots exist in actual 14-PFT parameter file")
 for k,v in latest.items():print("PRIOR REPORT",k,v)
 print("STAGE38 PRODUCTION READINESS: HOLD, unresolved gates=%d"%len(ISSUES))
 for k,detail in ISSUES.items():print("  HOLD",k,detail)
 if a.check:
  print("CHECK ONLY: no reports or inputs written");return
 d=a.report_root/("stage38_pre_spinup_readiness_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
 d.mkdir(parents=True,exist_ok=False)
 (d/"readiness.json").write_text(json.dumps({"sites":sorted(expected),"pft_evidence_table":str(a.pft_table),
   "all_ten_pft_candidates_defined":True,"pft_actual_model_initialization_verified":False,
   "production_spinup_ready":False,"blockers":ISSUES,"prior_reports":latest},indent=2)+"\n")
 print("REPORT DIR:",d)
 print("NO changes to surface, forcing, model, Slurm or Git.")
if __name__=="__main__":main()

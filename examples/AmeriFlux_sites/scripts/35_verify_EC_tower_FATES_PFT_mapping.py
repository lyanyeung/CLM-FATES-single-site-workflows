#!/usr/bin/env python3
"""Stage35 READ-ONLY: independently verify exact FATES paramfile names and EC targets.

Never changes JSON, namelists, source/forcing, surfaces, cases or Slurm.
The target PFT ledger is a scientific functional-group hypothesis, not a
measured PFT composition nor a configured FATES model.
"""
import argparse,csv,hashlib,json,re
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/"metadata"/"Batch01_EC_to_FATES_PFT_candidates_v1.tsv"
PARAM=Path("/iridisfs/scratch/ly3n24/CLM_FATES/CTSM/src/fates/parameter_files/fates_params_default.json")
REPORT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
SITES={"BR-Ma2","CA-Ca3","CA-Cbo","CA-LP1","CA-Man","CA-TP1","CA-TP3","CA-TP4","US-Aud","US-Bar"}
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def readtab(p):
 with p.open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f,delimiter="\t"))
def write(p,rows,keys):
 with p.open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
def pft_names(param):
 j=json.loads(param.read_text())
 n=int(j["dimensions"]["fates_pft"])
 v=j["parameters"]["fates_pftname"]
 if v["dims"]!=["fates_pft"] or len(v["data"])!=n:raise RuntimeError("Invalid FATES PFT dimension")
 names=[str(x).strip() for x in v["data"]]
 if len(set(names))!=n:raise RuntimeError("Duplicate FATES PFT names")
 return names
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 op=ap.add_mutually_exclusive_group(required=True);op.add_argument("--check",action="store_true");op.add_argument("--audit",action="store_true")
 ap.add_argument("--paramfile",type=Path,default=PARAM);ap.add_argument("--ledger",type=Path,default=LEDGER);ap.add_argument("--report-root",type=Path,default=REPORT)
 ap.add_argument("--case",type=Path,help="Existing reference CIME case for read-only settings review")
 a=ap.parse_args()
 if not a.paramfile.is_file():raise RuntimeError("Missing real FATES parameter file: "+str(a.paramfile))
 rows=readtab(a.ledger)
 if len(rows)!=10 or {r["site"] for r in rows}!=SITES:raise RuntimeError("Expected 10 unique Batch01 target sites")
 names=pft_names(a.paramfile);lookup={name:i+1 for i,name in enumerate(names)}
 print("STAGE35 PREFLIGHT: sites=10 FATES_PFTs=%d"%len(names))
 print("PARAM SHA256:",sha(a.paramfile));print("TARGET SHA256:",sha(a.ledger))
 if a.case:
  nml=a.case/"CaseDocs"/"lnd_in"
  if not nml.is_file():raise RuntimeError("CaseDocs/lnd_in not found: "+str(nml))
  text=nml.read_text(errors="replace")
  print("REFERENCE CASE:",a.case)
  for line in text.splitlines():
   if re.match(r"^\s*(fates_paramfile|use_fates\S*|fates\S*|create_crop_landunit|use_crop)\s*=",line,re.I):
    print("CASE_SETTING:",line.strip()[:240])
  print("REFERENCE CASE SETTINGS ARE CONTEXT ONLY; NOT PROOF OF NEW BATCH EFFECTIVE CONFIGURATION.")
 if a.check:
  print("CHECK ONLY: no reports or model edits");return
 outrows=[]
 for r in rows:
  primary=r["primary_target_fates_pft"].strip()
  others=[x for x in r["additional_or_alternative_pft_candidates"].split(";") if x]
  missing=[x for x in ([primary] if primary else [])+others if x not in lookup]
  if missing:raise RuntimeError(r["site"]+" candidate names NOT IN PARAMFILE: "+repr(missing))
  status="OPEN_C3_C4_ECOLOGY" if not primary else "SECONDARY_PFT_EVIDENCE_OPEN" if others else "PRIMARY_FUNCTIONAL_TARGET_CANDIDATE"
  rec=dict(site=r["site"],primary_candidate=primary,primary_fates_slot_1based=lookup.get(primary,""),
   alternatives=";".join(others),alternative_slots_1based=";".join(str(lookup[x]) for x in others),
   science_status=status,verified_paramfile_PFT_existence="YES",PFT_site_selection_scientifically_approved="NO",
   fates_active_PFTs_configured="NO",tower_PFT_fractions_proven="NO",
   case_initialization_verified_for_Batch01="NO",evidence=r["ecological_justification"])
  outrows.append(rec)
  print("%-7s primary=%-44s slot=%-3s alternatives=%-50s %s"%(r["site"],primary or "UNRESOLVED",rec["primary_fates_slot_1based"],rec["alternatives"] or "-",status))
 stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
 out=a.report_root/("stage35_EC_target_exact_FATES_PFT_crosswalk_"+stamp);out.mkdir(parents=True,exist_ok=False)
 write(out/"01_ten_site_target_PFT_CROSSWALK_NOT_APPROVED.csv",outrows,list(outrows[0]))
 write(out/"02_exact_parameterfile_FATES_names.csv",
       [dict(slot_1based=i+1,name=name,paramfile_sha256=sha(a.paramfile)) for i,name in enumerate(names)],
       ["slot_1based","name","paramfile_sha256"])
 print("STAGE35 SUMMARY: sites=10 names_exist=10 final_config_approved=0 ambiguous_US_Aud=1")
 print("REPORT DIR:",out)
 print("READ-ONLY: no paramfile, CIME, DATM, surface or Slurm changed.")
if __name__=="__main__":main()

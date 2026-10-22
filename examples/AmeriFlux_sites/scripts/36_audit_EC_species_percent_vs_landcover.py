#!/usr/bin/env python3
"""Stage36 read-only EC vegetation percentage provenance audit.

Read original pinned BIF SPP_* metadata, literature species-percent evidence,
and the existing Stage33 CTSM grid surface report. NEVER equate stem counts,
canopy cover, basal area, biomass share, or grid PCT_NAT_PFT percentages.
Never assign FATES PFT fractions automatically.
"""
import argparse,csv,hashlib
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT.parent/"AmeriFlux_MultiSite_10"
EVIDENCE=ROOT/"metadata"/"Batch01_published_tower_species_percent_evidence_v1.tsv"
SITES_ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
REPORTS=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
SPP_MARKERS=("SPP","VEG_COVER","VEG_SPECIES","SPECIES_COVER")
def read(p,sep=","):
 with p.open(newline="",encoding="utf-8-sig",errors="replace") as f:
  d=csv.DictReader(f,delimiter=sep)
  if not d.fieldnames:raise RuntimeError("Missing CSV header: "+str(p))
  return list(d)
def write(p,rows,fields):
 with p.open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(rows)
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 g=ap.add_mutually_exclusive_group(required=True)
 g.add_argument("--check",action="store_true");g.add_argument("--audit",action="store_true")
 ap.add_argument("--sites-tsv",type=Path,default=BATCH/"sites.tsv")
 ap.add_argument("--published-evidence",type=Path,default=EVIDENCE)
 ap.add_argument("--sites-root",type=Path,default=SITES_ROOT)
 ap.add_argument("--report-root",type=Path,default=REPORTS)
 ap.add_argument("--stage33-dir",type=Path,default=None)
 a=ap.parse_args()
 sites=read(a.sites_tsv,"\t");literature=read(a.published_evidence,"\t")
 if len(sites)!=10 or len({x["site"] for x in sites})!=10:raise RuntimeError("Need 10 distinct sites")
 if set(x["site"] for x in literature)-set(x["site"] for x in sites):raise RuntimeError("Literature site outside this batch")
 candidates=sorted(p for p in a.report_root.glob("stage33_ten_site_surface_ecology_*")
                   if (p/"01_ten_site_surface_landunit_and_ecology_matrix.csv").is_file())
 stage33=a.stage33_dir or (candidates[-1] if candidates else None)
 if stage33 is None:raise RuntimeError("No completed Stage33 land-cover CSV; supply --stage33-dir")
 land=read(stage33/"01_ten_site_surface_landunit_and_ecology_matrix.csv")
 landby={r["site"]:r for r in land}
 if len(landby)!=10:raise RuntimeError("Stage33 site count mismatch")
 src={}
 for r in sites:
  site=r["site"]
  directory=a.sites_root/site/"forcing"/"raw"/r["package"]
  paths=sorted(x for x in directory.glob("*.csv") if "_BIF_" in x.name.upper())
  if len(paths)!=1:raise RuntimeError(site+" BIF count="+str(len(paths)))
  src[site]=paths[0]
  print("CHECK OK",site,paths[0].name,flush=True)
 print("STAGE36 PREFLIGHT: 10/10 BIF + Stage33",stage33,flush=True)
 if a.check:return
 bf=[];review=[];igbp=[]
 litby=Counter(x["site"] for x in literature)
 for r in sites:
  site=r["site"];rows=read(src[site])
  for x in rows:
   variable=str(x.get("VARIABLE") or "").strip()
   if not any(variable.upper().startswith(prefix) for prefix in SPP_MARKERS):continue
   bf.append(dict(site=site,BIF_variable=variable,BIF_datavalue=str(x.get("DATAVALUE") or ""),
       BIF_group=str(x.get("GROUP_ID") or ""),source_BIF=str(src[site]),
       value_interpretation="UNVERIFIED_VARIABLE_OR_DENOMINATOR"))
  matching=[x for x in bf if x["site"]==site]
  matrix=landby[site]
  review.append(dict(site=site,working_IGBP=matrix.get("working_ec_igbp",""),
   BIF_species_related_metadata_rows=len(matching),
   published_percentage_evidence_rows=litby[site],
   reference_surface_natveg_pct=matrix.get("PCT_NATVEG",""),
   reference_surface_crop_pct=matrix.get("PCT_CROP",""),
   CLM_tree_pct_within_natveg=matrix.get("host_tree_pct_of_natveg",""),
   CLM_grass_pct_within_natveg=matrix.get("host_grass_pct_of_natveg",""),
   tower_PFT_cover_pct="NOT_VALIDATED",
   FATES_initial_PFT_shares="NOT_SET",
   recommended_action=("REVIEW_BIF_AND_LITERATURE_DENOMINATORS" if matching or litby[site] else
      "FIND_SITE_SPECIES_COVER_SURVEY_OR_DOCUMENT_SENSITIVITY"),
   final_science_gate="HOLD"))
  print("%-7s BIF_species_rows=%4d published_rows=%2d CROP=%s tower_PFT_percent=%s"%
   (site,len(matching),litby[site],matrix.get("PCT_CROP","?"),"NOT_VALIDATED"),flush=True)
 stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
 out=a.report_root/("stage36_tower_species_percent_evidence_"+stamp);out.mkdir(parents=True,exist_ok=False)
 write(out/"01_original_BIF_species_metadata.csv",bf,
  ["site","BIF_variable","BIF_datavalue","BIF_group","source_BIF","value_interpretation"])
 write(out/"02_published_species_percent_with_provenance.csv",literature,
  ["site","evidence_year","reported_species_or_PFT","reported_percentage",
   "percentage_denominator","functional_PFT_target","reference_url",
   "interpretation_note","direct_FATES_initial_fraction_approved"])
 write(out/"03_tower_percent_vs_reference_surface_review.csv",review,list(review[0]))
 print("STAGE36 SUMMARY: sites=10 BIF_species_rows=%d published_percentage_rows=%d science_approved=0"%
       (len(bf),len(literature)))
 print("REPORT DIR:",out)
 print("READ ONLY: no source, surface, FATES, DATM or Slurm edits.")
if __name__=="__main__":main()

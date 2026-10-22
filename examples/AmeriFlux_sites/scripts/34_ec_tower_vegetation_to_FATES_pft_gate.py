#!/usr/bin/env python3
"""Stage34: tower-vegetation-first scientific gate for AmeriFlux -> FATES.

EC tower vegetation is the target ecological standard; never take dominant
CTSM grid-cell PFT as a substitute for real tower vegetation. This script
does not assume that a broad IGBP label identifies an exact FATES PFT name.
It resolves the exact FATES PFT names and configuration from a PROVIDED,
existing JSON fates_paramfile. Draft mapping is produced only on --audit
and never changes surface, namelist, forcing, CIME case, model or jobs.

No silent one-PFT restriction: FATES initial conditions, viable biogeographic
PFTs, traits and cohort/seed configuration must be validated in the *actual*
run case. This is pre-run evidence and decision table, NOT FATES editing.
"""
from __future__ import annotations
import argparse,csv,json,hashlib,re
from pathlib import Path
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parents[1]
EVIDENCE=HERE/"metadata"/"Batch01_tower_vegetation_evidence_20261022.tsv"
REPORT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
EXPECTED_SITES={"BR-Ma2","CA-Ca3","CA-Cbo","CA-LP1","CA-Man","CA-TP1","CA-TP3","CA-TP4","US-Aud","US-Bar"}

def read_table(p):
    with p.open(encoding="utf-8-sig",newline="") as f:
        dr=csv.DictReader(f,delimiter="\t")
        if not dr.fieldnames or not {"site","official_IGBP","functional_group","observed_tower_vegetation","official_source_url","evidence_status"}<=set(dr.fieldnames):
            raise RuntimeError("Evidence TSV schema mismatch")
        rs=list(dr)
    if {r["site"] for r in rs}!=EXPECTED_SITES or len(rs)!=10:raise RuntimeError("Expected exactly 10 unique Batch01 sites")
    return rs

def digest(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def load_names(p):
    if not p or not p.is_file():return None,"NO_EXISTING_FATES_PARAMFILE_PROVIDED"
    if p.suffix.lower()!=".json":return None,"NON_JSON_PARAMFILE_MANUAL_INSPECTION_REQUIRED"
    try:
        j=json.loads(p.read_text(encoding="utf-8"))
        n=int(j["dimensions"]["fates_pft"])
        x=j["parameters"]["fates_pftname"]
        if x["dims"]!=["fates_pft"] or len(x["data"])!=n:raise ValueError("fates_pft names/shape mismatch")
        names=[str(v).strip() for v in x["data"]]
        if any(not x for x in names) or len(set(names))!=len(names):raise ValueError("Empty/duplicate names")
        return names,"FATES_NAMES_READ_OK"
    except Exception as exc:
        return None,"PARAMFILE_PARSE_ERROR:"+type(exc).__name__+":"+str(exc)[:100]

def matched_caution(group,names):
    """Only *textual* candidate selection. No ecological equivalence asserted."""
    if not names:return [],"NO_PARAMFILE_NO_MAPPING"
    group_tokens={
        "EVERGREEN_BROADLEAF_TROPICAL":("tropical","broadleaf","evergreen"),
        "EVERGREEN_NEEDLELEAF":("needleleaf","evergreen"),
        "EVERGREEN_NEEDLELEAF_TEMPERATE":("needleleaf","evergreen","temperate"),
        "EVERGREEN_NEEDLELEAF_BOREAL":("needleleaf","evergreen","boreal"),
        "DECIDUOUS_BROADLEAF_TEMPERATE":("broadleaf","deciduous","temperate"),
        "GRASSLAND":("grass",),
    }
    tokens=group_tokens.get(group)
    if not tokens:return [],"GROUP_HAS_NO_SAFE_LEXICAL_RULE"
    # Store *all* names for human evaluation, not just a guessed match:
    candidates=[]
    for i,name in enumerate(names):
        normalized=re.sub(r"[^a-z0-9]+"," ",name.lower())
        hits=sum(t in normalized for t in tokens)
        if hits>=max(1,len(tokens)-1):
            candidates.append(f"{i+1}:{name}")
    return candidates,("LEXICAL_SUGGESTIONS_ONLY_NOT_VERIFIED" if candidates
                       else "NO_TEXTUAL_MATCH_MANUAL_PFT_TRAIT_MAPPING_REQUIRED")

def write_csv(path,rows):
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),extrasaction="ignore")
        writer.writeheader();writer.writerows(rows)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--audit",action="store_true")
    ap.add_argument("--paramfile",type=Path,help="Exact effective existing fates_paramfile JSON; not inferred")
    ap.add_argument("--site-evidence",type=Path,default=EVIDENCE)
    ap.add_argument("--report-root",type=Path,default=REPORT)
    a=ap.parse_args()
    evidence=read_table(a.site_evidence)
    names,param_state=load_names(a.paramfile)
    print("STAGE34 PREFLIGHT: 10 tower vegetation evidence records")
    print("SOURCE_EVIDENCE_SHA256:",digest(a.site_evidence))
    print("FATES_PARAM_STATUS:",param_state)
    if names:
        print("FATES PARAMETER PFTs:"," | ".join(f"{i+1}:{n}" for i,n in enumerate(names)))
        print("FATES_PARAM_SHA256:",digest(a.paramfile))
    if a.check:
        print("CHECK ONLY: no reports, FATES files, cases or jobs written")
        return
    records=[]
    for r in evidence:
        hits,state=matched_caution(r["functional_group"],names)
        records.append(dict(site=r["site"],tower_IGBP=r["official_IGBP"],
            actual_tower_vegetation=r["observed_tower_vegetation"],
            functional_group=r["functional_group"],
            known_site_history=r["known_disturbance_or_age"],
            species_information=r["confirmed_species_evidence"],
            unresolved_ecology=r["open_scientific_questions"],
            original_source=r["official_source_url"],
            evidence_status=r["evidence_status"],
            fates_paramfile=str(a.paramfile or ""),
            FATES_PFT_names_source_status=param_state,
            FATES_PFT_textual_candidates=";".join(hits),
            PFT_candidate_interpretation=state,
            FATES_allowed_PFTs_approved="NO",
            FATES_initial_PFT_approved="NO",
            tower_surface_footprint_approved="NO",
            selected_actual_FATES_PFT_names="",
            verified_site_vegetation_reference="",
            reviewer="",
            final_model_configuration="HOLD_VERIFY_PARAMFILE_BIOGEOGRAPHY_AND_INITIALIZATION"))
        print("%-7s tower=%-35s group=%-33s FATES=%s"%
              (r["site"],r["observed_tower_vegetation"][:35],
               r["functional_group"],state),flush=True)
    output=a.report_root/("stage34_EC_tower_real_PFT_to_FATES_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    output.mkdir(parents=True,exist_ok=False)
    write_csv(output/"01_tower_vegetation_FATES_PFT_mapping_DECISION_MATRIX.csv",records)
    if names:
        write_csv(output/"02_actual_fates_paramfile_pft_names.csv",
                  [dict(slot=i+1,actual_fates_pft_name=n,source=str(a.paramfile),source_sha256=digest(a.paramfile))
                   for i,n in enumerate(names)])
    (output/"03_safety_gate.json").write_text(json.dumps({
        "site_vegetation_is_ecological_target":True,
        "CLM_surface_dominant_PFT_is_not_FATES_initial_PFT":True,
        "source_evidence_sha256":digest(a.site_evidence),
        "fates_paramfile_sha256":digest(a.paramfile) if names else None,
        "site_count":len(records),
        "mapped_approved_count":0,
        "model_files_created":False,
        "requires_after_case_creation":[
            "Verify effective fates_paramfile and names, actual functional traits/biogeography",
            "Verify cold-start initialization / prescribed PFT modes and seed/viability",
            "Check host natural vegetation vs crop/wetland masks at EC footprint",
            "Verify actual FATES PFT initialization and record model outcome"],
        "warning":"A tower IGBP label, BASE heights or lexical PFT candidate never alone constrains FATES active PFTs."
    },indent=2)+"\n",encoding="utf-8")
    print("STAGE34 SUMMARY: sites=10, EC_target_entries=10, FATES_mapping_approved=0")
    print("REPORT DIR:",output)
    print("READ ONLY SOURCE AUDIT. NO FATES, SURFACE, DATM OR SLURM CHANGES.")

if __name__=="__main__":
    main()

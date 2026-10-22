#!/usr/bin/env python3
"""AmeriFlux Batch01 Stage33: read-only land-cover / host CLM PFT audit.

Uses existing point surfaces and exact pinned source BIF. Does NOT produce
surface data, adjust cropland, fabricate tower-footprint PFT, or claim the
CLM PCT_NAT_PFT vector is an actual FATES PFT initialization.

Distinguishes three layers:
 (1) tower/ecosystem IGBP: repo EXPECTED_IGBP working labels vs raw BIF;
 (2) host CTSM surface landunit and natural CLM PFT fractions at grid point;
 (3) initial FATES PFTs: UNKNOWN until a real model case, effective
     fates_paramfile, and initialization strategy are inspected.

'REVIEW' flags are heuristics, not proof that the surface is wrong.
'--check' checks exact inputs; '--audit' reads surfaces and creates only
timestamped reports under experiments/AmeriFlux_MultiSite_10/reports.
No model jobs, NetCDF, inputdata, user_mods, or existing reports modified.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from netCDF4 import Dataset

BATCH=Path(__file__).resolve().parents[2]
DEFAULT_SITES=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")
DEFAULT_REPORTS=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")

# Working research classification from Batch01 Stage04a; verify against
# real BIF and tower documentation before declaring an ecological identity.
WORKING_IGBP={
 "BR-Ma2":"EBF","CA-Ca3":"ENF","CA-Cbo":"DBF","CA-LP1":"ENF",
 "CA-Man":"ENF","CA-TP1":"ENF","CA-TP3":"ENF","CA-TP4":"ENF",
 "US-Aud":"GRA","US-Bar":"DBF",
}
LANDUNITS=("PCT_NATVEG","PCT_CROP","PCT_LAKE","PCT_WETLAND",
           "PCT_GLACIER","PCT_URBAN")
PFT_GROUPS={
 "BARE_GROUND":[0],"CLM_TREE_PFT_INDICES":list(range(1,9)),
 "CLM_SHRUB_PFT_INDICES":list(range(9,12)),
 "CLM_GRASS_PFT_INDICES":list(range(12,15)),
}
# CLM index 15 exists in some 16-PFT datasets: leave its meaning unassigned.
HEURISTIC_CROP_THRESHOLD=20.0
HEURISTIC_FOREST_THRESHOLD=50.0
HEURISTIC_GRASS_THRESHOLD=50.0



def write(path,records,columns):
    """Write a diagnostic-only CSV to the new, unique Stage33 report directory."""
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=columns,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def read_manifest(p):
    with p.open(newline="",encoding="utf-8") as f:
        rd=csv.DictReader(f,delimiter="\t")
        if not rd.fieldnames or not {"site","package","first_year","last_year"}<=set(rd.fieldnames):
            raise RuntimeError("Expected exact-release manifest columns")
        rows=list(rd)
    if len(rows)!=10 or len({x["site"] for x in rows})!=10:
        raise RuntimeError("Expected ten distinct Batch01 sites")
    if {x["site"] for x in rows}!=set(WORKING_IGBP):
        raise RuntimeError("Source manifest differs from Batch01 working IGBP table")
    return rows


def file_hash(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(4*1024*1024),b""):h.update(b)
    return h.hexdigest()


def find_inputs(row,sites_root):
    site=row["site"]
    source=sites_root/site/"forcing"/"raw"/row["package"]
    bifs=sorted(p for p in source.glob("*.csv") if "_BIF_" in p.name.upper())
    surface_folder=sites_root/site/"subset_data"
    surfs=sorted(surface_folder.glob("surfdata*.nc"))
    if len(bifs)!=1 or len(surfs)!=1:
        raise RuntimeError("%s: BIF=%d surface=%d (expected each exactly one)"%
                           (site,len(bifs),len(surfs)))
    if not (surface_folder/"user_mods").is_dir():
        raise RuntimeError(site+": subset user_mods missing")
    if not (sites_root/site/(site+"_data.cfg")).is_file():
        raise RuntimeError(site+": point-surface config missing")
    return bifs[0],surfs[0]


def raw_igbp_evidence(bif):
    values={}
    with bif.open("r",encoding="utf-8-sig",errors="replace",newline="") as f:
        rd=csv.DictReader(f)
        if not rd.fieldnames or not {"VARIABLE","DATAVALUE"}<=set(rd.fieldnames):
            raise RuntimeError("Unexpected BIF fields "+str(bif))
        for r in rd:
            key=str(r.get("VARIABLE") or "").strip().upper()
            val=str(r.get("DATAVALUE") or "").strip()
            if key in ("IGBP","IGBP_CLASS","IGBP_VEGTYPE") and val:
                values.setdefault(key,set()).add(val)
    return values


def scalar(nc,field):
    if field not in nc.variables:return None
    ar=np.ma.filled(nc.variables[field][:],np.nan)
    vals=np.asarray(ar,dtype=np.float64).ravel()
    if field=="PCT_URBAN":
        if not vals.size or not np.isfinite(vals).all():
            raise RuntimeError(field+": contains NaN/Inf or empty")
        return float(vals.sum())
    if vals.size!=1 or not np.isfinite(vals[0]):
        raise RuntimeError(field+": expected single finite scalar")
    return float(vals[0])


def pft_vector(nc):
    if "PCT_NAT_PFT" not in nc.variables:
        raise RuntimeError("PCT_NAT_PFT missing")
    var=nc.variables["PCT_NAT_PFT"]
    dims=var.dimensions
    axes=[i for i,d in enumerate(dims) if "pft" in d.lower()]
    if len(axes)!=1:
        raise RuntimeError("PCT_NAT_PFT has ambiguous PFT axis: "+repr(dims))
    a=np.ma.filled(var[:],np.nan)
    a=np.asarray(a,dtype=np.float64)
    a=np.moveaxis(a,axes[0],0)
    if int(np.prod(a.shape[1:]))!=1:
        raise RuntimeError("PCT_NAT_PFT has non-singleton spatial dimensions "+repr(dims))
    out=a.reshape(a.shape[0])
    if len(out) not in (15,16):
        raise RuntimeError("Unexpected host natural PFT count "+str(len(out)))
    if not np.isfinite(out).all() or np.min(out)<-0.01 or np.max(out)>100.01:
        raise RuntimeError("Host PFT array contains invalid percentages")
    if abs(float(out.sum())-100)>0.5:
        raise RuntimeError("Host PCT_NAT_PFT sum %.5f not 100"%out.sum())
    return out,dims


def severity(flags,struct_errors):
    if struct_errors:return "STRUCTURAL_FAIL_STOP"
    if "BIF_IGBP_CONFLICT" in flags:return "SCIENCE_REVIEW_BIF_ECOLOGY"
    if "HIGH_CROP_AT_FOREST_TOWER" in flags:return "SCIENCE_REVIEW_GRID_FOREST_MISMATCH"
    if "TOWER_TYPE_VS_HOST_NAT_PFT_MISMATCH" in flags:return "SCIENCE_REVIEW_GRID_VEGETATION"
    if "CROP_FRACTION_GT20_PCT" in flags:return "SCIENCE_REVIEW_CROPLAND"
    return "STRUCTURE_OK_ECOLOGICAL_REVIEW_PENDING"


def main():
    p=argparse.ArgumentParser(description=__doc__)
    op=p.add_mutually_exclusive_group(required=True)
    op.add_argument("--check",action="store_true")
    op.add_argument("--audit",action="store_true")
    p.add_argument("--sites-root",type=Path,default=DEFAULT_SITES)
    p.add_argument("--report-root",type=Path,default=DEFAULT_REPORTS)
    p.add_argument("--sites-tsv",type=Path,default=BATCH/"sites.tsv")
    args=p.parse_args()
    manifest=read_manifest(args.sites_tsv)
    inputs={}
    for r in manifest:
        site=r["site"]
        bif,surf=find_inputs(r,args.sites_root)
        inputs[site]=(bif,surf)
        print("CHECK OK %-7s BIF=%s surface=%s"%
              (site,bif.name,surf.name),flush=True)
    print("STAGE33 PREFLIGHT: 10/10 exact BIF and CTSM point surfaces",flush=True)
    if args.check:
        print("CHECK ONLY: no files written or sites modified")
        return

    rows=[];vector_rows=[];evidence=[];actions=[];hashes=[]
    for r in manifest:
        site=r["site"];label=WORKING_IGBP[site]
        bif,surf=inputs[site]
        flags=[];errors=[]
        raw=raw_igbp_evidence(bif)
        rawlabels=sorted({label.upper() for ls in raw.values() for label in ls})
        evidence.append(dict(site=site,bif=str(bif),
                             working_ec_igbp=label,
                             all_igbp_raw="|".join(rawlabels),
                             raw_igbp_fields="|".join(sorted(raw)),
                             raw_site_igbp_status=(
                                 "NOT_PRESENT_DO_NOT_CLAIM_VERIFIED" if not rawlabels
                                 else "AMBIGUOUS_REVIEW" if len(rawlabels)>1
                                 else "ONE_BIF_LABEL_REVIEW")))
        if len(rawlabels)>1 or (rawlabels and label not in rawlabels):
            flags.append("BIF_IGBP_CONFLICT")
        if not rawlabels:
            flags.append("BIF_IGBP_NOT_IN_EXACT_RELEASE")
        data=dict(site=site,working_ec_igbp=label,
                  original_BIF_igbp="|".join(rawlabels),
                  BIF_type_provenance="RAW_BIF" if rawlabels else "WORKING_IGBP_TABLE",
                  surface=str(surf),surface_reference_year=2000,
                  source_first_year=int(r["first_year"]),
                  source_last_year=int(r["last_year"]))
        for key in LANDUNITS:data[key]=""
        data.update(host_tree_pct_of_natveg="",host_shrub_pct_of_natveg="",
                    host_grass_pct_of_natveg="",host_bare_pct_of_natveg="",
                    host_unmapped_index15_pct="",grid_tree_total_area_pct="",
                    grid_grass_total_area_pct="",
                    host_dominant_clm_pft_index="",host_dominant_clm_pct_of_natveg="",
                    surface_landunit_sum_pct="",host_clm_natural_pft_count="")
        try:
            with Dataset(surf,"r") as nc:
                for field in LANDUNITS:
                    value=scalar(nc,field)
                    if value is None:
                        flags.append("SURFACE_MISSING_"+field)
                    elif value<-.01 or value>100.01:
                        raise RuntimeError(field+" outside 0..100 pct")
                    else:
                        data[field]=round(value,4)
                if all(isinstance(data[k],(int,float)) for k in LANDUNITS):
                    total=sum(data[k] for k in LANDUNITS)
                    data["surface_landunit_sum_pct"]=round(total,4)
                    if abs(total-100)>.5:
                        raise RuntimeError("Landunit fractions sum "+str(total))
                else:
                    errors.append("NOT_ALL_LANDUNIT_KEYS_PRESENT")
                v,dims=pft_vector(nc)
                data["host_clm_natural_pft_count"]=len(v)
                groups={k:float(v[idx].sum()) for k,idx in PFT_GROUPS.items()}
                data["host_tree_pct_of_natveg"]=round(groups["CLM_TREE_PFT_INDICES"],4)
                data["host_shrub_pct_of_natveg"]=round(groups["CLM_SHRUB_PFT_INDICES"],4)
                data["host_grass_pct_of_natveg"]=round(groups["CLM_GRASS_PFT_INDICES"],4)
                data["host_bare_pct_of_natveg"]=round(groups["BARE_GROUND"],4)
                data["host_unmapped_index15_pct"]=round(float(v[15]),4) if len(v)==16 else 0
                ii=int(np.argmax(v))
                data["host_dominant_clm_pft_index"]=ii
                data["host_dominant_clm_pct_of_natveg"]=round(float(v[ii]),4)
                if isinstance(data["PCT_NATVEG"],(int,float)):
                    data["grid_tree_total_area_pct"]=round(
                        data["PCT_NATVEG"]*data["host_tree_pct_of_natveg"]/100,4)
                    data["grid_grass_total_area_pct"]=round(
                        data["PCT_NATVEG"]*data["host_grass_pct_of_natveg"]/100,4)
                for j,val in enumerate(v):
                    vector_rows.append(dict(site=site,Host_CLM_natpft_index=j,
                        host_pct_within_natural_vegetation=round(float(val),6),
                        surface_pft_dimension=";".join(dims),
                        ecological_name_status="CLM_HOST_INDEX_DO_NOT_LABEL_AS_FATES_PFT",
                        actual_FATES_PFT="UNKNOWN_NO_CASE_OR_PARAMFILE"))
                if len(v)==16:flags.append("EXTRA_HOST_PFT_INDEX15_MEANING_UNVERIFIED")
                if label in ("EBF","ENF","DBF","MF") and data["host_tree_pct_of_natveg"]<HEURISTIC_FOREST_THRESHOLD:
                    flags.append("TOWER_TYPE_VS_HOST_NAT_PFT_MISMATCH")
                if label=="GRA" and data["host_grass_pct_of_natveg"]<HEURISTIC_GRASS_THRESHOLD:
                    flags.append("TOWER_TYPE_VS_HOST_NAT_PFT_MISMATCH")
                if isinstance(data["PCT_CROP"],(int,float)) and data["PCT_CROP"]>HEURISTIC_CROP_THRESHOLD:
                    flags.append("CROP_FRACTION_GT20_PCT")
                    if label in ("EBF","ENF","DBF","MF"):
                        flags.append("HIGH_CROP_AT_FOREST_TOWER")
                if data.get("PCT_NATVEG")!="" and data["PCT_NATVEG"]<50:
                    flags.append("LOW_GRID_NATVEG_LT50_PCT")
        except Exception as exc:
            errors.append(type(exc).__name__+": "+str(exc))
        data["FATES_PFT_source"]="NOT_CREATED_OR_NOT_VERIFIED_CASE"
        data["FATES_parameter_pft_names"]="UNKNOWN"
        data["initial_FATES_dominant_PFT"]="UNKNOWN_NO_MODEL_CASE"
        data["ecological_site_footprint_verified"]="NO"
        data["flags"]="|".join(sorted(set(flags)))
        data["structural_issues"]="|".join(errors)
        data["pre_spinup_status"]=severity(flags,errors)
        rows.append(data)
        hashes.extend([
            dict(site=site,kind="exact_release_BIF",path=str(bif),sha256=file_hash(bif)),
            dict(site=site,kind="CTSM_point_surface",path=str(surf),sha256=file_hash(surf))])
        actions.append(dict(site=site,site_type=label,
            review_priority=("HIGH" if any(k in flags for k in
                    ("HIGH_CROP_AT_FOREST_TOWER","TOWER_TYPE_VS_HOST_NAT_PFT_MISMATCH",
                     "BIF_IGBP_CONFLICT")) else
                "NORMAL_MANUAL_REVIEW"),
            host_cover_flags=data["flags"],required_action=(
                "VERIFY_TOWER_ECOSYSTEM_AND_FOOTPRINT; COMPARE_SURFACE_REFERENCE_2000; "
                "VERIFY_FATES_PARAMFILE_PFT_SET_AND_CIME_INITIALIZATION; "
                "DECIDE_RETAIN_GRID_VS_SITE_SPECIFIC_SURFACE"),
            evidence_for_surface_choice="",
            surface_scientific_approval="NO",
            selected_FATES_PFT_names="NOT_YET_DEFINED",
            reviewer_decision="HOLD"))
        print("  %-7s tower=%-3s NAT=%-6s CROP=%-6s CLM_TREE=%-6s CLM_GRASS=%-6s  %s"%
              (site,label,data["PCT_NATVEG"],data["PCT_CROP"],
               data["host_tree_pct_of_natveg"],data["host_grass_pct_of_natveg"],
               data["pre_spinup_status"]),flush=True)
    timestamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out=args.report_root/("stage33_ten_site_surface_ecology_"+timestamp)
    out.mkdir(parents=True,exist_ok=False)
    write(out/"01_ten_site_surface_landunit_and_ecology_matrix.csv",rows,list(rows[0]))
    write(out/"02_host_CLM_natpft_vectors_NOT_FATES.csv",vector_rows,
          ["site","Host_CLM_natpft_index","host_pct_within_natural_vegetation",
           "surface_pft_dimension","ecological_name_status","actual_FATES_PFT"])
    write(out/"03_original_BIF_IGBP_source_check.csv",evidence,list(evidence[0]))
    write(out/"04_footprint_and_FATES_science_decision_TEMPLATE.csv",actions,list(actions[0]))
    write(out/"05_BIF_surface_SHA256.csv",hashes,list(hashes[0]))
    provenance=dict(stage="AmeriFlux Batch01 Stage33",mode="READ_ONLY",
        source="Exact pinned release BIF + 2000 reference point surface",
        no_surface_writes=True,no_CIME_case_exists_in_this_study=True,
        host_PFT_indices_not_FATES=True,
        FATES_initial_PFT_not_deducible_from_host_surface=True,
        percentages="PCT_NAT_PFT is percent WITHIN natural-vegetation landunit; "
                    "multiply by PCT_NATVEG/100 for approximate full cell coverage",
        review_screen_heuristics=dict(cropland_gt_percent=HEURISTIC_CROP_THRESHOLD,
            forest_natural_share_lt_percent=HEURISTIC_FOREST_THRESHOLD,
            grass_natural_share_lt_percent=HEURISTIC_GRASS_THRESHOLD),
        thresholds_are_scientific_flags_not_pass_fail=True,
        next_steps=["Confirm tower vegetation type/footprint and valid reference year",
                    "Assess surface grid crop vs local footprint and choose policy",
                    "Verify FATES parameter-file PFT list and initialization method when case created",
                    "Approve meteorology + ZBOT, build provisional DATM, run short model test"])
    (out/"06_provenance.json").write_text(json.dumps(provenance,indent=2)+"\n",encoding="utf-8")
    failed=sum(r["pre_spinup_status"]=="STRUCTURAL_FAIL_STOP" for r in rows)
    high=sum(x["review_priority"]=="HIGH" for x in actions)
    print("STAGE33 SUMMARY: sites=10 structural_fail=%d high_ecological_review=%d "
          "FATES_initialized_PFT_verified=0"% (failed,high),flush=True)
    print("REPORT DIR:",out,flush=True)
    print("SCIENCE GATE: HOLD (CLM host PFT != FATES PFT; footprint not verified).")
    print("NO source, surface, forcing, model case or jobs changed.",flush=True)
    if failed:raise SystemExit(2)


if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""OzFlux AU-ASM Stage16 isolated CTSM-2000 REFERENCE surface builder.

--check is strictly read-only. --build-reference writes only to a FRESH
HOME child folder and requires explicit confirmation. No --overwrite.
NO FATES PFT or soil edits, NO existing site-file edits, NO CIME/Slurm.
Generated gridded point surface is REFERENCE ONLY: not a science-approved
Mulga-tower footprint, field soil profile, PFT map or spinup input.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import netCDF4
import numpy as np

SITE="AU-ASM"
LAT=-22.2828
LON=133.2493
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
STAGE15=Path.home()/"ozflux_stage15_20261102T020625Z"
CONFIRM="CREATE_ISOLATED_AU_ASM_REFERENCE_SURFACE_ONLY"
REFERENCE_SURF="surfdata_0.9x1.25_hist_2000_16pfts_c240908.nc"
REFERENCE_MESH="fv0.9x1.25_141008_ESMFmesh.nc"
LAND=("PCT_NATVEG","PCT_CROP","PCT_LAKE","PCT_WETLAND",
      "PCT_GLACIER","PCT_URBAN")
LABELS=("bare_ground","needleleaf_evergreen_temperate_tree",
        "needleleaf_evergreen_boreal_tree","needleleaf_deciduous_boreal_tree",
        "broadleaf_evergreen_tropical_tree","broadleaf_evergreen_temperate_tree",
        "broadleaf_deciduous_tropical_tree","broadleaf_deciduous_temperate_tree",
        "broadleaf_deciduous_boreal_tree","broadleaf_evergreen_temperate_shrub",
        "broadleaf_deciduous_temperate_shrub","broadleaf_deciduous_boreal_shrub",
        "c3_arctic_grass","c3_nonarctic_grass","c4_grass","extra_slot_15_unclassified")

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(2**22),b""):
            h.update(block)
    return h.hexdigest()

def config_text(raw):
    """Pin known, existing CTSM source data only inside [surfdat].

    Old code required one literal "dir = .../ctsm5.4.0" in the WHOLE
    template. Actual CTSM cfg files can already use ctsm5.3.0, have
    different whitespace, or repeat a surfdata directory in [landuse].
    Neither case should silently fail or change other sections.
    """
    headers=list(re.finditer(
        r"(?m)^[ \t]*\[surfdat\][ \t]*(?:[;#][^\r\n]*)?$", raw))
    if len(headers)!=1:
        found=[line.strip() for line in raw.splitlines()
               if line.lstrip().startswith("[") or "surfdata_esmf" in line]
        raise ValueError("Expected exactly one [surfdat] section; "
                         "observed headings/paths: "+repr(found[:25]))
    start=headers[0].end()
    next_section=re.search(
        r"(?m)^[ \t]*\[[A-Za-z0-9_-]+\][ \t]*(?:[;#][^\r\n]*)?$",
        raw[start:])
    end=start+next_section.start() if next_section else len(raw)
    source_section=raw[start:end]
    section=source_section
    for key, value in (
        ("dir", "lnd/clm2/surfdata_esmf/ctsm5.3.0"),
        ("surfdat_16pft", REFERENCE_SURF),
        ("mesh_surf", REFERENCE_MESH),
    ):
        pat=re.compile(r"(?m)^([ \t]*"+re.escape(key)+r"[ \t]*=[ \t]*)[^\r\n]*\r?$")
        section,count=pat.subn(lambda m:m.group(1)+value,section)
        if count!=1:
            keys=[line.strip() for line in source_section.splitlines()
                  if re.match(r"^[ \t]*(dir|surfdat_16pft|mesh_surf)\s*=",line)]
            raise ValueError("Expected one "+key+" in [surfdat], found "+
                             str(count)+"; observed entries: "+repr(keys))
    result=raw[:start]+section+raw[end:]
    # All content outside the pinned [surfdat] body is byte-for-byte
    # preserved, including [landuse] or other similarly named "dir" lines.
    if result[:start]!=raw[:start] or result[start+len(section):]!=raw[end:]:
        raise AssertionError("Configuration change escaped [surfdat]")
    return result


def read_stage15(path):
    if path.is_symlink() or not path.is_dir():
        raise FileNotFoundError("Stage15 verified source report missing")
    record=path/"stage15_ASM_surface_PFT_soil_source_register.json"
    if not record.is_file():raise FileNotFoundError(record)
    obj=json.loads(record.read_text(encoding="utf-8"))
    if (obj.get("Stage14_files_verified")!=6 or
        obj.get("science_approval") is not False or
        obj.get("model_submission_authorised") is not False or
        obj.get("decision")!="HOLD_SURFACE_AND_SITE_PFT_FRACTIONS_NOT_APPROVED"):
        raise ValueError("Stage15 expected 6/6 read-only candidate evidence, no science approvals")
    return sha(record),obj

def check_inputs(root,report_dir):
    ctsm=root/"CTSM"
    source=root/"inputdata"
    subset=ctsm/"tools/site_and_regional/subset_data"
    template=ctsm/"tools/site_and_regional/default_data_2000.cfg"
    surf=source/"lnd/clm2/surfdata_esmf/ctsm5.3.0"/REFERENCE_SURF
    mesh=source/"share/meshes"/REFERENCE_MESH
    for p in (subset,template,surf,mesh):
        if not p.is_file() or p.is_symlink():
            raise FileNotFoundError("Missing or symlink required source: "+str(p))
    if not source.is_dir() or not os.access(subset,os.X_OK):
        raise ValueError("Missing inputdata or subset_data not executable")
    stage15_sha,stage15=read_stage15(report_dir)
    cfg=config_text(template.read_text(encoding="utf-8"))
    digest=hashlib.sha256(cfg.encode()).hexdigest()
    info={
        "CTSM_root":str(ctsm),"inputdata_root":str(source),
        "subset_data_script":str(subset),"subset_data_sha256":sha(subset),
        "template":str(template),"template_sha256":sha(template),
        "config_modified_SHA256":digest,
        "stage15_report_root":str(report_dir),"stage15_report_SHA256":stage15_sha,
        "reference_gridded_surf":str(surf),"reference_mesh":str(mesh),
        "requested_site":SITE,"requested_lat":LAT,"requested_lon":LON,
        "ctsm_surf_year":2000,"dompft_requested":False,
        "PFT_soil_bare_science_approved":False,
        "AD400_or_CIME_submission_authorised":False,
        "intentionally_not_replacing_any_existing_files":True,
    }
    return info,cfg,subset,ctsm,source

def help_check(subset,ctsm):
    r=subprocess.run([sys.executable,"-B",str(subset),"point","--help"],
                     cwd=ctsm,stdin=subprocess.DEVNULL,
                     capture_output=True,text=True,timeout=90)
    if r.returncode:
        raise RuntimeError("CTSM subset_data import/help preflight failed:\n"+
                           r.stdout[-1800:]+"\n"+r.stderr[-2800:])
    for flag in ("--lat","--lon","--site","--surf-year",
                 "--create-surface","--create-user-mods",
                 "--inputdata-dir","--cfg-file","--outdir"):
        if flag not in r.stdout:
            raise ValueError("subset_data tool lost required option: "+flag)
    return True

def arr(ds,name):
    if name not in ds.variables:return None
    v=ds.variables[name]
    x=np.ma.asarray(v[:],dtype=float).filled(np.nan).ravel()
    return x if np.isfinite(x).all() else None

def summary_surface(path):
    with netCDF4.Dataset(str(path),"r") as ds:
        lat=arr(ds,"LATIXY");lon=arr(ds,"LONGXY")
        if lat is None or lon is None or lat.size!=1 or lon.size!=1:
            raise ValueError("Reference surface coordinates absent/non-singleton")
        lon_diff=abs((float(lon[0])-LON+180)%360-180)
        if abs(float(lat[0])-LAT)>0.05 or lon_diff>0.05:
            raise ValueError("Reference surface coordinates differ >0.05 degrees from site")
        result={
            "surface_path":str(path),"surface_SHA256":sha(path),
            "site_lat":LAT,"site_lon":LON,
            "surface_lat":float(lat[0]),"surface_lon":float(lon[0]),
            "CTSM_natPFT_not_tower_cover":True,
            "source_grid_PFT_science_approved":False,
        }
        nat=arr(ds,"PCT_NAT_PFT")
        if nat is None or nat.size not in (15,16):
            result["PFT_schema"]="HOLD_NONSTANDARD_INDEX_OR_NO_FINITE_PFT"
        else:
            result["PFT_schema"]="HOST_NATPFT_VECTOR_PRESENT"
            result["n_natpft"]=len(nat)
            result["natpft_total"]=float(sum(nat))
            result["clm_host_pft_fraction_pct"]={
                LABELS[i]:float(x) for i,x in enumerate(nat)}
            result["bare_natural_pct"]=float(nat[0])
            result["woody_natural_pct"]=float(np.sum(nat[1:9]))
            result["shrub_natural_pct"]=float(np.sum(nat[9:12]))
            result["c3_natural_pct"]=float(np.sum(nat[12:14]))
            result["c4_natural_pct"]=float(nat[14])
            if not np.isclose(sum(nat),100.,atol=0.1):
                result["PFT_schema"]="HOLD_HOST_PFT_FRACTIONS_NOT_SUM_100"
        land={k:arr(ds,k) for k in LAND}
        if all(v is not None for v in land.values()):
            result["landunit_pct"]={k:float(np.sum(land[k])) for k in LAND}
            result["landunit_sum_pct"]=float(
                sum(np.sum(v) for v in land.values()))
        else: result["landunit_pct"]="HOLD_SOME_LANDUNIT_FIELDS_MISSING"
        soil={}
        for name in ("PCT_SAND","PCT_CLAY","ORGANIC"):
            x=arr(ds,name)
            soil[name]={
                "layers":int(x.size) if x is not None else None,
                "min":float(np.min(x)) if x is not None else None,
                "max":float(np.max(x)) if x is not None else None,
                "values":[float(y) for y in x] if x is not None and x.size<=40 else None,
            }
        result["reference_gridded_soil"]=soil
        sand=arr(ds,"PCT_SAND");clay=arr(ds,"PCT_CLAY")
        result["soil_sand_clay_bounds_valid"]=bool(
            sand is not None and clay is not None and
            len(sand)==len(clay) and len(sand)>=10
            and np.all(sand>=0) and np.all(clay>=0) and
            np.all(sand+clay<=100.001))
        return result

def output_files(folder):
    output={}
    for p in sorted(folder.rglob("*")):
        rel=str(p.relative_to(folder))
        if p.is_symlink():
            raise ValueError("Output unexpectedly contains symlink "+rel)
        if p.is_file():
            output[rel]={"bytes":p.stat().st_size,"sha256":sha(p)}
    return output

def selftest():
    surf_54=("[surfdat]\n"
             "dir = lnd/clm2/surfdata_esmf/ctsm5.4.0\n"
             "surfdat_16pft = old.nc\nmesh_surf = oldmesh.nc\n")
    landuse=("[landuse]\n"
             "dir = lnd/clm2/surfdata_esmf/ctsm5.4.0\n"
             "landuse_16pft = keep_original_file.nc\n")
    source=("[main]\nclmforcingindir = /original/unchanged\n"
            +surf_54+"\n"+landuse)
    result=config_text(source)
    assert "dir = lnd/clm2/surfdata_esmf/ctsm5.3.0" in result
    assert REFERENCE_SURF in result and REFERENCE_MESH in result
    assert landuse in result
    assert "clmforcingindir = /original/unchanged" in result
    assert result.count("ctsm5.4.0")==1  # only [landuse] remains unchanged
    # Idempotence when the source already uses ctsm5.3.0, plus flexible
    # horizontal whitespace and unrelated 'dir' values.
    assert config_text(result)==result
    variant=surf_54.replace(
        "dir = lnd/clm2/surfdata_esmf/ctsm5.4.0",
        "  dir\t=  lnd/clm2/surfdata_esmf/ctsm5.3.0")
    assert "  dir\t=  lnd/clm2/surfdata_esmf/ctsm5.3.0" in config_text(variant)
    try:
        config_text("[surfdat]\nsurfdat_16pft = bad\nmesh_surf = bad\n")
    except ValueError as exc:
        assert "Expected one dir" in str(exc)
    else:
        raise AssertionError("Missing [surfdat] dir must fail")
    assert len(LABELS)==16 and LABELS[0]=="bare_ground"
    assert LAT<0 and LON>0
    print("STAGE16 SELF-TEST PASS: [surfdat]-scoped version/whitespace fix, landuse unchanged; no file writes")


def main():
    if sys.argv[1:]==["--self-test"]:
        selftest();return
    p=argparse.ArgumentParser(description=__doc__)
    modes=p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--build-reference",action="store_true")
    p.add_argument("--confirm")
    p.add_argument("--stage15",type=Path,default=STAGE15)
    p.add_argument("--clm-root",type=Path,default=ROOT)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    out=args.out.resolve()
    root=args.clm_root.resolve()
    if (args.out.is_symlink() or out.exists() or
        out.parent!=Path.home().resolve() or
        root==out or root in out.parents or
        args.out.name in ("", ".", "..")):
        raise ValueError("Output must be a fresh DIRECT CHILD of HOME, outside CLM_FATES")
    info,cfg,subset,ctsm,inputdata=check_inputs(root,args.stage15)
    help_check(subset,ctsm)
    print("STAGE16 SOURCE TOOL/INPUT PREFLIGHT PASS")
    print("SITE",SITE,"LAT",LAT,"LON",LON,"REFERENCE_SURF_YEAR",2000)
    print("CONFIG SHA256",info["config_modified_SHA256"])
    print("CTSM",ctsm,"INPUTDATA",inputdata)
    if args.check:
        print("STAGE16 CHECK PASS | no output directory or surface created")
        print("SCIENCE_APPROVAL FALSE | MODEL_SUBMISSION FALSE")
        return
    if args.confirm!=CONFIRM:
        raise ValueError("Explicit build confirmation missing: --confirm "+CONFIRM)
    out.mkdir(parents=False,exist_ok=False)
    local_cfg=out/(SITE+"_reference_2000_data.cfg")
    with local_cfg.open("x",encoding="utf-8") as h:h.write(cfg)
    command=[sys.executable,"-B",str(subset),"point",
             "--lat",str(LAT),"--lon",str(LON),"--lon-type","180",
             "--site",SITE,"--surf-year","2000","--create-surface",
             "--create-user-mods","--inputdata-dir",str(inputdata),
             "--cfg-file",str(local_cfg),"--outdir",str(out)]
    print("RUNNING ISOLATED CTSM REFERENCE SURFACE",command,flush=True)
    subprocess.run(command,cwd=ctsm,stdin=subprocess.DEVNULL,
                   check=True,timeout=1800)
    files=sorted(p for p in out.glob("surfdata*.nc") if p.is_file() and not p.is_symlink())
    if len(files)!=1:
        raise ValueError("Expected one reference surfdata*.nc: "+str(files))
    usermods=out/"user_mods"
    if not usermods.is_dir() or usermods.is_symlink():
        raise ValueError("Missing generated user_mods")
    reference=summary_surface(files[0])
    report={
        "stage":"OzFlux Stage16 AU-ASM REFERENCE ONLY CTSM 2000 subset_data point surface",
        "source_evidence":info,"requested_command":command,
        "reference_surface":reference,
        "purpose":"REFERENCE CTSM GRID SOURCE ONLY; NOT site-science approved",
        "site_PFT_fractions_approved":False,
        "Mulga_woody_C3_C4_bare_fractions_approved":False,
        "site_soil_ten_layer_profile_approved":False,
        "FATES_parameter_mapping_approved":False,
        "point_surface_scientific_approval":False,
        "CIME_case_or_AD400_submission_authorised":False,
        "created_new_separate_reference":True,
        "original_source_and_DATM_unchanged":True,
        "output_inventory_sha256":output_files(out),
    }
    (out/"stage16_AU_ASM_REFERENCE_SURFACE_NOT_MODEL_APPROVED.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    print("STAGE16 REFERENCE SURFACE CREATED",files[0])
    print("PFT_SCHEMA",reference["PFT_schema"])
    print("BARE",reference.get("bare_natural_pct"),
          "TREE",reference.get("woody_natural_pct"),
          "SHRUB",reference.get("shrub_natural_pct"),
          "C3",reference.get("c3_natural_pct"),"C4",reference.get("c4_natural_pct"))
    print("SOIL_SAND_CLAY_BOUNDS_VALID",reference["soil_sand_clay_bounds_valid"])
    print("REPORT_DIR",out)
    print("SCIENCE_APPROVAL FALSE; NO CIME/SLURM")

if __name__=="__main__":
    main()

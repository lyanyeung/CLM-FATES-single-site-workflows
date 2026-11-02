#!/usr/bin/env python3
"""Stage18 AU-ASM: read-only exact FATES parameter / host-PFT mapping inventory.

Do NOT assign Mulga PFT percentages or infer tree vs shrub from model names.
Do NOT write/edit NetCDF, JSON parameter files, CIME cases, soil or surface.
Only write new HOME report JSON + TSV. Existing AU-How case, if present,
is an example/reference, NOT proof of what future AU-ASM will run.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
import netCDF4
import numpy as np

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
STAGE16=Path.home()/"ozflux_stage16_reference_20261102T023647Z"
STAGE17=Path.home()/"ozflux_stage17_20261102T025047Z"
REF_SHA="18edace32d8e356c7d73269329dca7ed6338140e1ad1456f1a88691522c307fa"
HOST_NAMES=(
    "bare_ground", "needleleaf_evergreen_temperate_tree",
    "needleleaf_evergreen_boreal_tree", "needleleaf_deciduous_boreal_tree",
    "broadleaf_evergreen_tropical_tree", "broadleaf_evergreen_temperate_tree",
    "broadleaf_deciduous_tropical_tree", "broadleaf_deciduous_temperate_tree",
    "broadleaf_deciduous_boreal_tree", "broadleaf_evergreen_temperate_shrub",
    "broadleaf_deciduous_temperate_shrub", "broadleaf_deciduous_boreal_shrub",
    "c3_arctic_grass","c3_nonarctic_grass","c4_grass","nonstandard_16th",
)
SELECTED_INDEX=(0,4,5,7,10,13,14)
COLS=("source_parameter_file","format","sha256","map_found","map_variable_shape",
      "map_dimensions_or_metadata","nonzero_map_cells","pft_name_fields",
      "interpretation_status")

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(4*1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def safe_arr(ds,name):
    if name not in ds.variables:
        raise ValueError("Missing reference surface variable "+name)
    z=np.ma.asarray(ds.variables[name][:],dtype=float).filled(np.nan).ravel()
    if not np.isfinite(z).all():
        raise ValueError("Nonfinite reference values "+name)
    return z

def evidence(stage16,stage17):
    s=stage16/"stage16_AU_ASM_REFERENCE_SURFACE_NOT_MODEL_APPROVED.json"
    t=stage17/"stage17_AU_ASM_PFT_soil_science_gate.json"
    if not s.is_file() or not t.is_file() or s.is_symlink() or t.is_symlink():
        raise ValueError("Stage16 / Stage17 operator reports missing")
    d=json.loads(s.read_text(encoding="utf-8"))
    e=json.loads(t.read_text(encoding="utf-8"))
    file=Path(d["reference_surface"]["surface_path"])
    if (d.get("point_surface_scientific_approval") is not False or
        d.get("CIME_case_or_AD400_submission_authorised") is not False or
        d["reference_surface"].get("surface_SHA256")!=REF_SHA or
        e.get("input_surface_SHA256")!=REF_SHA or
        e.get("PFT_fraction_science_approved") is not False or
        e.get("point_surface_science_approved") is not False or
        file.is_symlink() or file.parent.resolve()!=stage16.resolve() or
        sha(file)!=REF_SHA):
        raise ValueError("Pinned Stage16 and Stage17 science provenance mismatch")
    with netCDF4.Dataset(str(file),"r") as nc:
        nat=safe_arr(nc,"PCT_NAT_PFT")
        soil_sand=safe_arr(nc,"PCT_SAND")
        soil_clay=safe_arr(nc,"PCT_CLAY")
        if (len(nat)!=15 or len(soil_sand)!=10 or len(soil_clay)!=10 or
            abs(nat.sum()-100)>0.001):
            raise ValueError("Unexpected reference surface schema")
        result={
            "site":"AU-ASM","reference_surface":str(file),
            "surface_sha256":REF_SHA,
            "host_natpft_15":[float(v) for v in nat],
            "selected_host_PFT":[
                {"host_index":i,"host_name":HOST_NAMES[i],
                 "pct_natural_land":float(nat[i]),
                 "science_approval":False} for i in SELECTED_INDEX
            ],
            "reference_sand10_pct":[float(v) for v in soil_sand],
            "reference_clay10_pct":[float(v) for v in soil_clay],
            "source_Stage16_report_sha256":sha(s),
            "source_Stage17_report_sha256":sha(t),
        }
    return result

def parameter_sources(root,extra):
    # Bounded candidate directories only: no recursive walking through cases
    # or the entire inputdata tree. Cases are explicitly known older examples.
    ctsm=root/"CTSM"
    parents=[
        ctsm/"src/fates/parameter_files",
        ctsm/"src/external_models/fates/parameter_files",
        ctsm/"src/fates",
        ctsm/"src/external_models/fates",
        root/"FATES/parameter_files",
    ]
    found=[]
    for parent in parents:
        if not parent.is_dir() or parent.is_symlink():
            continue
        for pat in ("fates_params*.json","fates_params*.nc","fates_params*.cdl"):
            found.extend(p for p in parent.glob(pat) if p.is_file() and not p.is_symlink())
    for p in extra:
        if not p.is_file() or p.is_symlink():
            raise FileNotFoundError("Explicit FATES parameter source absent/symlink "+str(p))
        if p.suffix.lower() not in (".json",".nc",".cdl"):
            raise ValueError("Unsupported explicit parameter format "+str(p))
        found.append(p)
    dedup=sorted(set(p.resolve() for p in found),key=str)
    if len(dedup)>40:
        raise ValueError("Too many FATES parameter sources: pass a specific --params path")
    return dedup,parents

def limited_numeric_matrix(value):
    if isinstance(value,dict):
        for key in ("data","value","values"):
            if key in value:
                return limited_numeric_matrix(value[key])
        return None
    try:
        a=np.asarray(value,dtype=np.float64)
    except (ValueError,TypeError):
        return None
    if a.ndim!=2 or a.size>10000 or not np.isfinite(a).all():
        return None
    return a

def nc_info(path):
    with netCDF4.Dataset(str(path),"r") as nc:
        names=list(nc.variables)
        maps=[x for x in names if "hlm_pft_map" in x.lower()]
        fields=[x for x in names if "pftname" in x.lower()
                or ("pft" in x.lower() and "name" in x.lower())]
        if not maps:
            return {"map_found":False,"map_variable_shape":None,
                    "map_dimensions_or_metadata":[],"nonzero_map_cells":[],
                    "pft_name_fields":fields,"available_PFT_like_names":names[:40]}
        key="fates_hlm_pft_map" if "fates_hlm_pft_map" in maps else maps[0]
        v=nc.variables[key]
        a=np.ma.asarray(v[:],dtype=float).filled(np.nan)
        cells=[]
        if a.ndim==2 and np.isfinite(a).all() and a.size<=10000:
            cells=[{"row":int(i),"column":int(j),"value":float(a[i,j])}
                   for i,j in zip(*np.where(a!=0))]
        return {
            "map_found":True,
            "map_variable_name":key,
            "map_variable_shape":list(v.shape),
            "map_dimensions_or_metadata":list(v.dimensions),
            "nonzero_map_cells":cells,
            "pft_name_fields":fields,
            "possible_map_orientation_NOT_CERTIFIED":True,
        }

def json_info(path):
    obj=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj,dict):
        return {"map_found":False,"format_warning":"JSON root not a dict"}
    keys=list(obj)
    maps=[k for k in keys if "hlm_pft_map" in k.lower()]
    labels=[k for k in keys if "pft" in k.lower() and "name" in k.lower()]
    if not maps:
        return {"map_found":False,"map_variable_shape":None,
                "map_dimensions_or_metadata":[],
                "nonzero_map_cells":[],
                "pft_name_fields":labels,
                "top_level_fields_example":keys[:40]}
    key="fates_hlm_pft_map" if "fates_hlm_pft_map" in maps else maps[0]
    v=obj[key];a=limited_numeric_matrix(v)
    cells=([{"row":int(i),"column":int(j),"value":float(a[i,j])}
            for i,j in zip(*np.where(a!=0))] if a is not None else [])
    return {
        "map_found":True,"map_variable_name":key,
        "map_variable_shape":list(a.shape) if a is not None else None,
        "map_dimensions_or_metadata":{
            k:str(v[k])[:350] for k in v if k in
            ("dimensions","dims","name","units","long_name","size")
        } if isinstance(v,dict) else None,
        "nonzero_map_cells":cells,
        "pft_name_fields":labels,
        "raw_map_entry_type":type(v).__name__,
        "numeric_matrix_not_decoded":a is None,
        "possible_map_orientation_NOT_CERTIFIED":True,
    }

def cdl_info(path):
    # .cdl is text only. Never execute ncgen, write .nc or make an
    # assumption about the matrix shape without the actual NetCDF.
    data=path.read_text(encoding="utf-8",errors="replace")
    lines=data.splitlines()
    matching=[{"line":i+1,"excerpt":line[:300]}
              for i,line in enumerate(lines) if
              "fates_hlm_pft_map" in line or "fates_pftname" in line]
    return {"map_found":any("fates_hlm_pft_map" in r["excerpt"] for r in matching),
            "map_variable_shape":None,"map_dimensions_or_metadata":matching[:12],
            "nonzero_map_cells":[],"pft_name_fields":[],
            "cdl_requires_compiled_nc_or_json_to_verify_mapping":True}

def inspect(path):
    if path.stat().st_size>100_000_000:
        raise ValueError("Parameter file too large for bounded safe inspection "+str(path))
    if path.suffix==".nc":
        detail=nc_info(path)
    elif path.suffix==".json":
        detail=json_info(path)
    else:detail=cdl_info(path)
    return {
        "source_parameter_file":str(path),"format":path.suffix,
        "bytes":path.stat().st_size,"sha256":sha(path),**detail,
        "interpretation_status":"PARAMETER_CANDIDATE_ONLY_NOT_PROVEN_ACTIVE_AU_ASM",
    }

def case_context(root,additional):
    paths=[
        root/"cases/AU-How_FATES_1PT",
        root/"cases/AU-How_FATES_1PT_AD5",
    ]+additional
    result=[]
    for path in paths:
        if path.is_symlink() or not path.is_dir():
            continue
        rec={"case_path":str(path),"role":"REFERENCE_CASE_NOT_AU_ASM"}
        for relative in ("user_nl_clm","CaseDocs/lnd_in",
                         "run/lnd_in","CaseDocs/drv_in"):
            file=path/relative
            if not file.is_file() or file.is_symlink():
                continue
            if file.stat().st_size>2_000_000:
                continue
            lines=file.read_text(encoding="utf-8",errors="replace").splitlines()
            selected=[{"line":i+1,"text":s.strip()[:500]}
                      for i,s in enumerate(lines) if
                      re.search(r"(?i)\b(fates_paramfile|fsurdat|use_fates_nocomp|spinup_state)\b",s)
                      and not s.lstrip().startswith(("!","#"))]
            rec[relative]={"sha256":sha(file),"matching_lines":selected[:25]}
        result.append(rec)
    return result

def write_tsv(path,rows):
    with path.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=COLS,delimiter="\t",extrasaction="ignore")
        w.writeheader()
        for row in rows:
            t={**row,"nonzero_map_cells":json.dumps(row.get("nonzero_map_cells",[])),
               "map_dimensions_or_metadata":json.dumps(row.get("map_dimensions_or_metadata",[])),
               "pft_name_fields":json.dumps(row.get("pft_name_fields",[]))}
            w.writerow(t)

def self_test():
    assert len(HOST_NAMES)==16 and SELECTED_INDEX==(0,4,5,7,10,13,14)
    assert limited_numeric_matrix([[1,0],[0,1]]).shape==(2,2)
    assert limited_numeric_matrix({"data":[[1,0],[0,1]]}).shape==(2,2)
    assert limited_numeric_matrix([1,2,3]) is None
    assert REF_SHA.startswith("18edace3")
    print("STAGE18 SELF-TEST PASS: JSON/NetCDF/CDL FATES map discovery and report-only guards")

def main():
    if sys.argv[1:]==["--self-test"]:
        self_test();return
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage16",type=Path,default=STAGE16)
    parser.add_argument("--stage17",type=Path,default=STAGE17)
    parser.add_argument("--clm-root",type=Path,default=ROOT)
    parser.add_argument("--params",type=Path,action="append",default=[],
                        help="Optional exact active FATES parameter JSON, CDL or NC")
    parser.add_argument("--case",type=Path,action="append",default=[],
                        help="Optional exact existing reference case directory")
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    out=args.out.resolve();root=args.clm_root.resolve()
    stage16=args.stage16.resolve();stage17=args.stage17.resolve()
    if (args.out.is_symlink() or out.exists() or
        out.parent!=Path.home().resolve() or
        any(out==p or p in out.parents for p in (root,stage16,stage17))):
        raise ValueError("Report must be a fresh direct child of HOME")
    surface=evidence(stage16,stage17)
    candidates,search_dirs=parameter_sources(root,args.params)
    reports=[]
    for p in candidates:
        try:
            rec=inspect(p)
        except Exception as exc:
            rec={"source_parameter_file":str(p),"format":p.suffix,
                 "sha256":sha(p),"map_found":False,"error":str(exc)[:450],
                 "interpretation_status":"SOURCE_FOUND_BUT_NOT_PARSED"}
        reports.append(rec)
        print("PARAM_CANDIDATE",rec["source_parameter_file"],"MAP",
              rec["map_found"],"SHA",rec["sha256"],
              "STATUS",rec["interpretation_status"])
    cases=case_context(root,args.case)
    out.mkdir(parents=False,exist_ok=False)
    payload={
        "stage":"OzFlux Stage18 FATES actual-source mapping / host surface science gate",
        "site":"AU-ASM","read_only":True,
        "reference_surface_evidence":surface,
        "FATES_parameter_search_directories":[str(p) for p in search_dirs],
        "parameter_source_candidates":reports,
        "existing_non_AU_ASM_reference_cases":cases,
        "actual_AU_ASM_active_FATES_params_verified":False,
        "model_fates_biogeography_or_competition_mode_verified":False,
        "source_Acacia_PFT_fractions_selected":False,
        "site_soil_ten_layer_selected":False,
        "site_specific_surface_generated":False,
        "model_submit_authorised":False,
        "next_decisions":[
          "Choose exact proposed AU-ASM fates_paramfile and verify HLM-PFT matrix orientation, PFT trait names and active model mode",
          "Choose bounded site PFT/bare model hypothesis without equating plot cover to natural-land fractions",
          "Resolve grid 89.8/6.6 sandy soil vs red Kandosol 74/15 site texture and establish justified ten-layer soil parameter source",
          "Construct separate versioned AU-ASM site-specific surface only after explicitly accepting scientific assumptions",
          "No new CIME case or Slurm job before full surface, PFT and forcing review",
        ],
    }
    (out/"stage18_ASM_FATES_host_surface_source_gate.json").write_text(
        json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    write_tsv(out/"stage18_FATES_parameter_candidates.tsv",reports)
    print("STAGE18 REFERENCE SURFACE SHA VERIFIED",REF_SHA)
    print("HOST PFT SELECTED INDEX/SOURCE FRACTIONS",[(x["host_index"],round(x["pct_natural_land"],4))
          for x in surface["selected_host_PFT"]])
    print("PARAMETER_CANDIDATES",len(reports),"MAPPING_FIELDS_FOUND",
          sum(bool(x.get("map_found")) for x in reports))
    print("REFERENCE_CASE_CONFIGS",len(cases))
    print("SCIENCE_APPROVAL FALSE; NO SURFACE/PARAM/CASE/SLURM MODIFICATIONS")
    print("REPORT_DIR",out)

if __name__=="__main__":
    main()

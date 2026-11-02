#!/usr/bin/env python3
"""OzFlux Stage19: exact local FATES JSON structural and mode forensics.

Report-only. Reads source-pinned CTSM/src/fates/parameter_files/default JSON,
Stage18 provenance and EXISTING AU-How CaseDocs/lnd_in. Recursively searches
for fates_hlm_pft_map, PFT identifiers/names, selected dimension-bearing
parameters and initialization fields without assuming mapping presence.
Does NOT alter original JSON, surfaces, model cases or Slurm.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import sys

EXPECTED_SHA="0819f8fddcb3566f6209f72bb1159a3161d03c8225a1464727b1d2b21aec6c04"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
PARAMS=ROOT/"CTSM/src/fates/parameter_files/fates_params_default.json"
STAGE18=Path.home()/"ozflux_stage18_20261102T030211Z"
REFERENCE_CASE=ROOT/"cases/AU-How_FATES_1PT/CaseDocs/lnd_in"
INTEREST={
    "fates_hlm_pft_map","fates_pftname","fates_pft_name",
    "fates_pft","fates_num_pft","fates_pftmap",
    "fates_initd","fates_seed_rain","fates_leaf_vcmax25top",
    "fates_allom_htmode","fates_allom_d2h1","fates_allom_d2h2",
}
MODE_NAMES={"fates_paramfile","use_fates","use_fates_nocomp",
            "spinup_state","use_fates_fixed_biogeog",
            "use_fates_fixed_biogeography","fates_nocomp"}
MAX_JSON_BYTES=60_000_000
MAX_DEPTH=15
MAX_OUTPUT_ITEMS=2000


def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(4*1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def locate(obj):
    """Find named JSON parameter keys at arbitrary dict depth.

    Traverse dicts and lists of dictionaries, but DO NOT recurse into
    huge floating arrays. Return exact dot/index paths.
    """
    found=[]
    visited=0
    def walk(x,path,depth):
        nonlocal visited
        visited+=1
        if depth>MAX_DEPTH or visited>100_000:
            raise ValueError("FATES JSON traversal limit exceeded; inspect source format")
        if isinstance(x,dict):
            for key,val in x.items():
                name=str(key)
                pos=path+"."+name if path else name
                if ("hlm_pft_map" in name.lower()
                    or name.lower() in INTEREST
                    or name.lower() in ("fates_pftnames","fates_pft_names")
                    or re.fullmatch(r"fates_.*(pftname|pft_name)",name.lower())):
                    found.append((pos,name,val))
                if isinstance(val,dict):
                    walk(val,pos,depth+1)
                elif isinstance(val,list) and len(val)<50 and any(isinstance(z,dict) for z in val):
                    for i,item in enumerate(val):
                        if isinstance(item,dict):walk(item,pos+f"[{i}]",depth+1)
        return
    walk(obj,"",0)
    if len(found)>MAX_OUTPUT_ITEMS:
        raise ValueError("Suspiciously many FATES matches")
    return found,visited


def value_summary(v):
    if isinstance(v,dict):
        result={"kind":"parameter_dict","keys":list(v)[:35]}
        for key in ("dtype","dims","dim","units","long_name","description","size"):
            if key in v:
                data=v[key]
                result[key]=data if isinstance(data,(str,int,float,bool,list)) and len(str(data))<=1300 else str(data)[:600]
        if "data" in v:
            result.update(data_summary(v["data"]))
        return result
    return data_summary(v)


def data_summary(x):
    if isinstance(x,list):
        outer=len(x)
        inner=len(x[0]) if x and isinstance(x[0],list) else None
        kinds=Counter(type(v).__name__ for v in x[:100])
        sample=x[:20] if inner is None else [row[:30] if isinstance(row,list) else row for row in x[:20]]
        s=json.dumps(sample,ensure_ascii=False)
        return {
            "kind":"list","outer_len":outer,"first_inner_len":inner,
            "top_level_types":dict(kinds),
            "sample_first_20_max_30_per_row":sample if len(s)<=9000 else s[:9000],
            "truncated":outer>20 or (inner is not None and inner>30),
        }
    if isinstance(x,dict):
        return {"kind":"dict","keys":list(x)[:35],"short_preview":str(x)[:1200]}
    return {"kind":type(x).__name__,"value":x if isinstance(x,(str,int,float,bool)) else str(x)[:400]}


def parameter_summaries(obj):
    if not isinstance(obj,dict):
        raise ValueError("FATES JSON top-level is not a dict")
    top=list(obj)
    names=[name for name in top if "pft" in name.lower()]
    dim_pft=[]
    pft_related=[]
    for name,v in obj.items():
        if not isinstance(v,dict):
            continue
        dims=v.get("dims",[])
        if isinstance(dims,list) and any("fates_pft" in str(item).lower() for item in dims):
            dim_pft.append(name)
        if any(x in name.lower() for x in ("pftname","pft_name","fates_pft_",
                                           "fates_hlm","fates_initd","fates_seed_rain")):
            pft_related.append(name)
    return {
        "top_level_total":len(top),
        "top_level_first_35":top[:35],
        "top_level_keys_containing_pft":names[:120],
        "pft_dimensioned_parameter_count":len(dim_pft),
        "pft_dimensioned_first_45":dim_pft[:45],
        "other_PFT_related_top_level_first_100":pft_related[:100],
        "has_root_hlm_map":"fates_hlm_pft_map" in obj,
        "has_root_pftname":"fates_pftname" in obj,
    }


def validate_stage18(root,file):
    stage18=root/"stage18_ASM_FATES_host_surface_source_gate.json"
    if not stage18.is_file() or stage18.is_symlink():
        raise FileNotFoundError("Stage18 source evidence missing")
    x=json.loads(stage18.read_text(encoding="utf-8"))
    if (x.get("model_submit_authorised") is not False
        or x.get("actual_AU_ASM_active_FATES_params_verified") is not False
        or x.get("reference_surface_evidence",{}).get("surface_sha256")
           !="18edace32d8e356c7d73269329dca7ed6338140e1ad1456f1a88691522c307fa"):
        raise ValueError("Stage18 science-provenance mismatch")
    sources=x.get("parameter_source_candidates",[])
    if not any(Path(p.get("source_parameter_file","")).resolve()==file.resolve()
               and p.get("sha256")==EXPECTED_SHA for p in sources):
        raise ValueError("Stage18 parameter inventory not equal to pinned source")
    return sha(stage18),x


def case_info(file,expected_path):
    result={"reference_case_name":"AU-How_FATES_1PT",
            "AU_ASM_case_exists_and_selected":False,
            "case_document_exists":file.is_file() and not file.is_symlink(),
            "case_ownership":"REFERENCE_ONLY_NOT_AU_ASM",
            "parameter_file_matches_default":None,
            "mode_relevant_lines":[]}
    if not result["case_document_exists"]:return result
    if file.stat().st_size>2_000_000:
        raise ValueError("Unexpected giant reference CaseDocs lnd_in")
    text=file.read_text(encoding="utf-8",errors="replace")
    result["sha256"]=sha(file)
    for number,line in enumerate(text.splitlines(),1):
        check=line.strip()
        if not check or check[0] in ("!","#"):
            continue
        m=re.match(r"(?i)^\s*([a-z_][a-z0-9_]*)\s*=\s*(.*?)\s*(?:!.*)?$",check)
        if not m:
            continue
        key=m.group(1).lower()
        if key in MODE_NAMES or "fates" in key.lower() and "map" in key.lower():
            val=m.group(2).strip()
            result["mode_relevant_lines"].append({"line":number,"parameter":key,"value":val[:550]})
            if key=="fates_paramfile":
                path=val.strip(" \t\"'")
                result["parameter_file_matches_default"]=path==str(expected_path)
    return result


def self_test():
    fixture={"parameters":[{"fates_hlm_pft_map":{"dims":["x","y"],"data":[[1,0],[0,1]]}}],
             "fates_pftname":{"dtype":"char","data":["one","two"]}}
    matches,visited=locate(fixture)
    assert {x[1] for x in matches}=={"fates_hlm_pft_map","fates_pftname"}
    matrix=value_summary(matches[0][2])
    assert matrix.get("dims")==["x","y"]
    assert matrix.get("outer_len")==2
    assert parameter_summaries(fixture)["has_root_pftname"]
    assert "fates_hlm_pft_map" not in parameter_summaries(fixture)["top_level_first_35"]
    print("STAGE19 SELF-TEST PASS: nested FATES JSON maps, missing top-level keys and MODE parser; REPORTS ONLY")


def main():
    if sys.argv[1:]==["--self-test"]:
        self_test();return
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fates-json",type=Path,default=PARAMS)
    parser.add_argument("--stage18",type=Path,default=STAGE18)
    parser.add_argument("--case-lnd-in",type=Path,default=REFERENCE_CASE)
    parser.add_argument("--out",type=Path,required=True)
    a=parser.parse_args()
    file=a.fates_json.resolve()
    out=a.out.resolve()
    if (a.out.is_symlink() or out.exists() or out.parent!=Path.home().resolve()
        or file==out or file in out.parents):
        raise ValueError("Output must be a fresh direct HOME child separate from input")
    if file.is_symlink() or not file.is_file() or file.stat().st_size>MAX_JSON_BYTES:
        raise ValueError("Missing/symlinked/oversized FATES JSON")
    digest=sha(file)
    if digest!=EXPECTED_SHA:
        raise ValueError("FATES parameter file SHA256 differs from Stage18 source")
    s18hash,_=validate_stage18(a.stage18,file)
    obj=json.loads(file.read_text(encoding="utf-8"))
    matches,visited=locate(obj)
    parameter_stats=parameter_summaries(obj)
    inspected=[
        {"key_path":path,"key":key,"value_summary":value_summary(v)}
        for path,key,v in matches
    ]
    hlm=[x for x in inspected if "hlm_pft_map" in x["key"].lower()]
    pftname=[x for x in inspected if "pftname" in x["key"].lower() or "pft_name" in x["key"].lower()]
    reference_case=case_info(a.case_lnd_in,file)
    report={
        "stage":"OzFlux AU-ASM Stage19 exact FATES default JSON structure / mode forensics",
        "parameter_file":str(file),"parameter_SHA256":digest,
        "stage18_report_SHA256":s18hash,
        "stage18_mode_science_approval":False,
        "source_reference_case":reference_case,
        "json_structure_statistics":parameter_stats,
        "recursively_searched_json_nodes":visited,
        "exact_fates_hlm_pft_map_occurrences":hlm,
        "exact_FATES_PFT_name_parameter_occurrences":pftname,
        "other_PFT_related_matches":[x for x in inspected if x not in hlm and x not in pftname],
        "all_relevant_key_paths":[x["key_path"] for x in inspected],
        "actual_default_JSON_contains_hlm_map":bool(hlm),
        "interpretation":
            "EXACT_MAP_IN_FILE_NEEDS_DIMENSION_ORIENTATION_AND_MODE_CHECK"
            if hlm else
            "NO_HLM_MAP_FOUND_AT_ANY_JSON_DEPTH; DO_NOT_INVENT_HOST_TO_FATES_MAPPING",
        "AU_ASM_competition_or_nocomp_mode_SELECTED":False,
        "AU_ASM_host_surface_PFT_site_science_approved":False,
        "AU_ASM_FATES_params_selected":False,
        "site_specific_surface_created":False,
        "model_submission_authorised":False,
        "next_step":"If map absent, locate exact source-code implementation or generation step; if present, validate dims, PFT name labels, and intended active mode. Do not assign Acacia fractions.",
    }
    out.mkdir(parents=False,exist_ok=False)
    (out/"stage19_AU_ASM_FATES_JSON_actual_schema.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("STAGE19 SOURCE SHA256 VERIFIED",digest)
    print("STAGE19 TOPLEVEL_KEYS",parameter_stats["top_level_total"],
          "RECURSIVE_VISITED",visited)
    print("STAGE19 HLM_MAP_MATCHES",len(hlm))
    for match in hlm:
        print("HLM_MAP_LOCATION",match["key_path"])
        print("HLM_MAP_SUMMARY",json.dumps(match["value_summary"],ensure_ascii=False)[:2200])
    print("STAGE19 PFT_NAME_MATCHES",len(pftname))
    for match in pftname[:8]:
        print("PFT_NAME_LOCATION",match["key_path"])
        print("PFT_NAME_SUMMARY",json.dumps(match["value_summary"],ensure_ascii=False)[:1400])
    print("STAGE19 PFT_DIM_PARAMS",parameter_stats["pft_dimensioned_parameter_count"])
    print("STAGE19 AU_HOW_CASE_PARAM_MATCH",reference_case["parameter_file_matches_default"])
    for k in reference_case["mode_relevant_lines"]:
        print("REFERENCE_CASE",k["parameter"],k["value"])
    print("STAGE19 SCIENCE HOLD | no mapped Mulga PFT or soil profile approved; no CIME/Slurm")
    print("REPORT_DIR",out)

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""OzFlux AU-ASM Stage24 read-only exact local FATES height-allometry check.

Only calculate FATES4 and FATES7 H(DBH) if both:
1) The original local installed FatesAllometryMod.F90 has the EXACT
   independently verified Stage23 SHA256, mode dispatch 5 vs 1, and the
   height calculation statements for d2h_martcano and d2h_obrien.
2) The exact original pinned FATES JSON has the Stage23 mode/parameter
   values and immutable SHA256. Numeric curves are structural/
   allometric illustrations, NOT model vegetation trajectories or
   validation against tower canopy height.

Reads Stage23 report and parameter/source files. Writes CSV + JSON ONLY
in fresh direct child of HOME; no surface/forcing/params/NetCDF/case/
Slurm model writes, no PFT area mapping and no AD400.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys

HOME=Path.home()
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES")
PARAM=ROOT/"CTSM/src/fates/parameter_files/fates_params_default.json"
SOURCE=ROOT/"CTSM/src/fates/biogeochem/FatesAllometryMod.F90"
STAGE23=HOME/"ozflux_stage23_20261102T114525Z"
PARAM_SHA="0819f8fddcb3566f6209f72bb1159a3161d03c8225a1464727b1d2b21aec6c04"
SOURCE_SHA="8ad6c9eaaa9f5c40036f8aa099f6435b80f2a8e7248a48b6ddb3a978db3c7f16"
STAGE21_SHA="2ce8e2e0eba38bf284b67ddb73ffc54f4392105c6a35de0eeb44e49ec1c7b85d"
HEIGHT_REF=4.3
DBHS=(0.5,1.0,2.0,2.5,3.0,4.0,5.0,6.0,8.0,10.0,15.0,20.0,30.0,50.0)
COLUMNS=("dbh_cm","FATES4_martcano_height_m","FATES7_obrien_height_m",
         "FATES7_plateau_at_diameter_3cm","comment")
PARAM_NAMES=("fates_allom_hmode","fates_allom_d2h1",
             "fates_allom_d2h2","fates_allom_d2h3",
             "fates_allom_dbh_maxheight")


def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as fd:
        for chunk in iter(lambda:fd.read(4*1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def verified_file(p,digest,label):
    if p.is_symlink() or not p.is_file() or sha(p)!=digest:
        raise ValueError(label+" SHA256 mismatch: "+str(p))


def load_receipt():
    p=STAGE23/"stage23_AU_ASM_actual_allometry_source_science_hold.json"
    if STAGE23.is_symlink() or p.is_symlink() or not p.is_file():
        raise FileNotFoundError("Stage23 operator report missing")
    r=json.loads(p.read_text(encoding="utf-8"))
    receipts=r.get("source_SHA256",{})
    entries=r.get("FATES_code_candidates",[])
    modes=r.get("actual_FATES_height_allometry_modes",{})
    if (receipts.get("Stage21_traits_TSV_SHA256")!=STAGE21_SHA or
        receipts.get("FATES_default_JSON_SHA256")!=PARAM_SHA or
        r.get("AD400_authorised") is not False or
        r.get("AU_ASM_mode_and_PFT_fractions_approved") is not False or
        r.get("no_predicted_height_without_exact_local_model_formula") is not True or
        modes.get("4",{}).get("hmode_value")!=5 or
        modes.get("7",{}).get("hmode_value")!=1 or
        not any(x.get("sha256")==SOURCE_SHA and Path(x.get("file","")).resolve()==SOURCE.resolve()
                for x in entries)):
        raise ValueError("Stage23 pinned provenance/hmode science gate mismatch")
    return sha(p)


def block(text,name):
    pat=re.compile(
        r"^\s*subroutine\s+"+re.escape(name)+
        r"\s*\([^\n]*\).*?^\s*end\s+subroutine\s+"+
        re.escape(name)+r"\b",re.IGNORECASE|re.MULTILINE|re.DOTALL)
    hits=pat.findall(text)
    if len(hits)!=1:
        raise ValueError("Expected one local function "+name+
                         ", found "+str(len(hits)))
    return hits[0]


def uncomments(text):
    return "\n".join(line.split("!")[0] for line in text.splitlines())


def normalize_statement(text):
    return re.sub(r"\s|&","",uncomments(text)).lower()


def has_dispatch(htext,mode,function):
    cases=list(re.finditer(r"(?im)^\s*case\s*\(\s*(\d+)\s*\)",htext))
    matching=[(i,x) for i,x in enumerate(cases) if int(x.group(1))==mode]
    if len(matching)!=1:
        return False
    i,entry=matching[0]
    end=cases[i+1].start() if i+1<len(cases) else len(htext)
    snippet=htext[entry.end():end]
    return bool(re.search(r"(?i)\bcall\s+"+re.escape(function)+r"\s*\(",snippet))


def verify_local_height_code(fortran):
    h=block(fortran,"h_allom")
    obrien=block(fortran,"d2h_obrien")
    mart=block(fortran,"d2h_martcano")
    if not (has_dispatch(h,1,"d2h_obrien") and
            has_dispatch(h,5,"d2h_martcano")):
        raise ValueError("Pinned local h_allom mode1 or mode5 dispatcher differs")
    first=normalize_statement(obrien)
    second=normalize_statement(mart)
    if "h=10.0_r8**(log10(min(d,dbh_maxh))*p1+p2)" not in first:
        raise ValueError("Local O'Brien formula differs from independently reviewed one")
    if "h=(p1*min(d,dbh_maxh)**p2)/(p3+min(d,dbh_maxh)**p2)" not in second:
        raise ValueError("Local Martinez-Cano formula differs from reviewed one")
    return {
        "source_SHA256":SOURCE_SHA,
        "h_allom_mode1_calls":"d2h_obrien",
        "h_allom_mode5_calls":"d2h_martcano",
        "obrien_verified_formula":"h = 10**(log10(min(d,dbh_maxh))*p1+p2)",
        "martcano_verified_formula":"h = (p1*min(d,dbh_maxh)**p2)/(p3+min(d,dbh_maxh)**p2)",
        "local_source_function_text_SHA256":{
            "h_allom":hashlib.sha256(h.encode("utf-8")).hexdigest(),
            "d2h_obrien":hashlib.sha256(obrien.encode("utf-8")).hexdigest(),
            "d2h_martcano":hashlib.sha256(mart.encode("utf-8")).hexdigest(),
        },
        "verified_actual_local_source":True,
    }


def extract_params():
    obj=json.loads(PARAM.read_text(encoding="utf-8"))
    if not isinstance(obj,dict) or set(obj)!={"attributes","dimensions","parameters"}:
        raise ValueError("Actual FATES JSON root schema unexpected")
    p=obj["parameters"]
    selected={}
    for name in PARAM_NAMES:
        e=p[name]
        if e.get("dims")!=["fates_pft"] or len(e["data"])!=14:
            raise ValueError("Actual "+name+" not an exact 14 PFT scalar")
        selected[name]={"4":e["data"][3],"7":e["data"][6]}
    expected={
        "fates_allom_hmode":(5,1),
        "fates_allom_d2h1":(104.3586841,0.64),
        "fates_allom_d2h2":(1.1146973,0.37),
        "fates_allom_d2h3":(160.6835089,-999.9),
        "fates_allom_dbh_maxheight":(1000.0,3.0),
    }
    for k,(a,b) in expected.items():
        if not (math.isclose(float(selected[k]["4"]),a,rel_tol=1e-9,abs_tol=1e-9)
                and math.isclose(float(selected[k]["7"]),b,rel_tol=1e-9,abs_tol=1e-9)):
            raise ValueError("Actual Stage23 reported "+k+" differs from pinned JSON")
    return selected


def numeric_h4(dbh,p):
    a=p["fates_allom_d2h1"]["4"]
    b=p["fates_allom_d2h2"]["4"]
    c=p["fates_allom_d2h3"]["4"]
    cap=p["fates_allom_dbh_maxheight"]["4"]
    d=min(dbh,cap)
    return a*d**b/(c+d**b)


def numeric_h7(dbh,p):
    a=p["fates_allom_d2h1"]["7"]
    b=p["fates_allom_d2h2"]["7"]
    cap=p["fates_allom_dbh_maxheight"]["7"]
    return 10**(math.log10(min(dbh,cap))*a+b)


def dbh_for_height_tree(height,p):
    a=p["fates_allom_d2h1"]["4"]
    b=p["fates_allom_d2h2"]["4"]
    c=p["fates_allom_d2h3"]["4"]
    cap=p["fates_allom_dbh_maxheight"]["4"]
    if height<=0 or height>numeric_h4(cap,p):
        return None
    return (height*c/(a-height))**(1/b)


def dbh_for_height_shrub(height,p):
    a=p["fates_allom_d2h1"]["7"]
    b=p["fates_allom_d2h2"]["7"]
    cap=p["fates_allom_dbh_maxheight"]["7"]
    if height<=0 or height>numeric_h7(cap,p):
        return None
    return (height/(10**b))**(1/a)


def selftest():
    source="""subroutine h_allom(d,ipft,h,dhdd)
       select case(allom_hmode)
       case (1)
           call d2h_obrien(d,p1,p2,dbh_maxh,h,dhdd)
       case (5)
           call d2h_martcano(d,p1,p2,p3,dbh_maxh,h,dhdd)
       end select
    end subroutine h_allom
    subroutine d2h_obrien(d,p1,p2,dbh_maxh,h,dhdd)
       ! h = WRONG
       h = 10.0_r8**(log10(min(d,dbh_maxh))*p1+p2)
    end subroutine d2h_obrien
    subroutine d2h_martcano(d,p1,p2,p3,dbh_maxh,h,dhdd)
       h = (p1*min(d,dbh_maxh)**p2)/(p3+min(d,dbh_maxh)**p2)
    end subroutine d2h_martcano
    """
    assert verify_local_height_code(source)["verified_actual_local_source"]
    assert not has_dispatch(block(source,"h_allom"),2,"d2h_obrien")
    p={k:{"4":a,"7":b} for k,(a,b) in {
        "fates_allom_d2h1":(104.3586841,0.64),
        "fates_allom_d2h2":(1.1146973,0.37),
        "fates_allom_d2h3":(160.6835089,-999.9),
        "fates_allom_dbh_maxheight":(1000.,3.),
    }.items()}
    assert math.isclose(numeric_h7(3,p),numeric_h7(50,p),rel_tol=1e-12)
    assert math.isclose(numeric_h4(dbh_for_height_tree(HEIGHT_REF,p),p),HEIGHT_REF,rel_tol=1e-12)
    assert math.isclose(numeric_h7(dbh_for_height_shrub(HEIGHT_REF,p),p),HEIGHT_REF,rel_tol=1e-12)
    print("STAGE24 SELF-TEST PASS: strict local Fortran formula recognition, mode dispatcher, 4.3m inverse, 3cm shrub height cap; NO MODEL WRITES")


def main():
    if sys.argv[1:]==["--self-test"]:
        selftest();return
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    out=args.out.resolve()
    if (args.out.is_symlink() or out.exists() or
        out.parent!=HOME.resolve() or
        out==ROOT.resolve() or ROOT.resolve() in out.parents or
        out==STAGE23.resolve() or STAGE23.resolve() in out.parents):
        raise ValueError("Report must be fresh direct child of HOME")
    verified_file(PARAM,PARAM_SHA,"Original FATES JSON")
    verified_file(SOURCE,SOURCE_SHA,"Local FATES allometry Fortran")
    stage23sha=load_receipt()
    formula=verify_local_height_code(SOURCE.read_text(encoding="utf-8",errors="replace"))
    params=extract_params()
    rows=[]
    for dbh in DBHS:
        rows.append({
            "dbh_cm":dbh,
            "FATES4_martcano_height_m":round(numeric_h4(dbh,params),8),
            "FATES7_obrien_height_m":round(numeric_h7(dbh,params),8),
            "FATES7_plateau_at_diameter_3cm":dbh>=3.0,
            "comment":"PFT-specific structural allometry, NOT tower growth prediction",
        })
    h4_at=dbh_for_height_tree(HEIGHT_REF,params)
    h7_at=dbh_for_height_shrub(HEIGHT_REF,params)
    summary={
      "stage":"OzFlux Stage24 exact installed Fortran H(DBH) structural sensitivity",
      "source_code_formula_verified":True,
      "source_hashes":{
        "Stage23_receipt":stage23sha,
        "local_FATES_allometry_Fortran":SOURCE_SHA,
        "original_FATES_param_JSON":PARAM_SHA,
      },
      "verified_local_Fortran_formula":formula,
      "active_per_PFT_height_parameters":params,
      "height_benchmark_m":HEIGHT_REF,
      "height_benchmark_source":"AU-ASM tower site canopy median ~4.3m; check source/spatial distribution independently before model calibration",
      "height_benchmark_is_not_a_DBH_measurement":True,
      "FATES4_MartinezCano_DBH_cm_for_4p3m":h4_at,
      "FATES7_OBrien_DBH_cm_for_4p3m":h7_at,
      "FATES7_plateau_height_m":numeric_h7(3.0,params),
      "FATES7_dbh_cap_cm":3.0,
      "FATES4_dbh_cap_cm":1000.,
      "site_woody_DBH_distribution_unknown":True,
      "calculated_heights_are_formula_outputs_NOT_CIME_results":True,
      "FATES4_crown_structure_science_approved":False,
      "FATES7_crown_structure_science_approved":False,
      "tree_shrub_PFT_fraction_approved":False,
      "soil_ten_layer_profile_approved":False,
      "forcing_science_approved":False,
      "new_surface_or_model_case_created":False,
      "Slurm_or_AD400_authorised":False,
      "FATES_allom_rmode_missing_in_Stage23_optional_inventory":"does not prove rooting physics absent; separate exact source/parameter discovery needed",
    }
    out.mkdir(parents=False,exist_ok=False)
    with (out/"stage24_AU_ASM_FATES4_vs_7_DBH_height_exact_local_Fortran.tsv").open(
        "x",encoding="utf-8",newline="") as fd:
        w=csv.DictWriter(fd,fieldnames=COLUMNS,delimiter="\t",extrasaction="raise")
        w.writeheader();w.writerows(rows)
    (out/"stage24_AU_ASM_DBH_height_science_gate.json").write_text(
        json.dumps(summary,indent=2,ensure_ascii=False,allow_nan=False),encoding="utf-8")
    print("STAGE24 LOCAL FORTRAN SHA VERIFIED",SOURCE_SHA)
    print("STAGE24 ORIGINAL FATES PARAMETER SHA VERIFIED",PARAM_SHA)
    print("STAGE24 MODE5 MARTINEZ-CANO AND MODE1 OBRIEN EXACT LOCAL FORMULAS VERIFIED")
    print("STAGE24 FATES7 HEIGHT PLATEAU",round(numeric_h7(3.0,params),6),"m at DBH >=3cm")
    print("STAGE24 4.3M BENCHMARK FATES4 DBH",round(h4_at,6),"cm; FATES7 DBH",round(h7_at,6),"cm")
    for r in rows:
        print("DBH",r["dbh_cm"],"FATES4_H",r["FATES4_martcano_height_m"],
              "FATES7_H",r["FATES7_obrien_height_m"])
    print("STAGE24 SCIENCE HOLD: heights structural only; no observed DBH, no Mulga PFT/soil/final forcing approval, no Slurm")
    print("REPORT_DIR",out)


if __name__=="__main__":
    main()

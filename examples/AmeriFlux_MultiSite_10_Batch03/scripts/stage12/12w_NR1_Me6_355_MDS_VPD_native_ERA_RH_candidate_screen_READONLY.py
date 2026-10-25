#!/usr/bin/env python3
"""Stage12w: 355 signed invalid original high-quality MDS VPDs,
same-original-timestamp companion-ERA RH source diagnostic ONLY.

Compute water RH from original paired TA_ERA/VPD_ERA and candidate VPD/QBOT
at UNCHANGED source QC0 tower TA_F and the signed Stage12g site PSRF. Apply
the physical and 5-degree safeguards used by Stage12d, original observed
QC0 immediate-neighbor comparisons, and signed Stage12g neighboring-shadow
jumps. Do not assume missing neighbors imply a passed continuity test.

SOURCE REPORT ONLY. No source, previous science shadow, forcing, DATM,
Slurm, or model edits. All 86+233 scientific holds remain unchanged.

--self-test: synthetic physical/missing-neighbor tests, no files
--check: signed source and candidate evidence, zero writes
--run: same checks + NEW separate SHA-sealed SCIENCE REPORT ONLY
"""
import argparse
import hashlib
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
sys.dont_write_bytecode = True

VERSION="batch03-stage12w-v2-20261025-355-MDS-bad-VPD-ERA-RH-guarded-diagnostics"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
V=ROOT/"reports/stage12v_MDS_VPD_temperature_and_QC_source_forensics_20261025T184859Z_bb353075"
V_RECEIPT="stage12v_MDS_source_quality_SHA_receipt.json"
V_355="355_original_QC1_MDS_VPD_vs_MDS_T_source_details.csv"
U=ROOT/"reports/stage12u_original_MDS_QC1_VPD_cross_temperature_source_20261025T183511Z_57431d0b"
G=ROOT/"science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f"
G_RECEIPT="stage12g_research_only_sha_receipt.json"
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
YEARS={("US-Me6",2015):115,("US-Me6",2017):114,("US-NR1",2022):126}
SUFFIX="STAGE12G_INCOMPLETE_NOLEAP"
HOLD_MARKER="INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP"

def safe(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Original SHA-protected evidence missing/symlinked: "+str(p))
    return p

def sha(p):
    digest=hashlib.sha256()
    with safe(p).open("rb") as f:
        for data in iter(lambda:f.read(1<<20),b""):
            digest.update(data)
    return digest.hexdigest()

def numeric(x):
    result=pd.to_numeric(x,errors="coerce").to_numpy(dtype=float)
    result[~np.isfinite(result)|(result<=-9990)]=np.nan
    return result

def es_water(t):
    arr=np.asarray(t,dtype=float)
    with np.errstate(over="ignore",invalid="ignore",divide="ignore"):
        return 6.112*np.exp(17.67*arr/(arr+243.5))

def es_ice(t):
    arr=np.asarray(t,dtype=float)
    with np.errstate(over="ignore",invalid="ignore",divide="ignore"):
        return 6.112*np.exp(22.46*arr/(arr+272.62))

def candidate(t,pa,era_t,era_v):
    """Same RH-to-site temperature transfer equations as original Stage12d."""
    t=np.asarray(t,dtype=float)
    pa=np.asarray(pa,dtype=float)
    era_t=np.asarray(era_t,dtype=float)
    era_v=np.asarray(era_v,dtype=float)
    es_e=es_water(era_t)
    ea_e=es_e-era_v
    with np.errstate(invalid="ignore",divide="ignore"):
        rh=100*ea_e/es_e
    es_t=es_water(t)
    vapor=es_t*rh/100
    new_v=es_t-vapor
    new_ea_pa=vapor*100.
    with np.errstate(invalid="ignore",divide="ignore"):
        q=0.622*new_ea_pa/(pa-0.378*new_ea_pa)
        rel_ice=rh*es_t/es_ice(t)
    good_t=np.isfinite(t)&(t>=-80)&(t<=65)
    good_pa=np.isfinite(pa)&(pa>=50000)&(pa<=110000)
    good_era=(np.isfinite(era_t)&np.isfinite(era_v)
              &np.isfinite(es_e)&np.isfinite(ea_e)
              &(rh>0)&(rh<=100)&(ea_e>0)&(era_v>=0))
    match_t=np.isfinite(era_t)&np.isfinite(t)&(abs(t-era_t)<=5)
    good_phase=(t>=0)|(np.isfinite(rel_ice)&(rel_ice<=100))
    good_closure=(np.isfinite(new_v)&np.isfinite(q)
                  &(new_v>=0)&(new_v<es_t)&(q>0)&(q<0.08))
    return {
       "ERA_RH_pct":rh, "ERA_source_water_vapor_hPa":ea_e,
       "trial_VPD_USE_hPa":new_v,"trial_QBOT_kgkg":q,
       "ice_relative_humidity_pct":rel_ice,
       "site_T_physical":good_t,"site_P_physical":good_pa,
       "ERA_RH_source_physical":good_era,
       "ERA_T_within_5C_of_tower_T":match_t,
       "source_ice_phase_allowed":good_phase,
       "candidate_VPD_QBOT_closure":good_closure
    }

def selftest():
    t=np.asarray([20., -8.])
    pa=np.asarray([90000.,85000.])
    et=np.asarray([20.,-8.])
    ev=np.asarray([2.,1.])
    c=candidate(t,pa,et,ev)
    assert np.allclose(c["trial_VPD_USE_hPa"],ev,rtol=0,atol=1e-12)
    assert c["ERA_RH_source_physical"].all()
    assert c["site_T_physical"].all() and c["site_P_physical"].all()
    assert c["candidate_VPD_QBOT_closure"].all()
    assert float(es_ice(-8))<float(es_water(-8))
    assert (not bool(candidate([20.],[90000.],[30.],[2.])[
        "ERA_T_within_5C_of_tower_T"][0]))
    assert not bool(candidate([20.],[np.nan],[20.],[2.])[
        "site_P_physical"][0])
    print("STAGE12W SELF-TEST PASS: original Stage12d ERA-RH physics, tower T/P, ice, basic candidate closure; NO WRITES",flush=True)

def verify():
    rv=json.loads(safe(V/V_RECEIPT).read_text())
    if (rv.get("version")!="batch03-stage12v-v1-20261025-MDS-VPD-MDS-T-QC-science-only"
        or rv.get("original_355_bad_QC1_MDS_source_values_preserved") is not True
        or rv.get("original_32_signed_VPD_neighbor_sides_preserved") is not True
        or rv.get("original_86_held_events_preserved") is not True
        or rv.get("original_233_prior_physics_holds_preserved") is not True
        or rv.get("original_source_T_P_VPD_clock_unchanged") is not True
        or rv.get("new_repairs")!=0
        or rv.get("Postv5_approved")!=0 or rv.get("DATM_ready")!=0
        or rv.get("spinup_authorized")!=0
        or rv.get("original_stage12u_SHA256")!=sha(
            U/"stage12u_original_VPD_MDS_source_SHA_receipt.json")):
        raise ValueError("Stage12v sealed source and 86/233 science HOLD gate changed")
    for name,digest in rv.get("output_SHA256",{}).items():
        if sha(V/name)!=digest:
            raise ValueError("Signed Stage12v output changed: "+name)
    rg=json.loads(safe(G/G_RECEIPT).read_text())
    safe(G/HOLD_MARKER)
    if (rg.get("Postv5_approved")!=0 or rg.get("DATM_ready")!=0
        or rg.get("spinup_authorized")!=0):
        raise ValueError("Stage12g sealed shadow approvals changed")
    for site in ("US-Me6","US-NR1"):
        name=f"{site}_{SUFFIX}.csv"
        expected=rg.get("output_sha256",{}).get(name)
        if not expected or sha(G/name)!=expected:
            raise ValueError("Signed Stage12g source-shadow CSV changed: "+name)
    manifest=json.loads(safe(S07/"exact_input_manifest.json").read_text())
    sites={a["site"]:a for a in manifest["sites"]}
    pins={str(Path(p).resolve()):digest
          for p,digest in manifest["input_sha256"].items()}
    for site in ("US-Me6","US-NR1"):
        for label in ("primary","era"):
            f=safe(sites[site][label])
            if sha(f)!=pins.get(str(f.resolve())):
                raise ValueError("Original native FLUXMET/ERA SHA changed: "+site+" "+label)
    return sites

def source_year(site,year,path):
    columns=["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC"]
    data=pd.read_csv(safe(path),usecols=columns,
                     dtype={"TIMESTAMP_START":str},low_memory=False)
    data=data.loc[data.TIMESTAMP_START.str.startswith(str(year))].copy()
    data.sort_values("TIMESTAMP_START",inplace=True)
    data.reset_index(drop=True,inplace=True)
    if len(data)!=17520 or data.TIMESTAMP_START.duplicated().any():
        raise ValueError("Full source native nonleap site-year 17520 mismatch")
    dt=pd.to_datetime(data.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
    start=pd.Timestamp(year,1,1)
    if (dt.iloc[0]!=start
        or dt.iloc[-1]!=start+pd.Timedelta(days=365)-pd.Timedelta(minutes=30)
        or not (dt.diff().iloc[1:]==pd.Timedelta(minutes=30)).all()):
        raise ValueError("Original native site-year chronological half-hours changed")
    for c in columns[1:]:data[c]=numeric(data[c])
    return data

def shadow_year(site,year):
    path=G/(site+"_"+SUFFIX+".csv")
    data=pd.read_csv(safe(path),usecols=["time","TA_USE","PSRF","VPD_USE"],
                     dtype={"time":str},low_memory=False)
    data["native_key"]=data.time.str.replace(
        r"[^0-9]","",regex=True).str.slice(0,12)
    data=data.loc[data.native_key.str.startswith(str(year))].copy()
    data.sort_values("native_key",inplace=True)
    data.reset_index(drop=True,inplace=True)
    if len(data)!=17520 or data.native_key.duplicated().any():
        raise ValueError("Stage12g exact original site-year native shadow mismatch")
    for col in ["TA_USE","PSRF","VPD_USE"]:data[col]=numeric(data[col])
    return data

def audit():
    site_sources=verify()
    signed=pd.read_csv(safe(V/V_355),dtype={"native_key":str},low_memory=False)
    if (len(signed)!=355 or signed.duplicated(["site","native_key"]).any()
        or not signed[["site","year"]].apply(tuple,axis=1).isin(YEARS).all()
        or not signed.original_VPD_F_QC.eq(1).all()
        or not signed.original_TA_F_QC.eq(0).all()):
        raise ValueError("Stage12v exact 355 source originals changed")
    rows=[]
    for (site,year),expected in YEARS.items():
        original=source_year(site,year,site_sources[site]["primary"])
        shadow=shadow_year(site,year)
        if not original.TIMESTAMP_START.equals(shadow.native_key):
            raise ValueError("Original source vs signed Stage12g time alignment changed")
        s=signed.loc[(signed.site==site)&(signed.year==year)].copy()
        if len(s)!=expected:raise ValueError("Signed source site-year total changed")
        index={key:i for i,key in enumerate(original.TIMESTAMP_START)}
        t=original.TA_F.to_numpy(dtype=float)
        v=original.VPD_F.to_numpy(dtype=float)
        tqc=original.TA_F_QC.to_numpy(dtype=float)
        vqc=original.VPD_F_QC.to_numpy(dtype=float)
        bnd=es_water(t)
        qc0_good=(np.isfinite(t)&np.isfinite(v)&(tqc==0)&(vqc==0)
                  &(v>=0)&(v<bnd))
        oldg=shadow.VPD_USE.to_numpy(dtype=float)
        st=shadow.TA_USE.to_numpy(dtype=float)
        p=shadow.PSRF.to_numpy(dtype=float)
        for rec in s.itertuples(index=False):
            key=rec.native_key
            if key not in index:raise ValueError("Signed native 355 source row missing: "+key)
            i=index[key]
            if (not np.isfinite(t[i]) or not np.isfinite(v[i])
                or tqc[i]!=0 or vqc[i]!=1 or v[i]<bnd[i]
                or abs(t[i]-float(rec.original_TA_F_C))>1e-7
                or abs(v[i]-float(rec.original_VPD_F_hPa))>1e-7):
                raise ValueError("Original QC1 VPD or tower QC0 T evidence changed at "+key)
            # Fail-closed if the existing research forcing T diverges from
            # original measured tower T: never propose overwriting that T.
            if not np.isfinite(st[i]) or abs(st[i]-t[i])>1e-7:
                raise ValueError("Original measured tower T not retained in Stage12g at "+key)
            et=float(rec.paired_native_TA_ERA_C)
            ev=float(rec.paired_native_VPD_ERA_hPa)
            c=candidate([t[i]],[p[i]],[et],[ev])
            at={field:(bool(arr[0]) if field in {
                  "site_T_physical","site_P_physical","ERA_RH_source_physical",
                  "ERA_T_within_5C_of_tower_T","source_ice_phase_allowed",
                  "candidate_VPD_QBOT_closure"} else float(arr[0]))
                for field,arr in c.items()}
            cv=at["trial_VPD_USE_hPa"]
            comparison=[]
            shadow_refs=[]
            qc0_refs=[]
            for j in (i-1,i+1):
                if j<0 or j>=len(original):continue
                if np.isfinite(oldg[j]):
                    shadow_refs.append((int((j-i)*30),float(oldg[j])))
                if qc0_good[j]:
                    qc0_refs.append((int((j-i)*30),float(v[j])))
            for label,reference in (("shadow",shadow_refs),
                                    ("original_QC0",qc0_refs)):
                for shift, vv in reference:
                    comparison.append({
                        "ref_type":label,"offset_min":shift,
                        "reference_value":vv,
                        "candidate_abs_jump_hPa":abs(cv-vv)
                        if np.isfinite(cv) else np.nan})
            sh_jumps=[x["candidate_abs_jump_hPa"] for x in comparison
                      if x["ref_type"]=="shadow"]
            qc_jumps=[x["candidate_abs_jump_hPa"] for x in comparison
                      if x["ref_type"]=="original_QC0"]
            base=(at["site_T_physical"] and at["site_P_physical"]
                  and at["ERA_RH_source_physical"]
                  and at["ERA_T_within_5C_of_tower_T"]
                  and at["source_ice_phase_allowed"]
                  and at["candidate_VPD_QBOT_closure"])
            if not at["site_T_physical"] or not at["site_P_physical"]:
                group="SITE_T_OR_PRESSURE_INVALID"
            elif not at["ERA_RH_source_physical"]:
                group="COMPANION_ERA_RH_SOURCE_INVALID"
            elif not at["ERA_T_within_5C_of_tower_T"]:
                group="COMPANION_ERA_T_MISMATCH_GT5C"
            elif not at["source_ice_phase_allowed"]:
                group="WATER_RH_IMPLIES_ICE_SUPERSATURATION"
            elif not at["candidate_VPD_QBOT_closure"]:
                group="INVALID_CANDIDATE_VPD_QBOT_PHYSICS"
            elif any(j>4 for j in sh_jumps):
                group="GT4HPA_JUMP_TO_EXISTING_STAGE12G_NEIGHBOR"
            elif any(j>4 for j in qc_jumps):
                group="GT4HPA_JUMP_TO_ORIGINAL_QC0_NEIGHBOR"
            elif not sh_jumps and not qc_jumps:
                group="NO_FINITE_IMMEDIATE_REFERENCE_CONTINUITY_UNTESTED"
            else:
                group="DIAGNOSTIC_PHYSICS_AND_AVAILABLE_EDGE_TEST_PASS_NOT_APPROVED"
            rows.append({
                "site":site,"year":year,"native_key":key,
                "original_TA_F_QC":int(tqc[i]),"original_VPD_F_QC":int(vqc[i]),
                "source_VPD_F_MDS_QC":rec.original_VPD_F_MDS_QC,
                "original_unchanged_QC0_tower_T_C":t[i],
                "original_impossible_MDS_VPD_hPa":v[i],
                "original_source_VPD_above_saturation_hPa":v[i]-bnd[i],
                "paired_original_companion_TA_ERA_C":et,
                "paired_original_companion_VPD_ERA_hPa":ev,
                "retained_Stage12g_PSRF_Pa":p[i],
                "retained_Stage12g_TA_USE_C":st[i],
                "tower_minus_companion_ERA_T_C":t[i]-et,
                **at,
                "Stage12g_same_timestamp_existing_VPD_USE_hPa":oldg[i],
                "Stage12g_same_timestamp_finite":bool(np.isfinite(oldg[i])),
                "immediate_finite_Stage12g_neighbor_count":len(sh_jumps),
                "max_abs_candidate_jump_to_Stage12g_neighbor_hPa":(
                    max(sh_jumps) if sh_jumps else np.nan),
                "immediate_physically_valid_original_QC0_VPD_neighbor_count":len(qc_jumps),
                "max_abs_candidate_jump_to_original_QC0_neighbor_hPa":(
                    max(qc_jumps) if qc_jumps else np.nan),
                "screen_group_NOT_MODEL_APPROVAL":group,
                "input_source_repaired":False,
                "original_86_plus_233_holds_preserved":True,
                "Postv5_approved":False,
                "DATM_ready":False,"spinup_authorized":False
            })
    out=pd.DataFrame(rows)
    if (len(out)!=355 or out.duplicated(["site","native_key"]).any()
        or not (out.groupby(["site","year"]).size().to_dict()==YEARS)
        or not out.original_source_VPD_above_saturation_hPa.ge(-1e-7).all()
        or out.input_source_repaired.any()):
        raise ValueError("355 exact signed QC1 MDS source physics and output guard changed")
    summary=out.groupby(["site","year","screen_group_NOT_MODEL_APPROVAL"],
                        dropna=False,as_index=False).agg(
         original_source_QC1_MDS_bad_rows=("native_key","size"),
         Stage12g_already_finite_at_same_time=("Stage12g_same_timestamp_finite","sum"),
         median_abs_site_minus_ERA_T_C=("tower_minus_companion_ERA_T_C",
           lambda x:float(x.abs().median())),
         median_candidate_VPD_hPa=("trial_VPD_USE_hPa","median"),
         with_Stage12g_immediate_finite_neighbor=(
              "immediate_finite_Stage12g_neighbor_count",
              lambda x:int(x.gt(0).sum())),
         with_original_QC0_immediate_neighbor=(
              "immediate_physically_valid_original_QC0_VPD_neighbor_count",
              lambda x:int(x.gt(0).sum())))
    held=out.loc[out.screen_group_NOT_MODEL_APPROVAL.ne(
            "DIAGNOSTIC_PHYSICS_AND_AVAILABLE_EDGE_TEST_PASS_NOT_APPROVED")].copy()
    return out,summary,held

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    for opt in ("self-test","check","run"):
        g.add_argument("--"+opt,action="store_true")
    args=p.parse_args()
    print("STAGE12W — 355 SOURCE MDS BAD VPD: ERA RH WITH TOWER QC0 T + ORIGINAL 4hPa EDGES | "+VERSION,flush=True)
    selftest()
    if args.self_test:return
    detail,summary,held=audit()
    print("\n========== ORIGINAL 355 MDS BAD VPD SOURCE: ERA-RH PHYSICS / CONTINUITY TRIAGE ==========",flush=True)
    print(summary.to_string(index=False),flush=True)
    print("\n========== SOURCE-ONLY PHYSICS AND EDGE SCREEN BY SITE-YEAR ==========",flush=True)
    print(detail.groupby(["site","year"],as_index=False).agg(
      source_bad_MDS_VPD=("native_key","size"),
      ERA_temperature_within_5C=("ERA_T_within_5C_of_tower_T","sum"),
      paired_ERA_RH_physical=("ERA_RH_source_physical","sum"),
      ice_phase_allowed=("source_ice_phase_allowed","sum"),
      physics_closed_trial=("candidate_VPD_QBOT_closure","sum"),
      retained_Stage12g_finite=("Stage12g_same_timestamp_finite","sum"),
      unapproved_and_unresolved=("screen_group_NOT_MODEL_APPROVAL",
           lambda x:int(x.ne("DIAGNOSTIC_PHYSICS_AND_AVAILABLE_EDGE_TEST_PASS_NOT_APPROVED").sum()))
    ).to_string(index=False),flush=True)
    print("\nSTAGE12W SUMMARY: original_355_QC1_MDS_source_rows=TRUE "
          "unchanged_QC0_tower_T_and_native_P=TRUE original_86+233_holds=TRUE "
          "research_candidate_only=TRUE new_repairs=0 Postv5_approved=0 DATM_ready=0 spinup=0",flush=True)
    if args.check:
        print("STAGE12W CHECK ONLY: NO OUTPUT, SOURCE, FORCING OR MODEL WRITES.",flush=True)
        return
    folder=ROOT/"reports"/(
        "stage12w_355_original_MDS_VPD_companion_ERA_RH_physics_triage_"
        +datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        +"_"+uuid4().hex[:8])
    folder.mkdir(exist_ok=False,parents=True)
    results={
       "355_original_QC1_MDS_VPD_ERA_RH_cautionary_candidate_evidence.csv":detail,
       "355_original_MDS_VPD_candidate_screen_summary.csv":summary,
       "held_or_unevaluated_ERA_RH_research_candidate_rows.csv":held,
    }
    for name,data in results.items():data.to_csv(folder/name,index=False)
    (folder/"SCIENTIFIC_HOLD.md").write_text(
       "This Stage12w research triage is not a prospective model input or "
       "an approval to replace any original MDS source value. The exact "
       "native original ERA source is paired to original tower QC0 T and "
       "Stage12g native PSRF; 5C, water RH, below-zero ice RH, QBOT "
       "physics and 4hPa available-neighbor comparisons are preserved. "
       "Passing tests against available neighbors DOES NOT license "
       "unobserved or multi-hour context jumps, original 86/233 HOLD "
       "release, or future Post-v5, DATM, Slurm or spinup.\n")
    outputs={name:sha(folder/name) for name in [*results,"SCIENTIFIC_HOLD.md"]}
    receipt={
      "version":VERSION,
      "verified_stage12v_source_receipt_sha256":sha(V/V_RECEIPT),
      "verified_stage12g_source_receipt_sha256":sha(G/G_RECEIPT),
      "source_355_original_invalid_MDS_QC1_preserved":True,
      "tower_QC0_T_and_site_P_and_native_clock_unchanged":True,
      "original_86_plus_233_science_holds_unchanged":True,
      "new_source_or_forcing_repairs":0,
      "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
      "output_SHA256":outputs}
    (folder/"stage12w_355_MDS_ERA_RH_science_report_SHA_receipt.json").write_text(
        json.dumps(receipt,indent=2)+"\n")
    print("STAGE12W SCIENCE-ONLY SOURCE REVIEW REPORT DIR:",folder,flush=True)
    print("ZERO SOURCE, FORCING, PREVIOUS SHADOW, CIME, SLURM OR MODEL WRITES.",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as error:
        print("STAGE12W STOP:",error,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

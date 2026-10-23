#!/usr/bin/env python3
"""Stage20: read-only freezing humidity and evidence review for all Stage19 targets.

Compare ERA5 water-RH transfer against the physically different alternative
of transferring ERA5 dewpoint-derived actual vapour pressure. For subzero
temperatures compare water and ice saturation REFERENCES using unchanged
actual vapour pressure. Ice saturation does not generate a new water-vapour
estimate. No RH/VPD clipping. An ice RH >100% may imply ice supersaturation.

ERA5 2m dewpoint implies actual e using saturation-over-water coefficients.
Hourly ERA data are interpolated to native half hours; report interpolation
discrepancies. 14 original Stage11 HOLDS remain. No DATM/forcing/CIME/Slurm.
--check writes nothing; --write-report writes new HOME-only reports.
References: ECMWF ERA5 data documentation, NPL dew point and RH guidance.
"""
import argparse
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

INROOT=(Path.home()/
    "AmeriFlux_Batch02_stage19_full_dewpoint_audit_20261023T015650Z_8505582f")
CSV="all_4884_ERA5_RH_VPD_QBOT_sensitivity.csv"
EXPECTED={"US-EML":1327,"US-GLE":295,"US-Ho1":917,"US-ICh":169,"US-ICt":2176}
SHA17="84f680fb67030d374bb8a02abd4fce5a4a2c5d4abe7c59a30acf7bb5948488d4"

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def esw(t):
    t=np.asarray(t,dtype=float)
    return 6.112*np.exp(17.67*t/(t+243.5)) # hPa over water

def esi(t):
    t=np.asarray(t,dtype=float)
    return 6.112*np.exp(22.46*t/(272.62+t)) # hPa over ice (NPL)

def qspec(e,p):
    epa=100*np.asarray(e,dtype=float)
    ppa=1000*np.asarray(p,dtype=float)
    return .622*epa/(ppa-.378*epa)

def read_source(root,rehash):
    root=root.expanduser().resolve(strict=True)
    if not (root/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Unapproved Stage19 marker missing")
    m=json.loads((root/"manifest.json").read_text())
    for k,v in dict(schema="STAGE19_ALL_4884_ERA5_DIAGNOSTIC_v1",
                    stage17_plan_sha256=SHA17,
                    n_target_rows=4884,number_site_years=42,
                    n_stage11_holds=14,n_numeric_invalid=0,
                    scientifically_approved_rows=0,
                    scientific_status="NUMERICAL_SENSITIVITY_ONLY_ALL_ROWS_HOLD").items():
        if m.get(k)!=v:raise ValueError("Unexpected Stage19 contract: "+k)
    if rehash:
        for field,expected in [("original_source_sha256",5),
                               ("cds_receipt_sha256",39),
                               ("verified_netcdf_sha256",39)]:
            hashes=m[field]
            if len(hashes)!=expected:raise ValueError("Hash scope differs: "+field)
            for p,d in hashes.items():
                if digest(p)!=d:raise ValueError("Original/ERA file changed: "+p)
    file=root/CSV
    a=pd.read_csv(file,parse_dates=["local"])
    if len(a)!=4884 or a.duplicated(["site","local"]).any() or \
       a.groupby("site").size().to_dict()!=EXPECTED or \
       a.groupby(["site","year"]).ngroups!=42:
        raise ValueError("Stage19 CSV coverage or identity differs")
    if int(a.original_Stage11_HOLD_preserved.sum())!=14 or \
       int((~a.sensitivity_numeric_valid).sum())!=0 or \
       not a.scientific_decision.str.startswith("HOLD_").all():
        raise ValueError("Stage19 science/numeric HOLD contract differs")
    if not (a.local.dt.year.to_numpy()==a.year.to_numpy()).all() or \
       not a.raw_tower_T_equals_Stage11_retained_T.all():
        raise ValueError("Tower timestamp or retained temperature differs")
    if not a.loc[a.site.eq("US-Ho1"),"UTC_offset_evidence"].str.startswith(
        "PROVISIONAL_").all():
        raise ValueError("US-Ho1 timezone must still be provisional")
    return a,m,file

def compute(a):
    a=a.copy()
    tt=a.retained_TA_C.to_numpy(float)
    te=a.ERA5_T2M_C.to_numpy(float)
    td=a.ERA5_Td2M_C.to_numpy(float)
    pa=a.retained_PA_kPa.to_numpy(float)
    rh=a.ERA5_RH_water_pct.to_numpy(float)
    sw=esw(tt)
    se=esw(te)
    si=esi(tt)
    ice_era=esi(te)
    # RH-transfer: exactly reproduce Stage19 unapproved sensitivity.
    e_rh=sw*rh/100
    q_rh=qspec(e_rh,pa)
    v_rh=sw-e_rh
    if not np.allclose(q_rh,a.sensitivity_QBOT_kgkg.to_numpy(float),
                       atol=1e-10,rtol=1e-8) or \
       not np.allclose(v_rh,a.sensitivity_VPD_hPa.to_numpy(float),
                       atol=1e-8,rtol=1e-8):
        raise ValueError("Stage19 RH-transfer reproduction failed")
    # Td-transfer: keep ERA5 dewpoint-derived actual vapour pressure.
    # This is NOT necessarily more representative at tower altitude.
    e_td=esw(td)
    q_td=qspec(e_td,pa)
    v_td=sw-e_td
    tower_cold=tt<0
    era_cold=te<0
    tower_ice_domain=tower_cold&(tt>=-65)
    era_ice_domain=era_cold&(te>=-65)
    ice_rh_era=np.where(era_ice_domain,100*e_td/ice_era,np.nan)
    ice_vpd_rh=np.where(tower_ice_domain,si-e_rh,np.nan)
    ice_vpd_td=np.where(tower_ice_domain,si-e_td,np.nan)
    a["ERA5_water_RH_recomputed_from_interp_T_Td_pct"]=100*e_td/se
    a["ERA5_RH_interpolation_gap_pp"]=rh-100*e_td/se
    a["ERA5_ice_RH_pct_subzero"]=ice_rh_era
    a["ERA5_ice_RH_above100_subzero"]=np.isfinite(ice_rh_era)&(ice_rh_era>100)
    a["ERA_minus_tower_T_C"]=te-tt
    a["tower_T_subzero"]=tower_cold
    a["ERA_T_subzero"]=era_cold
    a["ice_formula_outside_minus65C_domain"]=(tower_cold&~tower_ice_domain)|(
        era_cold&~era_ice_domain)
    a["RH_transfer_vapour_pressure_hPa"]=e_rh
    a["Td_transfer_vapour_pressure_hPa"]=e_td
    a["Td_transfer_water_VPD_hPa"]=v_td
    a["Td_transfer_QBOT_kgkg"]=q_td
    a["RH_transfer_ice_VPD_subzero_hPa"]=ice_vpd_rh
    a["Td_transfer_ice_VPD_subzero_hPa"]=ice_vpd_td
    a["Td_minus_RH_transfer_water_VPD_hPa"]=v_td-v_rh
    a["Td_minus_RH_transfer_QBOT_kgkg"]=q_td-q_rh
    a["Td_transfer_negative_water_VPD"]=v_td<-.005
    a["RH_transfer_negative_ice_VPD_subzero"]=np.isfinite(ice_vpd_rh)&(
        ice_vpd_rh<-.005)
    a["Td_transfer_negative_ice_VPD_subzero"]=np.isfinite(ice_vpd_td)&(
        ice_vpd_td<-.005)
    a["Td_transfer_numeric_bad"]=(~np.isfinite(v_td))|(~np.isfinite(q_td))|(
        q_td<=0)|(q_td>=.08)|(pa<=49)|(pa>=111)
    a["nearby_QC0_24h_any"]=a.nearby_QC0_T_and_VPD_24h_n>0
    a["scientific_approval"]=False
    a["stage20_decision"]="HOLD_MORE_EVIDENCE_REQUIRED"
    a["stage20_priority"]=np.select(
        [a.original_Stage11_HOLD_preserved,
         a.Td_transfer_numeric_bad|a.Td_transfer_negative_water_VPD|
         a.ice_formula_outside_minus65C_domain,
         ~a.nearby_QC0_24h_any],
        ["P0_ORIGINAL_HOLD","P1_TRANSFER_OR_FORMULA_CAUTION",
         "P2_NO_NEARBY_QC0"],
        default="P3_NEARBY_QC0_NOT_INDEPENDENT_VALIDATION")
    return a

def summarize(a):
    groups=[]
    for site,g in a.groupby("site",sort=True):
        groups.append(dict(site=site,n_targets=len(g),
            n_original_holds=int(g.original_Stage11_HOLD_preserved.sum()),
            n_nearby_QC0_24h=int(g.nearby_QC0_24h_any.sum()),
            n_tower_subzero=int(g.tower_T_subzero.sum()),
            n_ERA_subzero=int(g.ERA_T_subzero.sum()),
            n_ERA_ice_RH_above100=int(g.ERA5_ice_RH_above100_subzero.sum()),
            n_Td_transfer_negative_water_VPD=int(
                g.Td_transfer_negative_water_VPD.sum()),
            n_Td_transfer_numeric_bad=int(g.Td_transfer_numeric_bad.sum()),
            n_RH_transfer_negative_ice_VPD=int(
                g.RH_transfer_negative_ice_VPD_subzero.sum()),
            n_Td_transfer_negative_ice_VPD=int(
                g.Td_transfer_negative_ice_VPD_subzero.sum()),
            median_abs_T_ERA_vs_tower_C=float(
                g.ERA_minus_tower_T_C.abs().median()),
            median_abs_Td_vs_RH_VPD_hPa=float(
                g.Td_minus_RH_transfer_water_VPD_hPa.abs().median()),
            median_abs_Td_vs_RH_QBOT_kgkg=float(
                g.Td_minus_RH_transfer_QBOT_kgkg.abs().median()),
            median_abs_RH_interpolation_gap_pp=float(
                g.ERA5_RH_interpolation_gap_pp.abs().median()),
            n_scientifically_approved=0,science_status="ALL_HOLD"))
    return pd.DataFrame(groups)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    choice=parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--check",action="store_true")
    choice.add_argument("--write-report",action="store_true")
    parser.add_argument("--stage19-root",type=Path,default=INROOT)
    parser.add_argument("--output-root",type=Path)
    parser.add_argument("--skip-lineage-rehash",action="store_true",
                        help="Only for rapid checks; skips original/ERA file SHA256 rehash")
    args=parser.parse_args()
    a,m,inputfile=read_source(args.stage19_root,not args.skip_lineage_rehash)
    out=compute(a)
    summary=summarize(out)
    holds=out.loc[out.original_Stage11_HOLD_preserved].copy()
    if len(out)!=4884 or len(holds)!=14 or out.scientific_approval.any() or \
       not out.stage20_decision.str.startswith("HOLD_").all():
        raise ValueError("Stage20 HOLD invariants failed")
    print("========== STAGE20 FREEZING / HUMIDITY TRANSFER / QC ==========")
    print("Stage19 targets verified:",len(out),"/4884; ORIGINAL HOLD:",len(holds),"/14")
    print("TOWER below 0C:",int(out.tower_T_subzero.sum()),
          "ERA5 below 0C:",int(out.ERA_T_subzero.sum()))
    print("ERA5 RH_ice >100% where subzero:",int(
        out.ERA5_ice_RH_above100_subzero.sum()))
    print("Td-transfer water VPD <0:",int(out.Td_transfer_negative_water_VPD.sum()))
    print("Td-transfer numerical problems:",int(out.Td_transfer_numeric_bad.sum()))
    print("Nearby QC0 within 24h:",int(out.nearby_QC0_24h_any.sum()),"/4884")
    print("US-Ho1 -5 timezone PROVISIONAL; ICh/ICt same ERA grid")
    print("SCIENTIFIC APPROVAL: 0; all 4884 HOLD")
    print(summary[["site","n_targets","n_original_holds","n_nearby_QC0_24h",
                   "n_tower_subzero","n_ERA_subzero",
                   "n_Td_transfer_negative_water_VPD",
                   "median_abs_Td_vs_RH_VPD_hPa"]].to_string(index=False))
    print("========== ORIGINAL 14 HOLD TRANSFER SENSITIVITY ==========")
    print(holds[["site","local","ERA5_RH_water_pct",
                 "sensitivity_VPD_hPa","Td_transfer_water_VPD_hPa",
                 "Td_minus_RH_transfer_water_VPD_hPa",
                 "nearby_QC0_T_and_VPD_24h_n"]].to_string(index=False))
    if args.check:
        print("STAGE20 CHECK ONLY: no files, forcing or model changes")
        return 0
    path=(args.output_root.expanduser().resolve() if args.output_root else
          Path.home()/("AmeriFlux_Batch02_stage20_physical_evidence_review_"+
          datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+
          uuid4().hex[:8]))
    root=args.stage19_root.expanduser().resolve()
    protected=[root,Path.home()/"AmeriFlux_Batch02_ERA5_missing_grid_years",
               Path.home()/"AmeriFlux_Batch02_ERA5_five_one_year_controls"]
    if path.exists() or path.is_symlink() or \
       any(path==p or path in p.parents or p in path.parents for p in protected):
        raise ValueError("Existing/unsafe report path")
    path.mkdir(parents=True,exist_ok=False)
    (path/"DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "Stage20 water/ice and transfer sensitivity only. All 4884 HOLD.\n")
    out.to_csv(path/"all_4884_phase_transfer_QC_sensitivity.csv",index=False)
    summary.to_csv(path/"five_site_evidence_summary.csv",index=False)
    holds.to_csv(path/"original_14_HOLD_special_review.csv",index=False)
    manifest=dict(schema="STAGE20_PHASE_TRANSFER_EVIDENCE_REVIEW_v1",
        stage19_root=str(root),stage19_input_csv_sha256=digest(inputfile),
        stage19_manifest_sha256=digest(root/"manifest.json"),
        script_sha256=digest(Path(__file__)),stage17_plan_sha256=SHA17,
        number_targets=4884,number_original_holds=14,number_approved=0,
        n_halfhour_interpolated=int(out.ERA5_temporal_method.eq(
            "LINEAR_INTERPOLATION_HALFHOUR").sum()),
        n_ERA_ice_RH_above100=int(out.ERA5_ice_RH_above100_subzero.sum()),
        n_Td_transfer_negative_water_VPD=int(out.Td_transfer_negative_water_VPD.sum()),
        US_Ho1_timezone_status="PROVISIONAL_MINUS5_BADM_PENDING",
        shared_grid_ICh_ICt_not_independent=True,
        scientific_status="ALL_4884_HOLD_NO_DATM_APPROVAL",
        no_original_forcing_DATM_CIME_Slurm_changes=True,
        references=["https://confluence.ecmwf.int/pages/viewpage.action?pageId=185075856",
                    "https://www.npl.co.uk/resources/q-a/dew-point-and-relative-humidity"])
    (path/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print("STAGE20 REPORT:",path)
    print("Only isolated HOME reports written; no raw/forcing/DATM/model/Slurm changes")
    return 0

if __name__=="__main__":
    raise SystemExit(main())

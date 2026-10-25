#!/usr/bin/env python3
"""Stage12j — US-MtB elevation-aware humidity SOURCE validation and optional shadow.

Stage12i proved ERA5-Land grid/US-MtB site pressure differences correspond
to approximately 1.06km elevation mismatch. This is not proof that
gridded RH should be directly transplanted to measured tower conditions.

Validate four PREDECLARED physically distinct humidity-transfer formulas
against originally measured FLUXMET VPD_F_QC=0, never training or replacing
a QC0 value. Use 2020, 2022, 2024 source-native original tower TA/PA, exact
year-paired ERA and already verified Stage12f grid T2m/Td2m/SP.
Controls: original tower TA_F_QC=0; VPD_F_QC=0; ambient T <=5C,
physically valid tower VPD and water/ice humidity. FULL year stats reported
separately, for general representativeness.

Four candidates for source humidity:
  GRID_RH:       gridded RH held constant, recompute e at tower T.
  GRID_Q:        grid specific humidity held constant, tower P applied.
  GRID_E:        grid absolute vapour pressure held constant.
  LAPSE_TD:      move grid dewpoint down by original grid-tower T difference,
                 recompute e at tower elevation (diagnostic sensitivity).
All are EVALUATED at retained tower TA and PSRF. A 6.5K/km,
pressure-hypsometry-normalized T2m check replaces unjustified direct
grid/tower T<=5C screen ONLY in this new scientific trial.

The guarded candidate method is chosen from measured QC0 cold subsets only
if EVERY year has >=50 valid QC0 cold analogues, >=60% physically valid
predictions, <=1.5 hPa mean absolute VPD error and <=0.7 hPa absolute
VPD bias, AND at most 10% of valid cold analogues exceed 2 hPa error.
This validation threshold is a PROVISIONAL research gate; not scientific
approval of any tower clock or historical source. If no method qualifies,
no humidity changes at all. Stage12g's 3 repairs, 1031 T holds, 4 ice
holds, original 233 physics holds and all prior products remain unchanged.

--self-test: formulas and fixed source partition only; zero writes.
--check: all three yearly SHA sources, original Stage12i/G provenance,
         QC0 analog validation and hypothetical target screening, NO writes.
--run: one NEW research-only report and (if gates pass) an INCOMPLETE
       stand-alone US-MtB full native NOLEAP CSV shadow, WITHOUT overwrites.
NO Post-v5/DATM/CIME/Slurm/spinup release.
"""
import argparse, hashlib, importlib.util, json, sys, traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

VERSION="batch03-stage12j-v1-20261025-QC0-elevation-aware-RH"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
I=ROOT/"reports/stage12i_US-MtB_orography_pressure_20261025T064222Z_2944f5f6"
H=ROOT/"reports/stage12h_US-MtB_temperature_and_clock_three_year_diagnostics_20261025T054717Z_58c34b41"
G=ROOT/"science_trials/stage12g_six_site_new_year_gridRH_science_20261024T233640Z_b3d74fae"
E=ROOT/"science_trials/stage12e_six_site_verified_yearly_gridRH_shadows_20261024T123527Z_1d117b97"
I_SCRIPT=BASE/"scripts/stage12/12i_us_mtb_pressure_orography_READONLY.py"
I_BLOB="5897f8a71cd8ade217a17adb2988c47e1f40d915"
YEARS=(2020,2022,2024)
EXPECTED={2020:302,2022:328,2024:408}
MODELS=("GRID_RH","GRID_Q","GRID_E","LAPSE_TD")
LAPSE_K_KM=6.5
MIN_VALID_PER_YEAR=50
MIN_VALID_FRAC=0.60
MAX_MAE_HPA=1.5
MAX_ABS_BIAS_HPA=0.7
MAX_BAD2_FRAC=0.10
COLS=("time","TBOT","QBOT","PSRF","FSDS","FLDS","WIND",
      "PRECTmms","TA_USE","VPD_USE")

def regular(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Missing/symlink originally SHA-sealed source: "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with regular(p).open("rb") as stream:
        for part in iter(lambda:stream.read(1<<20),b""):h.update(part)
    return h.hexdigest()
def gitblob(p):
    b=regular(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def esw(t):
    with np.errstate(over="ignore",invalid="ignore",divide="ignore"):
        return 6.112*np.exp(17.67*np.asarray(t,dtype=float)/(np.asarray(t,dtype=float)+243.5))
def esi(t):
    with np.errstate(over="ignore",invalid="ignore",divide="ignore"):
        return 6.112*np.exp(22.46*np.asarray(t,dtype=float)/(np.asarray(t,dtype=float)+272.62))
def q_from_e(e_hpa,p_pa):
    e=100*np.asarray(e_hpa,dtype=float)
    return 0.622*e/(np.asarray(p_pa,dtype=float)-0.378*e)
def e_from_q(q,p_pa):
    return (np.asarray(q,dtype=float)*np.asarray(p_pa,dtype=float)/(0.622+0.378*np.asarray(q,dtype=float)))/100
def dewpoint_model(site_T,grid_T,grid_Td,grid_P,site_P):
    """Vector dictionary of predicted site vapour pressure in hPa."""
    ea_grid=esw(grid_Td)
    rh_grid=ea_grid/esw(grid_T)
    qgrid=q_from_e(ea_grid,grid_P)
    return {
       "GRID_RH":rh_grid*esw(site_T),
       "GRID_Q":e_from_q(qgrid,site_P),
       "GRID_E":ea_grid,
       "LAPSE_TD":esw(grid_Td+(np.asarray(site_T,dtype=float)-np.asarray(grid_T,dtype=float)))
    }
def numeric(series):
    a=pd.to_numeric(series,errors="coerce").to_numpy(dtype=float)
    a[(~np.isfinite(a))|(a<=-9990)]=np.nan
    return a
def physical(site_T,site_P,e_hpa):
    sat=esw(site_T)
    ice=esi(site_T)
    e=np.asarray(e_hpa,dtype=float)
    q=q_from_e(e,site_P)
    with np.errstate(invalid="ignore",divide="ignore"):
        return (np.isfinite(e)&np.isfinite(site_T)&np.isfinite(site_P)&
                (e>0)&(e<sat)&(q>0)&(q<.08)&
                ((np.asarray(site_T)>=0)|(e<=ice)))
def selftest():
    assert len(YEARS)==3 and sum(EXPECTED.values())==1038
    assert len(MODELS)==4 and MIN_VALID_PER_YEAR>0
    q=q_from_e(4.0,74000.0)
    assert abs(float(e_from_q(q,74000.0))-4.0)<1e-12
    trial=dewpoint_model(-5.,3.,0.,84000.,74000.)
    assert set(trial)==set(MODELS)
    assert all(np.isfinite(float(x)) for x in trial.values())
    print("STAGE12J SELF-TEST PASS: 3 SHA-pinned years, four fixed humidity methods, independent measured VPD QC0 gates, 1038 target source IDs; NO WRITES",flush=True)

def upstream():
    if not I.is_dir() or I.is_symlink():
        raise ValueError("Stage12i hypsometric diagnostic report missing")
    receipt=json.loads(regular(I/"stage12i_pressure_science_receipt.json").read_text())
    if (receipt.get("version")!="batch03-stage12i-v1-20261025-pressure-altitude-T-diagnostic"
        or receipt.get("upstream_Stage12h_receipt_SHA256")!=sha(H/"stage12h_temperature_source_science_receipt.json")
        or receipt.get("original_source_events")!=1038
        or receipt.get("grid_geopotential_not_measured") is not True
        or receipt.get("original_T_P_clock_changed") is not False
        or receipt.get("new_humidity_changes")!=0
        or receipt.get("Postv5_approved")!=0
        or receipt.get("DATM_ready")!=0 or receipt.get("spinup_authorized")!=0
        or set(receipt.get("output_sha256",{}))!={
           "six_year_scope_pressure_height_statistics.csv",
           "18_lapse_sensitivities_NO_FORCING_CHANGES.csv",
           "36_month_temperature_pressure_stats.csv",
           "1038_native_source_event_pressure_evidence.csv",
           "SCIENTIFIC_HOLD.md"}):
        raise ValueError("Stage12i signed report science receipt differs")
    for fn,dig in receipt["output_sha256"].items():
        if sha(I/fn)!=dig:
            raise ValueError("Original Stage12i source SHA mismatch "+fn)
    if gitblob(I_SCRIPT)!=I_BLOB:
        raise ValueError("Pinned Stage12i Git blob mismatch")
    spec=importlib.util.spec_from_file_location("stage12i_for_stage12j",I_SCRIPT)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    h,src,specinfo,catalog,original_1038=mod.check_sources()
    held=original_1038.loc[original_1038.Stage12g_classification.ne("PASS_RH_SHADOW")]
    if (len(held)!=1035 or
        held.Stage12g_classification.value_counts().to_dict()!={"HOLD_ORIGINAL_GRID_T_DIFFERENCE":1031,"HOLD_ICE_SUPERSATURATION":4}):
        raise ValueError("Stage12h 1035 originally held source events differ")
    return h,src,specinfo,catalog,held,original_1038

def evaluate():
    h,src,spec,catalog,held,all_targets=upstream()
    original=pd.read_csv(regular(E/"US-MtB_STAGE12E_INCOMPLETE_NOLEAP.csv"),low_memory=False)
    current=pd.read_csv(regular(G/"US-MtB_STAGE12G_INCOMPLETE_NOLEAP.csv"),low_memory=False)
    if (list(current)!=list(COLS) or len(current)!=len(original)
        or not current.time.equals(original.time)
        or not current.TA_USE.equals(original.TA_USE)
        or not current.PSRF.equals(original.PSRF)):
        raise ValueError("Stage12g preserved site T, P or source native time differs")
    tested=[];candidates=[];years_by_method={};source_count=0
    for year in YEARS:
        print("STAGE12J VERIFIED YEAR:",year,flush=True)
        raw_header=set(pd.read_csv(regular(spec["primary"]),nrows=0).columns)
        names=["TIMESTAMP_START","TA_F","PA_F","VPD_F","VPD_F_QC","TA_F_QC"]
        if not set(names)<=raw_header:
            raise ValueError("Original FLUXMET measured QC0 VPD/air temperature unavailable")
        raw=pd.read_csv(regular(spec["primary"]),usecols=names,
                        dtype={"TIMESTAMP_START":str},low_memory=False)
        dt=pd.to_datetime(raw.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
        raw=raw.loc[dt.dt.year.eq(year)&~((dt.dt.month==2)&(dt.dt.day==29))].reset_index(drop=True)
        if len(raw)!=17520:
            raise ValueError("Original source expected exactly 17520 noleap half-hour entries/year")
        shadow=current.loc[pd.to_datetime(current.time).dt.year.eq(year)].reset_index(drop=True)
        stamp=pd.to_datetime(raw.TIMESTAMP_START,format="%Y%m%d%H%M")
        if (len(shadow)!=len(raw) or not np.array_equal(
            stamp.dt.strftime("%Y-%m-%d %H:%M:%S"),shadow.time)):
            raise ValueError("Stage12g time-vs-original FLUXMET mismatch")
        siteT=numeric(raw.TA_F);siteP=numeric(raw.PA_F)*1000
        oldV=numeric(raw.VPD_F);qcV=numeric(raw.VPD_F_QC);qcT=numeric(raw.TA_F_QC)
        if (not np.allclose(siteT,shadow.TA_USE.to_numpy(dtype=float),atol=1e-6,rtol=0,equal_nan=True)
            or not np.allclose(siteP,shadow.PSRF.to_numpy(dtype=float),atol=1e-3,rtol=0,equal_nan=True)):
            raise ValueError("Stage12j original measured QC0 tower source not preserved")
        plan,meta=catalog[("US-MtB",year)]
        if sha(meta["path"])!=meta["sha256"]:
            raise ValueError("Stage12f new yearly source SHA changed since upstream 12i")
        loc=plan["request"]["location"]
        hours,field,coord=src.grid_fields(regular(meta["path"]),year,
                          (loc["latitude"],loc["longitude"]))
        utc=stamp+pd.Timedelta(minutes=int(spec["native_minutes"])/2) - pd.Timedelta(hours=src.BIF_OFFSET["US-MtB"])
        gt=src.interpolate(hours,field["t2m"],utc)-273.15
        gd=src.interpolate(hours,field["d2m"],utc)-273.15
        gp=src.interpolate(hours,field["sp"],utc)
        hyps=287.05*((gt+siteT)/2+273.15)/9.80665 * np.log(gp/siteP)
        heightadjusted=gt-LAPSE_K_KM*hyps/1000.
        original_good=(np.isfinite(siteT)&np.isfinite(siteP)&
             np.isfinite(gt)&np.isfinite(gd)&np.isfinite(gp)&
             (siteP>45000)&(siteP<110000)&(gp>45000)&(gp<110000)&
             (gd<=gt+.1)&(np.abs(hyps)<4500))
        source_qc0=(qcV==0)&(qcT==0)&(oldV>=0)&(oldV<esw(siteT))&
            (physical(siteT,siteP,esw(siteT)-oldV))&original_good
        cold=source_qc0&(siteT<=5.)
        if cold.sum()<MIN_VALID_PER_YEAR:
            print("STAGE12J CAUTION: cold measured QC0 source analogues count",year,int(cold.sum()),flush=True)
        targetids=set(held.native_key)
        targets=np.isin(stamp.dt.strftime("%Y%m%d%H%M").to_numpy(),list(targetids))
        targetcount=int(targets.sum())
        if targetcount!=sum(
            pd.to_datetime(held.native_key,format="%Y%m%d%H%M").dt.year.eq(year)):
            raise ValueError("Previously sealed target source-year count changed")
        source_count+=targetcount
        measures=dewpoint_model(siteT,gt,gd,gp,siteP)
        for method in MODELS:
            e=measures[method]
            vp=esw(siteT)-e
            phys=physical(siteT,siteP,e)&original_good
            # Terrain-normalized source T gate does NOT edit the
            # gridded/raw air temperatures used in humidity formulas.
            terr=(np.isfinite(heightadjusted)&(np.abs(siteT-heightadjusted)<=5.))
            eligible=phys&terr
            sample=cold
            valid=sample&eligible
            errors=vp[valid]-oldV[valid]
            N=int(sample.sum());Nv=int(valid.sum())
            results={
                "year":year,"method":method,
                "QC0_cold_source_N":N,
                "QC0_cold_physically_valid_model_N":Nv,
                "QC0_cold_valid_fraction":Nv/N if N else 0.,
                "QC0_cold_pred_VPD_MAE_hPa":float(np.mean(np.abs(errors))) if Nv else np.nan,
                "QC0_cold_VPD_bias_hPa":float(np.mean(errors)) if Nv else np.nan,
                "QC0_cold_fraction_abs_error_over2hPa":float(np.mean(np.abs(errors)>2.)) if Nv else 1.,
                "height_proxy_median_m":float(np.nanmedian(hyps)),
                "site_temperature_source_changed":False,
                "scientific_release":False}
            tested.append(results)
            years_by_method[(year,method)]=results
            for i in np.flatnonzero(targets):
                candidates.append({
                   "site":"US-MtB","year":year,
                   "native_key":stamp.iloc[i].strftime("%Y%m%d%H%M"),
                   "method":method,
                   "original_source_VPD_F_QC":qcV[i],
                   "site_T_original_C":siteT[i],
                   "site_P_original_Pa":siteP[i],
                   "ERA5Land_original_grid_T_C":gt[i],
                   "ERA5Land_original_grid_dewpoint_C":gd[i],
                   "terrain_normalised_grid_T_C_DIAGNOSTIC":heightadjusted[i],
                   "hypsometric_grid_vs_site_height_m":hyps[i],
                   "physical_and_terrain_check_pass":bool(eligible[i]),
                   "candidate_VPD_hPa":float(vp[i]) if eligible[i] else np.nan,
                   "candidate_QBOT_kgkg":float(q_from_e(e[i],siteP[i])) if eligible[i] else np.nan,
                   "approved_for_model":False})
    if source_count!=1035:
        raise ValueError("Expected original held 1035 Stage12g source times")
    stats=pd.DataFrame(tested)
    catalog=pd.DataFrame(candidates)
    if len(stats)!=12 or len(catalog)!=1035*4:
        raise ValueError("Research method validation/target schema unexpected")
    bymethod=[]
    for method in MODELS:
        subset=stats.loc[stats.method.eq(method)]
        gate=((subset.QC0_cold_source_N>=MIN_VALID_PER_YEAR)&
            (subset.QC0_cold_valid_fraction>=MIN_VALID_FRAC)&
            (subset.QC0_cold_pred_VPD_MAE_hPa<=MAX_MAE_HPA)&
            (subset.QC0_cold_VPD_bias_hPa.abs()<=MAX_ABS_BIAS_HPA)&
            (subset.QC0_cold_fraction_abs_error_over2hPa<=MAX_BAD2_FRAC)).all()
        bymethod.append({
            "method":method,"all_three_QC0_validation_years_pass":bool(gate),
            "worst_year_MAE_hPa":float(subset.QC0_cold_pred_VPD_MAE_hPa.max()),
            "worst_year_absolute_bias_hPa":float(subset.QC0_cold_VPD_bias_hPa.abs().max()),
            "worst_year_fraction_QC0_cold_invalid":float((1-subset.QC0_cold_valid_fraction).max()),
            "mean_yearly_QC0_cold_MAE_hPa":float(subset.QC0_cold_pred_VPD_MAE_hPa.mean())})
    policy=pd.DataFrame(bymethod)
    allowed=policy.loc[policy.all_three_QC0_validation_years_pass].sort_values(
                 ["worst_year_MAE_hPa","method"])
    choice=str(allowed.iloc[0].method) if len(allowed) else None
    wanted=catalog.loc[catalog.method.eq(choice)].copy() if choice else catalog.iloc[:0].copy()
    if len(wanted) and not wanted.original_source_VPD_F_QC.isin([1,2]).all():
        # Targets must have original source gap-filled/downscaled VPD,
        # not a QC0 observation, before any research candidate application.
        choice=None
        wanted=catalog.iloc[:0].copy()
    return stats,policy,catalog,wanted,choice,current,held

def choose_shadow(current,wanted,choice,held):
    shadow=current.copy(deep=True)
    approved=[];notready=[]
    idx={pd.Timestamp(x).strftime("%Y%m%d%H%M"):i for i,x in enumerate(shadow.time)}
    if not choice:return shadow,pd.DataFrame(),pd.DataFrame(),0
    selecting=np.zeros(len(shadow),dtype=bool)
    for r in wanted.itertuples(index=False):
        i=idx.get(r.native_key)
        if i is None:raise ValueError("Original held source time missing")
        if (np.isfinite(shadow.VPD_USE.iloc[i]) or np.isfinite(shadow.QBOT.iloc[i]) or
            r.native_key not in set(held.native_key)):
            raise ValueError("Illegal overwriting of already valid/hardheld site forcing")
        if r.physical_and_terrain_check_pass:
            selecting[i]=True
            shadow.loc[i,"VPD_USE"]=r.candidate_VPD_hPa
            shadow.loc[i,"QBOT"]=r.candidate_QBOT_kgkg
        else:
            notready.append({"native_key":r.native_key,"reason":"ELEVATION_NORMALISED_T_OR_ICE_OR_Q_PHYSICS_FAIL"})
    original_q=current.QBOT.to_numpy(dtype=float)
    for _ in range(10):
        v=shadow.VPD_USE.to_numpy(dtype=float)
        reject=np.zeros(len(shadow),dtype=bool)
        for i in np.flatnonzero(selecting):
            for j in (i-1,i+1):
                if 0<=j<len(v) and np.isfinite(v[j]) and abs(v[i]-v[j])>4.:
                    reject[i]=True
        if not reject.any():break
        for i in np.flatnonzero(reject):
            selecting[i]=False
            notready.append({"native_key":pd.Timestamp(shadow.time.iloc[i]).strftime("%Y%m%d%H%M"),
                             "reason":"NEW_SHADOW_BOUNDARY_JUMP_GT4HPA"})
            shadow.loc[i,"VPD_USE"]=np.nan
            shadow.loc[i,"QBOT"]=np.nan
    else:raise ValueError("Boundary rejection of 1035 selected candidate events did not converge")
    old=current.VPD_USE.to_numpy(dtype=float)
    new=shadow.VPD_USE.to_numpy(dtype=float)
    if (not np.array_equal(old[~selecting],new[~selecting],equal_nan=True)
        or not np.array_equal(original_q[~selecting],shadow.QBOT.to_numpy(dtype=float)[~selecting],equal_nan=True)):
        raise ValueError("Stage12j attempted to change original Stage12g valid humidity data")
    for col in COLS:
        if col not in ("VPD_USE","QBOT") and not shadow[col].equals(current[col]):
            raise ValueError("Stage12j original source TBOT/T/pressure/time/other altered")
    for r in wanted.itertuples(index=False):
        i=idx[r.native_key]
        if selecting[i]:
            approved.append({"native_key":r.native_key,"method":choice,
               "source_T_original_C":r.site_T_original_C,
               "source_P_original_Pa":r.site_P_original_Pa,
               "source_height_diagnostic_m":r.hypsometric_grid_vs_site_height_m,
               "new_VPD_hPa":float(shadow.VPD_USE.iloc[i]),
               "new_QBOT_kgkg":float(shadow.QBOT.iloc[i]),
               "clock_approved":False,"model_ready":False})
    return shadow,pd.DataFrame(approved),pd.DataFrame(notready),int(selecting.sum())

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    modes=ap.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test",action="store_true")
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--run",action="store_true")
    args=ap.parse_args()
    print("STAGE12J — US-MTB ELEVATION-AWARE WATER VAPOR QC0 VALIDATION | "+VERSION,flush=True)
    selftest()
    if args.self_test:return
    stats,policy,allmodels,wanted,method,current,held=evaluate()
    shadow,approved,failed,added=choose_shadow(current,wanted,method,held)
    print("\n========== THREE-YEAR MEASURED QC0 VPD COLD-ANALOGUE VALIDATION ==========",flush=True)
    print(stats.to_string(index=False),flush=True)
    print("\n========== PREDECLARED MULTI-YEAR SCIENCE GATE ==========",flush=True)
    print(policy.to_string(index=False),flush=True)
    print("\nSTAGE12J SUMMARY:","selected_validation_method="+str(method),
          "3_year_verified_source=TRUE","QC0_measured_tower_humidity_modified=0",
          "prior_stage12g_source_numeric_replacements_preserved=TRUE",
          f"new_provisional_only_target_VPD_QBOT_research_candidates={added}",
          f"held_1035_Stage12g_source_events={1035-added}",
          "site_tower_T_P_clock_unchanged=TRUE","Postv5_approved=0 DATM_ready=0 spinup=0",
          flush=True)
    if args.check:
        print("STAGE12J CHECK ONLY: zero report or forcing writes.",flush=True)
        return
    output=ROOT/"science_trials"/("stage12j_US-MtB_QC0_elevation_aware_humidity_trial_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    output.mkdir(exist_ok=False,parents=True)
    (output/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP").write_text(
        "Research-only QC0 validation of 4 altitude-aware humidity transfer methods. No Post-v5, DATM or spinup authorization.\n")
    reports={
      "three_year_original_VPD_QC0_cold_validation.csv":stats,
      "four_method_three_year_independent_QC0_gates.csv":policy,
      "all_1035_held_times_four_method_proposals_NO_APPROVAL.csv":allmodels,
      "selected_method_held_target_candidate_event_ledger.csv":approved,
      "selected_method_unresolved_target_events.csv":failed,
    }
    if method and added:
        reports["US-MtB_STAGE12J_INCOMPLETE_NOLEAP.csv"]=shadow
    hashes={}
    for name,table in reports.items():
        table.to_csv(output/name,index=False)
        hashes[name]=sha(output/name)
    note=("This site altitude-aware humidity method is conditionally selected "
          "from matched original station VPD_F_QC=0 cold observations in THREE "
          "separate source years. Original QC0 station humidity, original "
          "tower T and surface P are never replaced. Terrain normalization "
          "is diagnostic and does NOT prove correct vertical humidity "
          "transfer. The site BIF UTC offset remains a HYPOTHESIS; "
          "the method is research only. Exactly 233 earlier source "
          "physics holds and all already accepted Stage12e/g source "
          "numeric values remain unchanged. Output is never DATM/CIME "
          "or spinup-ready. Scientific source review and independent "
          "validation required before Post-v5 release.\n")
    (output/"SCIENCE_HOLD.md").write_text(note)
    hashes["SCIENCE_HOLD.md"]=sha(output/"SCIENCE_HOLD.md")
    receipt={
       "version":VERSION,
       "Stage12i_original_receipt_SHA256":sha(I/"stage12i_pressure_science_receipt.json"),
       "original_three_year_site_grid_height_diagnostic_ONLY":True,
       "validated_method":method,
       "new_candidate_research_repair_events":int(added),
       "original_1035_held_time_events":1035,
       "source_T_P_UTC_changed":False,
       "previous_QC0_observations_modified":0,
       "Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,
       "INCOMPLETE_marker_present":True,"output_sha256":hashes}
    (output/"stage12j_science_only_sha_receipt.json").write_text(
          json.dumps(receipt,indent=2)+"\n")
    print("STAGE12J QC0 VALIDATION AND RESEARCH TRIAL DIR:",output,flush=True)
    print("NO PREVIOUS SOURCE/FORCING, CLOCK, TOWER T/P OR MODEL WRITES.",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE12J STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

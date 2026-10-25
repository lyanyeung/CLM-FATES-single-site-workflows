#!/usr/bin/env python3
"""Stage12m — read-only US-NR1 / US-Me6 source temperature and VPD holds.

The Stage12g nine-source-year receipt established:
 US-Me6: 78 source-covered, 14 valid RH-only research shadows, 29 T holds,
         35 new adjacent-VPD >4 hPa holds, 2 missing source years.
 US-NR1: 22 source-covered, 0 valid, 19 T holds, 3 VPD holds.
Do not download further years automatically or relax 5 C / 4 hPa guards.

Read only the exact SHA-sealed latest Stage12g six-site shadow,
source-native held event ledger, original Stage12e forcing and exact
Stage12f new verified grid years. Reconstruct gridded surface pressure
and temperature at the unchanged EC tower native half-hour midpoint
using prior published-but-provisional BIF offset, compare tower/grid
pressure and temperature, approximate pressure-height difference.
Reconstruct rejected candidate VPD from already-reported Stage12g RH
ONLY as diagnostic: adjacent VPD in FINAL shadow may be missing since
both endpoints can be rejected simultaneously. This reconstruction is
NOT Stage12g's full chronological pre-rejection boundary history.
No changes to anything except optional NEW isolated diagnostic reports.

--self-test: independent numeric synthetic tests, no source reads/writes
--check: source SHA, native time checks and in-memory science diagnostics
--run: same + write report-only new SHA receipt
"""
import argparse
import hashlib
import importlib.util
import json
import sys
import traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

VERSION="batch03-stage12m-v1-20261025-NR1-Me6-T-VPD-hold-no-writes"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
BASE=Path.home()/"CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
G=ROOT/"science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f"
E=ROOT/"science_trials/stage12e_six_site_verified_yearly_gridRH_shadows_20261024T123527Z_1d117b97"
G_SCRIPT=BASE/"scripts/stage12/12g_apply_new_year_ERA5Land_RH_shadow.py"
G_BLOB="14eabe09a56614808d6186d88fa5576233ed240b"
REASONS={"HOLD_SITE_GRID_T_DIFF_GT5C","HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA"}
SITES={"US-NR1":{2022:{"HOLD_SITE_GRID_T_DIFF_GT5C":19,
                       "HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA":3}},
       "US-Me6":{2015:None,2017:None}}
EXPECTED_SITE={"US-NR1":{"coverage":22,"repair":0,"holds":22,"T":19,"J":3},
               "US-Me6":{"coverage":78,"repair":14,"holds":64,"T":29,"J":35}}

def file(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():
        raise ValueError("Source missing/symlinked: "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with file(p).open("rb") as stream:
        for b in iter(lambda:stream.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()
def blob(p):
    data=file(p).read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def mainmodule():
    if blob(G_SCRIPT)!=G_BLOB:
        raise ValueError("Stage12g original script Git blob changed")
    spec=importlib.util.spec_from_file_location("stage12m_pinned_source_stage12g",G_SCRIPT)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
def selftest():
    assert sum(x["coverage"] for x in EXPECTED_SITE.values())==100
    assert sum(x["holds"] for x in EXPECTED_SITE.values())==86
    assert sum(x["repair"] for x in EXPECTED_SITE.values())==14
    assert sum(x["T"] for x in EXPECTED_SITE.values())==48
    assert sum(x["J"] for x in EXPECTED_SITE.values())==38
    assert len(REASONS)==2
    # Sign of proxy: higher grid pressure -> grid lower than site.
    z=287.05*280./9.80665*np.log(90000./80000.)
    assert 900<z<1000
    print("STAGE12M SELF-TEST PASS: 100 exact source events, 48 T/38 jump holds and 14 prior numeric repairs, read-only",flush=True)
def evidence():
    if not G.is_dir() or G.is_symlink() or not E.is_dir() or E.is_symlink():
        raise ValueError("Expected original signed nine-year Stage12g and Stage12e trial")
    file(G/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    r=json.loads(file(G/"stage12g_research_only_sha_receipt.json").read_text())
    if (r.get("version")!="batch03-stage12g-v1-20261025-sha-verified-new-year-gridRH"
        or r.get("new_sha_verified_source_site_years")!=9
        or r.get("new_covered_original_missing_year_events")!=1334
        or r.get("new_numerical_ERA5Land_RH_only_research_repairs")!=138
        or r.get("original_233_physics_holds_untouched") is not True
        or r.get("original_six_site_T_P_native_clock_unchanged") is not True
        or r.get("all_original_Stage12e_finite_humidity_untouched") is not True
        or r.get("INCOMPLETE_marker_present") is not True
        or r.get("Postv5_approved")!=0 or r.get("DATM_ready")!=0
        or r.get("spinup_authorized")!=0 or
        len(r.get("output_sha256",{}))!=11):
        raise ValueError("New nine-source-year Stage12g source science receipt differs")
    for name,digest in r["output_sha256"].items():
        if sha(G/name)!=digest:
            raise ValueError("Nine-source-year original Stage12g SHA changed: "+name)
    mod=mainmodule()
    stage10,specs,orig_hold,orig_missing,catalog,pending=mod.sources()
    if not set((site,year) for site,years in SITES.items() for year in years).issubset(catalog):
        raise ValueError("Expected exactly NR1 2022 and Me6 2015, 2017 verified source")
    reports=pd.read_csv(file(G/"six_site_stage12g_science_status.csv"))
    for site,expected in EXPECTED_SITE.items():
        rows=reports.loc[reports.site.eq(site)]
        if (len(rows)!=1 or int(rows.iloc[0].new_site_year_verified_event_coverage)!=expected["coverage"]
            or int(rows.iloc[0].new_humidity_only_numeric_research_repairs)!=expected["repair"]
            or int(rows.iloc[0].new_downloaded_year_humidity_holds)!=expected["holds"]):
            raise ValueError("Stage12g current site science status differs: "+site)
    held=pd.read_csv(file(G/"2810_original_missing_year_source_review_after_stage12g.csv"),
                     dtype={"native_key":str,"site":str},low_memory=False)
    repairs=pd.read_csv(file(G/"new_ERA5Land_year_source_RH_repair_candidates.csv"),
                        dtype={"native_key":str,"site":str},low_memory=False)
    if len(repairs)!=138:
        raise ValueError("Stage12g accepted source candidate ledger incomplete")
    for site,expected in EXPECTED_SITE.items():
        got=held.loc[held.site.eq(site)&held.reason.isin(REASONS)]
        count=got.reason.value_counts().to_dict()
        if (len(got)!=expected["holds"] or count.get("HOLD_SITE_GRID_T_DIFF_GT5C",0)!=expected["T"]
            or count.get("HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA",0)!=expected["J"]
            or len(repairs.loc[repairs.site.eq(site)])!=expected["repair"]):
            raise ValueError("Stage12g original site hold reason ledger mismatch "+site)
    return mod,stage10,specs,catalog,held,repairs,r

def build():
    mod,stage10,specs,catalog,held,repairs,receipt=evidence()
    rows=[]
    cases=[]
    for site,years in SITES.items():
        print("STAGE12M VERIFIED SITE:",site,flush=True)
        original=pd.read_csv(file(E/(site+"_STAGE12E_INCOMPLETE_NOLEAP.csv")),low_memory=False)
        current=pd.read_csv(file(G/(site+"_STAGE12G_INCOMPLETE_NOLEAP.csv")),low_memory=False)
        if (len(original)!=len(current) or list(original)!=list(current)
            or not original.time.equals(current.time)
            or not original.TA_USE.equals(current.TA_USE)
            or not original.PSRF.equals(current.PSRF)):
            raise ValueError("Original EC tower time/T/P changed for "+site)
        times=pd.to_datetime(current.time,format="%Y-%m-%d %H:%M:%S",errors="raise")
        keys=times.dt.strftime("%Y%m%d%H%M")
        if keys.duplicated().any():raise ValueError("Duplicate original native time "+site)
        lookup=pd.Series(np.arange(len(keys)),index=keys.to_numpy())
        site_hold=held.loc[held.site.eq(site)&held.reason.isin(REASONS)].copy()
        site_good=repairs.loc[repairs.site.eq(site)]
        source_years={}
        for year in years:
            plan,meta=catalog[(site,year)]
            loc=plan["request"]["location"]
            source_years[year]=(plan,meta)
            if sha(meta["path"])!=meta["sha256"]:
                raise ValueError("Stage12f gridded year source SHA differs "+site+":"+str(year))
            hours,field,coord=stage10.grid_fields(
                  file(meta["path"]),year,(loc["latitude"],loc["longitude"]))
            year_hold=site_hold.loc[
                pd.to_datetime(site_hold.native_key,format="%Y%m%d%H%M").dt.year.eq(year)]
            if not len(year_hold):
                continue
            idx=lookup.loc[year_hold.native_key].to_numpy(dtype=int)
            t0=current.TA_USE.iloc[idx].to_numpy(dtype=float)
            p0=current.PSRF.iloc[idx].to_numpy(dtype=float)
            stamp=times.iloc[idx]
            step=int(specs[site]["native_minutes"])
            utc=stamp+pd.Timedelta(minutes=step/2)-pd.Timedelta(hours=stage10.BIF_OFFSET[site])
            tgrid=stage10.interpolate(hours,field["t2m"],utc)-273.15
            pgrid=stage10.interpolate(hours,field["sp"],utc)
            if (not np.allclose(tgrid,year_hold.grid_T2M_C.to_numpy(dtype=float),
                                atol=1e-7,rtol=0,equal_nan=True)
                or not np.array_equal(t0,year_hold.original_tower_T_C.to_numpy(dtype=float),
                                      equal_nan=True)):
                raise ValueError("Grid temperature or preserved original tower air T does not match signed Stage12g hold ledger")
            with np.errstate(divide="ignore",invalid="ignore"):
                dz=(287.05/9.80665)*((tgrid+t0)/2+273.15)*np.log(pgrid/p0)
            rh=year_hold.grid_water_RH_pct.to_numpy(dtype=float)
            vpd_candidate=mod.esw(t0)*(1-rh/100.)
            v=current.VPD_USE.to_numpy(dtype=float)
            for n,j in enumerate(idx):
                adjacent=[float(v[k]) for k in (j-1,j+1)
                          if 0<=k<len(v) and np.isfinite(v[k])]
                diffs=[abs(float(vpd_candidate[n])-z) for z in adjacent]
                reason=year_hold.reason.iloc[n]
                if reason=="HOLD_SITE_GRID_T_DIFF_GT5C" and not abs(float(t0[n]-tgrid[n]))>5-1e-7:
                    raise ValueError("Signed original T-grid mismatch label disagrees")
                cases.append({
                    "site":site,"year":year,
                    "original_native_key":str(year_hold.native_key.iloc[n]),
                    "original_held_science_reason":reason,
                    "original_EC_T_C":float(t0[n]),
                    "ERA5Land_gridded_T_C":float(tgrid[n]),
                    "tower_minus_grid_T_C":float(t0[n]-tgrid[n]),
                    "original_EC_surface_pressure_Pa":float(p0[n]),
                    "ERA5Land_surface_pressure_Pa":float(pgrid[n]),
                    "pressure_grid_minus_tower_Pa":float(pgrid[n]-p0[n]),
                    "pressure_height_tower_minus_grid_proxy_m":float(dz[n]),
                    "original_ERA5Land_water_RH_pct":float(rh[n]),
                    "diagnostic_held_GRID_RH_candidate_VPD_hPa":float(vpd_candidate[n]),
                    "finite_neighbors_in_final_shadow":len(adjacent),
                    "max_abs_candidate_to_final_shadow_neighbor_VPD_hPa":
                        max(diffs) if diffs else np.nan,
                    "full_original_pre_rejection_neighbor_sequence_reconstructed":False,
                    "original_QC0_tower_T_P_clock_changed":False,
                    "new_science_approval":False
                })
    report=pd.DataFrame(cases).sort_values(["site","year","original_native_key"])
    if (len(report)!=86 or
        report.groupby(["site","original_held_science_reason"]).size().to_dict()!={ 
          ("US-Me6","HOLD_SITE_GRID_T_DIFF_GT5C"):29,
          ("US-Me6","HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA"):35,
          ("US-NR1","HOLD_SITE_GRID_T_DIFF_GT5C"):19,
          ("US-NR1","HOLD_NEW_ADJACENT_VPD_JUMP_GT4HPA"):3}):
        raise ValueError("Original exact 86 separate T/jump scientific holds not conserved")
    metrics=[]
    for (site,year,reason),g in report.groupby(
            ["site","year","original_held_science_reason"]):
        metrics.append({
            "site":site,"year":year,"scientific_hold_reason":reason,"N":len(g),
            "mean_tower_minus_grid_T_C":float(g.tower_minus_grid_T_C.mean()),
            "median_tower_minus_grid_T_C":float(g.tower_minus_grid_T_C.median()),
            "median_abs_T_difference_C":float(g.tower_minus_grid_T_C.abs().median()),
            "median_grid_minus_site_pressure_Pa":float(g.pressure_grid_minus_tower_Pa.median()),
            "median_pressure_relative_height_proxy_m":
                  float(g.pressure_height_tower_minus_grid_proxy_m.median()),
            "n_rejected_jump_events_with_final_finite_neighbor":
                  int((g.finite_neighbors_in_final_shadow>0).sum()),
            "n_rejected_jump_events_final_candidate_neighbor_absVPD_gt4":
                  int((g.max_abs_candidate_to_final_shadow_neighbor_VPD_hPa>4).sum()),
            "original_site_clock_approved":False,"forcing_changes":0,
            "scientific_release":False
        })
    summary=pd.DataFrame(metrics).sort_values(["site","year","scientific_hold_reason"])
    return report,summary

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    flags=ap.add_mutually_exclusive_group(required=True)
    flags.add_argument("--self-test",action="store_true")
    flags.add_argument("--check",action="store_true")
    flags.add_argument("--run",action="store_true")
    a=ap.parse_args()
    print("STAGE12M — NON-MTB NEW SOURCE TEMPERATURE AND VPD HOLD QA | "+VERSION,flush=True)
    selftest()
    if a.self_test:return
    detail,stats=build()
    print("\n========== NR1 / ME6 ORIGINAL HOLD EVIDENCE ==========",flush=True)
    print(stats.to_string(index=False),flush=True)
    print("\n========== 86 ORIGINAL HOLDS, SOURCE JUMP NEIGHBOR INSPECTION ==========",flush=True)
    print(detail.groupby(["site","original_held_science_reason"]).agg(
         N=("original_native_key","size"),
         final_finite_neighbor_cases=("finite_neighbors_in_final_shadow",
             lambda x:int((x>0).sum())),
         final_neighbor_diff_over4hPa=(
           "max_abs_candidate_to_final_shadow_neighbor_VPD_hPa",
             lambda x:int((x>4).sum()))
    ).to_string(),flush=True)
    print("STAGE12M SUMMARY: original_86_stage12g_science_holds_preserved=TRUE "
          "source_100_covered_events=TRUE "
          "new_numeric_RH_repair_candidates=0",flush=True)
    print("STAGE12M VERIFIED: 48 temperature holds; 38 boundary jump holds; "
          "no gap repairs/temperature changes/clock approval; "
          "Postv5=0 DATM=0 spinup=0",flush=True)
    if a.check:
        print("STAGE12M CHECK ONLY: no reports, forcing or model writes.",flush=True)
        return
    out=ROOT/"reports"/("stage12m_nonMtB_NRI_Me6_original_T_VPD_HOLD_diagnosis_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    tables={"86_exact_science_held_event_source_and_neighbor_evidence.csv":detail,
            "source_year_by_hold_reason_diagnostic.csv":stats}
    for name,data in tables.items():
        data.to_csv(out/name,index=False)
    (out/"SCIENCE_HOLD.md").write_text(
       "Stage12m is a read-only scientific source diagnostic, NO VPD repair. "
       "Relative heights use surface pressure proxy, NOT grid geopotential. "
       "For candidate VPD jump holds, the final Stage12g output may have "
       "simultaneously masked neighboring candidate values: finite final "
       "neighbors are NOT a complete source chronology. The earlier "
       "Stage12g 5C temperature and 4hPa VPD hold conditions remain "
       "UNCHANGED. Original EC station QC0, T, P and source time remain "
       "immutable; Stage12g 86 held events stay held. No Post-v5/DATM/spinup.\n")
    names=[*tables,"SCIENCE_HOLD.md"]
    rc={"version":VERSION,
      "nine_year_Stage12g_receipt_SHA256":sha(G/"stage12g_research_only_sha_receipt.json"),
      "source_covered_for_sites":100,
      "previous_stage12g_repairs_unchanged":14,
      "original_science_holds_unchanged":86,
      "original_tower_T_P_clock_unchanged":True,
      "new_scientific_approval":0,"Postv5_approved":0,
      "DATM_ready":0,"spinup_authorized":0,
      "output_SHA256":{n:sha(out/n) for n in names}}
    (out/"stage12m_science_hold_SHA_receipt.json").write_text(
        json.dumps(rc,indent=2)+"\n")
    print("STAGE12M READ-ONLY DIAGNOSTIC OUTPUT DIR:",out,flush=True)
    print("NO SOURCE, PREVIOUS STAGE12E/G, METEOROLOGY OR MODEL INPUTS MODIFIED.",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE12M STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc()
        raise SystemExit(2)

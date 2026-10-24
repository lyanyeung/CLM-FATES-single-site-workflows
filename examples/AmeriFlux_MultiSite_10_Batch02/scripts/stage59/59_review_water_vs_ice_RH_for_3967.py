#!/usr/bin/env python3
"""Stage59: source-pinned water-vs-ice saturation review for 3,967 accepted EC temperatures.

Water-basis RH, VPD, QBOT from Stage58 are unchanged. Diagnostic ice saturation
is calculated at original tower TA_F: e_ice=6.112*exp(22.46*T/(272.62+T)).
At subzero, e_actual = RH_water/100*es_water(T). Derive RH_ice and VPD_ice;
do NOT silently clip ice supersaturation or alter final forcing.
Also inventories original US-Ho1 site BIF files to expose missing UTC_OFFSET.
No source, previous stages, NetCDF forcing, DATM, CIME or Slurm writes.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
S58=ROOT/"reports/stage58_63_manual_T_approved_3967_T_total_20261024T110141Z_e65bde6c"
F58="4884_final_original_tower_temperature_policy.csv"
DEC_W="KEEP_ORIGINAL_TA_F_WITHIN8C"
DEC_M="KEEP_ORIGINAL_TA_F_MANUALLY_APPROVED_EXTREME_COLD_GT8C"
DEC_H="HOLD_HO1_LOCAL_UTC_OFFSET_PROVISIONAL"
SITES={"US-EML":1327,"US-GLE":295,"US-Ho1":917,"US-ICh":169,"US-ICt":2176}
RESULT="3967_water_vs_ice_humidity_sensitivity.csv"

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):
            h.update(block)
    return h.hexdigest()

def saturation_water(t):
    t=np.asarray(t,dtype=float)
    return 6.112*np.exp(17.67*t/(t+243.5))

def saturation_ice(t):
    t=np.asarray(t,dtype=float)
    return 6.112*np.exp(22.46*t/(t+272.62))

def qc_route(temp,rhi):
    if temp>=0:return "ABOVE_ZERO_WATER_REFERENCE"
    if rhi>105:return "REVIEW_ICE_RH_OVER105_PCT"
    if rhi>100:return "REVIEW_ICE_RH_100_TO105_PCT"
    return "SUBZERO_NO_ICE_SUPERSAT_NUMERIC_FLAG"

def load():
    if (S58/"INCOMPLETE_DO_NOT_USE").exists():
        raise ValueError("Stage58 source incomplete")
    meta=json.loads((S58/"manual_temperature_decision_manifest.json").read_text())
    report=S58/F58
    if (meta.get("schema")!="STAGE58_USER_MANUAL_EXTREME_COLD_TA_APPROVAL_ONLY_v1"
        or meta.get("n_stage11_records")!=4884
        or meta.get("n_manual_T_approved")!=63
        or meta.get("n_total_original_T_retained")!=3967
        or meta.get("n_Ho1_provisional_offset_hold")!=917
        or meta.get("approved_for_DATM") is not False
        or meta.get("humidity_and_phase_science_HOLD") is not True
        or meta.get("no_original_or_model_forcing_edits") is not True
        or meta.get("report_sha256",{}).get(F58)!=sha(report)):
        raise ValueError("Pinned Stage58 temperature-only scientific contract failed")
    for fname,digest in meta["report_sha256"].items():
        if sha(S58/fname)!=digest:
            raise ValueError("Stage58 report SHA256 mismatch: "+fname)
    df=pd.read_csv(report,dtype={"site":str,"local_key":str})
    if len(df)!=4884 or Counter(df.site)!=Counter(SITES):
        raise ValueError("Stage58 population/site census mismatch")
    counts=Counter(df.final_temperature_decision)
    if (counts.get(DEC_W)!=3904 or counts.get(DEC_M)!=63
        or counts.get(DEC_H)!=917 or len(counts)!=3):
        raise ValueError("Expected exact 3904+63+917 Stage58 decisions")
    if df.duplicated(["site","local_key"]).any():
        raise ValueError("Repeated site/local timestamp")
    accepted=df[df.final_temperature_decision.isin([DEC_W,DEC_M])].copy()
    if (len(accepted)!=3967 or not accepted.original_TA_F_retained.astype(str).str.lower().eq("true").all()
        or not accepted.temperature_accepted_RH_VPD_QBOT_numeric_candidate.astype(str).str.lower().eq("true").all()):
        raise ValueError("Stage58 original T and RH/VPD/QBOT numerical candidate flags changed")
    for c in ["TA_F","PA_F","ERA5_RH_water_pct_selected",
              "VPD_water_hPa_original_TA","QBOT_kgkg_original_TA_PA"]:
        if c not in accepted:
            raise ValueError("Required Stage58 original humidity field absent: "+c)
    return accepted,meta

def calculate(df):
    t=pd.to_numeric(df.TA_F,errors="raise").to_numpy(dtype=float)
    rhw=pd.to_numeric(df.ERA5_RH_water_pct_selected,errors="raise").to_numpy(dtype=float)
    pressure=pd.to_numeric(df.PA_F,errors="raise").to_numpy(dtype=float)
    esw=saturation_water(t)
    esi=saturation_ice(t)
    vapour_hpa=esw*rhw/100
    vpw=esw-vapour_hpa
    vpi=esi-vapour_hpa
    rhi=100*vapour_hpa/esi
    q=0.622*(vapour_hpa*100)/(pressure*1000-0.378*vapour_hpa*100)
    if (not np.isfinite(vpi).all() or not np.isfinite(rhi).all()
        or (rhw<=0).any() or (rhw>100.05).any()
        or (pressure<=50).any() or (pressure>=110).any()
        or not np.allclose(vpw,pd.to_numeric(df.VPD_water_hPa_original_TA),
                           rtol=1e-7,atol=1e-8)
        or not np.allclose(q,pd.to_numeric(df.QBOT_kgkg_original_TA_PA),
                            rtol=1e-7,atol=1e-9)):
        raise ValueError("Stage58 water-basis RH/VPD/QBOT source values cannot be reproduced")
    x=df.copy()
    x["es_water_hPa_at_tower_T"]=esw
    x["es_ice_hPa_at_tower_T"]=np.where(t<0,esi,np.nan)
    x["water_basis_vapour_pressure_hPa"]=vapour_hpa
    x["RH_over_ice_pct_diagnostic"]=np.where(t<0,rhi,np.nan)
    x["VPD_over_ice_hPa_diagnostic"]=np.where(t<0,vpi,np.nan)
    x["VPD_ice_minus_water_hPa_diagnostic"]=np.where(t<0,vpi-vpw,np.nan)
    x["ice_rh_above_100"]=np.where(t<0,rhi>100,False)
    x["ice_rh_above_105"]=np.where(t<0,rhi>105,False)
    x["ice_vpd_negative"]=np.where(t<0,vpi<0,False)
    x["humidity_review_route"]=[qc_route(a,b) for a,b in zip(t,rhi)]
    x["ice_saturation_science_HOLD"]=True
    x["US_Ho1_offset_HOLD_not_included"]=True
    x["approved_for_DATM"]=False
    return x

def ho1_source_bif_inventory():
    """Discovery only: no assumption that nearby BIF is a verified release BIF."""
    src11=ROOT/"stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
    m11=json.loads((src11/"manifest.json").read_text())
    m08=json.loads((Path(m11["source_stage08"])/"exact_input_manifest.json").read_text())
    source=[r for r in m08["sites"] if r["site"]=="US-Ho1"]
    if len(source)!=1:raise ValueError("US-Ho1 source inventory not unique")
    primary=Path(source[0]["primary"]).resolve(strict=True)
    if sha(primary)!=m11["input_hashes"].get(str(primary)):
        raise ValueError("Original US-Ho1 primary SHA256 differs")
    matches=sorted(primary.parent.glob("*_BIF_*.csv"))
    found=[]
    for p in matches:
        offsets=[]
        with p.open(encoding="utf-8-sig",newline="") as stream:
            for row in csv.DictReader(stream):
                if row.get("VARIABLE","").strip().upper()=="UTC_OFFSET":
                    offsets.append((row.get("SITE_ID","").strip(),row.get("DATAVALUE","").strip()))
        found.append({"candidate_file":str(p),"candidate_sha256":sha(p),"UTC_OFFSET_entries":offsets})
    return {"original_primary":str(primary),"primary_sha256":sha(primary),
        "original_release_adjacent_BIF_candidates":found,
        "status":"REQUIRES_OFFICIAL_RELEASE_BADM_BIF_UTC_OFFSET_VERIFICATION",
        "not_authorized_for_Ho1_ERA5_alignment":True}

def self_test():
    t=np.array([-30.,-10.,0.])
    assert (saturation_water(t[:2])>saturation_ice(t[:2])).all()
    assert qc_route(-30,106)=="REVIEW_ICE_RH_OVER105_PCT"
    assert qc_route(-10,102)=="REVIEW_ICE_RH_100_TO105_PCT"
    assert qc_route(-2,90)=="SUBZERO_NO_ICE_SUPERSAT_NUMERIC_FLAG"
    assert qc_route(2,110)=="ABOVE_ZERO_WATER_REFERENCE"
    print("STAGE59 SELF-TEST PASS | water/ice saturation separated; no clipping")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    g=parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--check",action="store_true")
    g.add_argument("--audit",action="store_true")
    args=parser.parse_args()
    if args.self_test:return self_test()
    raw,manifest=load()
    values=calculate(raw)
    ho1=ho1_source_bif_inventory()
    routes=dict(Counter(values.humidity_review_route))
    summary=[]
    for site in SITES:
        data=values.loc[values.site==site]
        if site=="US-Ho1":continue
        row={"site":site,"n_temperature_retained":len(data),
             "n_original_T_below0":int((data.TA_F<0).sum()),
             "ice_RH_above100":int(data.ice_rh_above_100.sum()),
             "ice_RH_above105":int(data.ice_rh_above_105.sum()),
             "ice_VPD_negative":int(data.ice_vpd_negative.sum()),
             "max_RH_ice_pct":float(data.RH_over_ice_pct_diagnostic.max()),
             "max_water_minus_ice_VPD_hPa":float(
                 (-data.VPD_ice_minus_water_hPa_diagnostic).max())}
        summary.append(row)
        print("SITE",row)
    print("STAGE59 SOURCE CHECK PASS | Stage58 3967 original TA retained + 917 Ho1 HOLD")
    print("PHASE_ROUTE_COUNTS",routes)
    print("HO1_RELEASE_BIF_INVENTORY",json.dumps(ho1,sort_keys=True))
    print("TOP 20 HIGHEST ICE RH (diagnostic only):")
    shown=values.loc[values.TA_F<0].nlargest(
        20,"RH_over_ice_pct_diagnostic")[[
        "site","local_key","TA_F","ERA5_RH_water_pct_selected",
        "RH_over_ice_pct_diagnostic","VPD_over_ice_hPa_diagnostic",
        "humidity_review_route"]]
    print(shown.round(4).to_string(index=False))
    print("ALL ORIGINAL HUMIDITY AND MODEL FORCING STILL HOLD")
    if args.check:
        print("STAGE59 CHECK PASS | no files written");return
    root=ROOT/"reports"
    dest=root/("stage59_water_ice_review_3967_"+
       datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    marker=dest/"INCOMPLETE_DO_NOT_USE"
    marker.write_text("Read-only science sensitivity; not model forcing.\n")
    output={RESULT:values,
            "four_site_water_ice_QC_summary.csv":pd.DataFrame(summary),
            "phase_route_counts.csv":pd.DataFrame([
                {"phase_route":k,"n":v} for k,v in sorted(routes.items())])}
    shas={}
    for name,data in output.items():
        out=dest/name
        data.to_csv(out,index=False)
        shas[name]=sha(out)
    (dest/"Ho1_original_release_BIF_inventory.json").write_text(
        json.dumps(ho1,sort_keys=True,indent=2)+"\n")
    shas["Ho1_original_release_BIF_inventory.json"]=sha(
        dest/"Ho1_original_release_BIF_inventory.json")
    if sha(S58/F58)!=manifest["report_sha256"][F58]:
        raise ValueError("Stage58 source changed during Stage59")
    (dest/"phase_science_manifest.json").write_text(json.dumps({
        "schema":"STAGE59_3967_WATER_ICE_DIAGNOSTIC_v1",
        "n_original_temperature_retained":3967,
        "n_Ho1_time_offset_HOLD":917,
        "stage58_report_sha256":sha(S58/F58),
        "stage58_manifest_sha256":sha(S58/"manual_temperature_decision_manifest.json"),
        "report_sha256":shas,
        "phase_routes":routes,
        "all_humidity_science_HOLD":True,
        "water_vpd_qbot_unchanged":True,
        "no_model_or_source_changes":True},sort_keys=True,indent=2)+"\n")
    marker.unlink()
    print("STAGE59 AUDIT PASS | 3967 water/ice RH diagnostics; Ho1 UTC gate retained")
    print("REPORT",dest)
    print("NO ORIGINAL EC, STAGE58, DATM, FORCING, CIME OR SLURM CHANGES")
if __name__=="__main__":
    main()

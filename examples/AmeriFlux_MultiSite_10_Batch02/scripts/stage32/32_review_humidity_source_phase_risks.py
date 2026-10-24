#!/usr/bin/env python3
"""Stage32 read-only source-aware humidity sensitivity and phase-risk gate.

Runs on the 4,884 Stage08-held Batch02 timestamps using pinned Stage19 and
Stage20 science outputs and the original unchanged FLUXNET tower sources.
Compares:
  A  ERA5 water-RH transferred to the *retained* site temperature.
  B  ERA5 dewpoint-derived vapour pressure transferred to site temperature.
  C  ERA5 water-RH and ERA5 T as a *paired* numerical reference (not forcing).
Temperature/source-QC, saturation over ice, excess VPD, timezone and source
provenance remain uncertainty gates. All records remain SCIENTIFIC HOLD.

No new ERA5 downloads; no writes, forcing, DATM, CIME or Slurm changes.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import numpy as np
import pandas as pd

SITE_N = {"US-EML":1327, "US-GLE":295, "US-Ho1":917,
          "US-ICh":169, "US-ICt":2176}
ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
HOME = Path.home()
DEFAULT11 = ROOT / "stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
DEFAULT19 = HOME / "AmeriFlux_Batch02_stage19_full_dewpoint_audit_20261023T015650Z_8505582f"
DEFAULT20 = HOME / "AmeriFlux_Batch02_stage20_physical_evidence_review_20261023T021238Z_d7a70a5f"
DEFAULT21 = HOME / "AmeriFlux_Batch02_stage21_postv5_candidate_decisions_20261023T022056Z_b754ce13"
CSV19 = "all_4884_ERA5_RH_VPD_QBOT_sensitivity.csv"
CSV20 = "all_4884_phase_transfer_QC_sensitivity.csv"

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest()

def water_es(t):
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        return 6.112*np.exp(17.67*t/(t+243.5))

def ice_es(t):
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        return 6.112*np.exp(22.46*t/(272.62+t))

def quant(x):
    v = pd.to_numeric(x, errors="coerce")
    return v.quantile([.05,.25,.50,.75,.95]).round(4).to_dict() if v.notna().any() else {}

def boolcol(s):
    v=s.astype(str).str.strip().str.lower()
    if not v.isin(["true","false","1","0"]).all():
        raise ValueError("Non-boolean phase flag values")
    return v.isin(["true","1"])

def read_and_verify(args):
    s11,s19,s20,s21 = [getattr(args,k) for k in
                         ("stage11_root","stage19_root","stage20_root","stage21_root")]
    for d in (s11,s19,s20):
        if not (d/"DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
            raise ValueError("Missing required scientific-HOLD marker: "+str(d))
    m11=json.loads((s11/"manifest.json").read_text())
    m19=json.loads((s19/"manifest.json").read_text())
    m20=json.loads((s20/"manifest.json").read_text())
    m21=json.loads((s21/"manifest.json").read_text())
    if (m19.get("n_target_rows"),m19.get("scientifically_approved_rows")) != (4884,0):
        raise ValueError("Stage19 target/science contract changed")
    if (m20.get("number_targets"),m20.get("number_approved")) != (4884,0):
        raise ValueError("Stage20 target/science contract changed")
    if Path(m20["stage19_root"]).resolve() != s19.resolve():
        raise ValueError("Stage20 belongs to a different Stage19")
    if sha256(s19/"manifest.json") != m20["stage19_manifest_sha256"]:
        raise ValueError("Stage19 manifest hash changed")
    if sha256(s20/CSV20) != m21["stage20_csv_sha256"]:
        raise ValueError("Stage20 report hash changed since Stage21")
    m08=json.loads((Path(m11["source_stage08"])/"exact_input_manifest.json").read_text())
    originals={r["site"]:Path(r["primary"]).resolve(strict=True)
               for r in m08["sites"] if r["site"] in SITE_N}
    if set(originals)!=set(SITE_N):raise ValueError("Missing source release")
    for site,path in originals.items():
        expected=m19["original_source_sha256"][site]
        if m11["input_hashes"].get(str(path))!=expected or sha256(path)!=expected:
            raise ValueError("Original source changed: "+site)
        print("SOURCE VERIFIED:",site,path.name,flush=True)
    a=pd.read_csv(s19/CSV19,parse_dates=["local"])
    b=pd.read_csv(s20/CSV20,parse_dates=["local"])
    for name,df in (("Stage19",a),("Stage20",b)):
        if len(df)!=4884 or df.duplicated(["site","local"]).any() or df.groupby("site").size().to_dict()!=SITE_N:
            raise ValueError(name+" row/site/timestamp mismatch")
    if set(zip(a.site,a.local))!=set(zip(b.site,b.local)):
        raise ValueError("Stage19 and Stage20 target timestamps differ")
    # Stage20 retains the official source QC and Stage19 source values.
    need={"site","local","TA_F_QC","retained_TA_C","retained_PA_kPa",
          "ERA5_T2M_C","ERA5_Td2M_C","ERA5_RH_water_pct",
          "sensitivity_VPD_hPa","Td_transfer_water_VPD_hPa",
          "ERA5_ice_RH_above100_subzero","RH_transfer_ice_VPD_subzero_hPa",
          "Td_transfer_ice_VPD_subzero_hPa"}
    if not need.issubset(b.columns):
        raise ValueError("Missing Stage20 scientific variables: "+str(need-set(b.columns)))
    if not {"retained_TA_C","TA_F_QC","ERA5_T2M_C","ERA5_RH_water_pct"}.issubset(a.columns):
        raise ValueError("Stage19 missing comparison variables")
    paired=a[["site","local","retained_TA_C","TA_F_QC","ERA5_T2M_C","ERA5_RH_water_pct"]].merge(
        b[["site","local","retained_TA_C","TA_F_QC","ERA5_T2M_C","ERA5_RH_water_pct"]],
        on=["site","local"],validate="one_to_one",suffixes=("_19","_20"))
    for c in ("retained_TA_C","TA_F_QC","ERA5_T2M_C","ERA5_RH_water_pct"):
        if not np.isclose(paired[c+"_19"],paired[c+"_20"],atol=1e-9,rtol=0,equal_nan=True).all():
            raise ValueError("Stage19/20 variable disagreement: "+c)
    return b

def science_table(data,site):
    x=data.loc[data.site.eq(site)].sort_values("local").copy()
    t=x.retained_TA_C.to_numpy(dtype=float)
    te=x.ERA5_T2M_C.to_numpy(dtype=float)
    td=x.ERA5_Td2M_C.to_numpy(dtype=float)
    rh=x.ERA5_RH_water_pct.to_numpy(dtype=float)
    vpd_rh=x.sensitivity_VPD_hPa.to_numpy(dtype=float)
    vpd_td=x.Td_transfer_water_VPD_hPa.to_numpy(dtype=float)
    sw=water_es(t)
    si=ice_es(t)
    paired_vpd=water_es(te)*(1-rh/100)
    rh_recalc=sw*(1-rh/100)
    td_recalc=sw-water_es(td)
    if not (np.isfinite(t).all() and np.isfinite(te).all() and
            np.isfinite(td).all() and np.isfinite(rh).all() and
            np.isfinite(vpd_rh).all() and np.isfinite(vpd_td).all()):
        raise ValueError(site+": expected finite sensitivity inputs")
    if not np.allclose(rh_recalc,vpd_rh,rtol=1e-8,atol=1e-7):
        raise ValueError(site+": RH-transfer reproducibility failed")
    if not np.allclose(td_recalc,vpd_td,rtol=1e-8,atol=1e-7):
        raise ValueError(site+": dewpoint-transfer reproducibility failed")
    qc=pd.to_numeric(x.TA_F_QC,errors="coerce")
    x["source_group"]=np.select([qc.eq(0),qc.eq(2)],
        ["QC0_MEASURED_T","QC2_ERA_ORIGIN_T"],default="OTHER_T_SOURCE")
    x["Td_minus_retained_T_C"]=td-t
    x["CDS_minus_retained_T_C"]=te-t
    x["RH_minus_Td_VPD_hPa"]=vpd_rh-vpd_td
    x["paired_CDS_VPD_hPa"]=paired_vpd
    x["Td_water_supersaturation"]=vpd_td < -0.005
    x["RH_transfer_water_valid"]=(vpd_rh>=-0.005)&(vpd_rh<=sw+0.005)
    x["paired_CDS_water_valid"]=(paired_vpd>=-0.005)&(paired_vpd<=water_es(te)+0.005)
    x["ice_caution"]=boolcol(x.ERA5_ice_RH_above100_subzero)
    ice_domain=(t<0)&(t>=-65)
    x["RH_transfer_ice_supersat"] = ice_domain & ((si-(sw-vpd_rh)) < -0.005)
    x["Td_transfer_ice_supersat"] = ice_domain & ((si-water_es(td)) < -0.005)
    # Cross-check saved Stage20 phase calculations to prevent silent formula drift.
    rhi=pd.to_numeric(x.RH_transfer_ice_VPD_subzero_hPa,errors="coerce")
    tdi=pd.to_numeric(x.Td_transfer_ice_VPD_subzero_hPa,errors="coerce")
    if not np.allclose(rhi[ice_domain],(si-(sw-vpd_rh))[ice_domain],rtol=1e-8,atol=1e-7):
        raise ValueError(site+": Stage20 RH ice saturation mismatch")
    if not np.allclose(tdi[ice_domain],(si-water_es(td))[ice_domain],rtol=1e-8,atol=1e-7):
        raise ValueError(site+": Stage20 Td ice saturation mismatch")
    # Mutually exclusive review routing priorities, NOT acceptance classifications.
    clock=np.full(len(x),site=="US-Ho1")
    x["review_route"]=np.select([
        clock,
        x.Td_water_supersaturation,
        x.ice_caution|x.RH_transfer_ice_supersat|x.Td_transfer_ice_supersat,
        np.abs(te-t)>5
    ],[
        "P0_HO1_CLOCK_HOLD",
        "P1_TD_WATER_SUPERSAT_HOLD",
        "P2_ICE_PHASE_HOLD",
        "P3_TEMPERATURE_REPRESENTATIVENESS_HOLD"
    ],default="P4_UNVALIDATED_HUMIDITY_HOLD")
    return x

def output(x,site):
    print("\n"+"="*112)
    print("SITE:",site,"| TARGETS:",len(x),"| ALL SCIENTIFIC HOLD")
    print("="*112)
    print("A RH-at-retained-T water-valid:",int(x.RH_transfer_water_valid.sum()))
    print("B Td-at-retained-T water-supersaturated:",int(x.Td_water_supersaturation.sum()))
    print("C paired CDS-T/RH water-valid:",int(x.paired_CDS_water_valid.sum()),
          "(NUMERICAL REFERENCE ONLY)")
    print("RH-transfer ice supersat at site T:",int(x.RH_transfer_ice_supersat.sum()))
    print("Td-transfer ice supersat at site T:",int(x.Td_transfer_ice_supersat.sum()))
    print("ERA5 ice-RH caution:",int(x.ice_caution.sum()))
    print("Mutually-exclusive review routes:")
    print(x.review_route.value_counts().to_string())
    print("Source-stratified comparison:")
    rows=[]
    for group,g in x.groupby("source_group"):
        rows.append({
            "source_group":group,
            "n":len(g),
            "RH_transfer_water_valid":int(g.RH_transfer_water_valid.sum()),
            "Td_water_supersat":int(g.Td_water_supersaturation.sum()),
            "RH_ice_supersat":int(g.RH_transfer_ice_supersat.sum()),
            "Td_ice_supersat":int(g.Td_transfer_ice_supersat.sum()),
            "ERA5_ice_caution":int(g.ice_caution.sum()),
            "abs_CDS_minus_site_T_gt5C":int(g.CDS_minus_retained_T_C.abs().gt(5).sum()),
            "median_abs_RH_minus_Td_VPD_hPa":round(g.RH_minus_Td_VPD_hPa.abs().median(),5),
            "median_CDS_minus_site_T_C":round(g.CDS_minus_retained_T_C.median(),3),
        })
    print(pd.DataFrame(rows).to_string(index=False))
    if x.Td_water_supersaturation.any():
        neg=x.loc[x.Td_water_supersaturation].copy()
        print("\nNegative Td-transfer VPD — year distribution:")
        print(neg.groupby(neg.local.dt.year).size().to_string())
        print("\nTd minus retained T (C), quantiles:")
        print(quant(neg.Td_minus_retained_T_C))
        cols=["local","TA_F_QC","retained_TA_C","ERA5_T2M_C","ERA5_Td2M_C",
              "Td_minus_retained_T_C","Td_transfer_water_VPD_hPa",
              "ERA5_RH_water_pct","ice_caution"]
        print("\nWorst 8 water-saturation conflicts:")
        print(neg.nsmallest(8,"Td_transfer_water_VPD_hPa")[cols].round(4).to_string(index=False))
    print("\nAbsolute temperature difference quantiles (CDS T minus retained site T):")
    print(quant(x.CDS_minus_retained_T_C.abs()))
    if site=="US-Ho1":
        print("CLOCK HOLD: provisional local-to-UTC offset; do NOT approve a candidate")
    return rows

def main():
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--audit",action="store_true")
    p.add_argument("--stage11-root",type=Path,default=DEFAULT11)
    p.add_argument("--stage19-root",type=Path,default=DEFAULT19)
    p.add_argument("--stage20-root",type=Path,default=DEFAULT20)
    p.add_argument("--stage21-root",type=Path,default=DEFAULT21)
    p.add_argument("--site",choices=list(SITE_N),help="Restrict reporting only; still verifies 5 source releases")
    args=p.parse_args()
    b=read_and_verify(args)
    print("STAGE32 PREFLIGHT: 4,884/4,884 pinned Stage19–21 records, five original SHA256 verified")
    if args.check:
        print("CHECK ONLY; zero files written / zero approved forcing")
        return
    all_rows=[]
    for site in SITE_N:
        x=science_table(b,site)
        if args.site is None or args.site==site:
            all_rows.extend(output(x,site))
    if args.site is None:
        full=pd.DataFrame(all_rows)
        if int(full["n"].sum())!=4884:
            raise ValueError("Cohort summaries fail to reconcile 4884 records")
        print("\n"+"="*112)
        print("STAGE32 FIVE-SITE COHORT SUMMARY")
        print("="*112)
        print(full.to_string(index=False))
    print("\nSCIENTIFIC STATUS: HOLD / 0 replacements approved")
    print("RH water validity is partly a mathematical construction, not independent tower validation.")
    print("No automatic dewpoint substitution, RH floor, or edit of QC0 observations.")
    print("US-Ho1 local UTC offset and physical altitude/representativeness remain unresolved.")
    print("NO FILES WRITTEN / NO FORCING, DATM, CIME OR SLURM CHANGES")

if __name__=="__main__":
    main()

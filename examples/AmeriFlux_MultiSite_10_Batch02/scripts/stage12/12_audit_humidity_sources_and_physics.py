#!/usr/bin/env python3
"""Batch02 Stage12: READ-ONLY source/provenance audit for winter humidity.

Verifies the exact Stage11 proposals against pinned files. At each of the
4,884 unresolved Stage08 timestamps, independently recomputes water- and
ice-saturation feasibility at source ERA temperature (and retained tower
temperature). Inventory candidate dewpoint/specific-humidity columns by
HEADER ONLY; existence is not evidence of independent or reliable coverage.

NO repairs, forcing overlays, DATM, CIME, queue changes or overwrites.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from uuid import uuid4

import numpy as np
import pandas as pd

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02")
DEFAULT_STAGE11 = ROOT / "stage11_cold_humidity_review_20261022T020911Z_2ad6f27b"
EXPECTED = {"US-EML":1327,"US-GLE":295,"US-Ho1":917,"US-ICh":169,"US-ICt":2176}
MOISTURE = re.compile(r"(^RH($|_)|DEW|TDEW|DEWP|D2M|(^|_)TD($|_)|HUMID|HUSS|SPECIFIC[_ ]?HUM|QBOT|(^|_)Q_ERA$)", re.I)

def csv_header_only(path):
    """Inventory header only, without asking pandas to tokenize the file body.

    Several AmeriFlux auxiliary CSVs contain legacy cp1252/Latin-1 bytes,
    including 0xb5 (micro sign), which can occur inside pandas' read buffer
    even for read_csv(nrows=0). Replacing undecodable characters is only
    permitted here for a non-scientific column-name inventory; actual numeric
    source parsing and hash checks remain strict and unmodified.
    """
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as stream:
        try:
            return next(csv.reader(stream))
        except StopIteration:
            return []


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for piece in iter(lambda: f.read(1048576), b""):
            h.update(piece)
    return h.hexdigest()

def es_water(t):
    return 6.112 * np.exp(17.67 * t / (t + 243.5))

def es_ice(t):
    return 6.112 * np.exp(22.46 * t / (272.62 + t))

def timeparse(x):
    s=x.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    return pd.to_datetime(s, format="%Y%m%d%H%M", errors="raise")

def run(args):
    old = args.stage11_root.expanduser().resolve()
    if not (old / "DO_NOT_USE_FOR_DATM_OR_SPINUP").is_file():
        raise ValueError("Expected Stage11 report with no-DATM marker")
    manifest_p=old / "manifest.json"
    proposal_p=old / "cold_humidity_repair_proposals.csv"
    summary_p=old / "site_summary.csv"
    manifest=json.loads(manifest_p.read_text())
    if manifest["n_target_rows"] != 4884 or manifest["scientific_status"] != "HOLD_INDEPENDENT_VALIDATION_REQUIRED":
        raise ValueError("Unexpected Stage11 provenance/scope")
    pins={str(p):digest(p) for p in (manifest_p,proposal_p,summary_p)}
    source8=Path(manifest["source_stage08"]).resolve()
    if not (source8 / "INCOMPLETE_SENSITIVITY_DO_NOT_USE_FOR_DATM").exists():
        raise ValueError("Original Stage08 marker missing")
    eight=json.loads((source8 / "exact_input_manifest.json").read_text())
    if eight["algorithm"] != "STAGE07_BLOCKERS_SAME_RELEASE_RAW_RH_SENSITIVITY":
        raise ValueError("Not an original Stage08 output")
    siteinfo={x["site"]:x for x in eight["sites"]}
    proposals=pd.read_csv(proposal_p,dtype={"site":str,"time":str})
    if len(proposals)!=4884 or set(proposals.site)!=set(EXPECTED):
        raise ValueError("Unexpected Stage11 proposals")
    if proposals.duplicated(["site","time"]).any():
        raise ValueError("Repeated proposal timestamp")
    decisions=proposals.decision.value_counts().to_dict()
    if decisions.get("PROVISIONAL_ANALOGUE_REVIEW_REQUIRED",0)!=4870 or decisions.get("HOLD_NO_SUPPORTED_ANALOGUE",0)!=14:
        raise ValueError("Unexpected Stage11 decision totals")
    source_inventory=[]
    science=[]
    sums=[]
    for site, count in EXPECTED.items():
        one=proposals.loc[proposals.site.eq(site)].copy()
        if len(one)!=count: raise ValueError("Site count differs: "+site)
        item=siteinfo[site]
        primary,era=Path(item["primary"]).resolve(),Path(item["era"]).resolve()
        for file in (primary,era):
            pinned=manifest["input_hashes"].get(str(file))
            if not pinned or digest(file)!=pinned:
                raise ValueError("Source file is not pinned/unchanged: "+str(file))
            pins[str(file)]=pinned
        # Preserve native release provenance: do not search another site's files.
        for f in sorted(primary.parent.glob("*.csv")):
            columns=csv_header_only(f)
            hits=[c for c in columns if MOISTURE.search(str(c))]
            if hits:
                source_inventory.append(dict(
                    site=site,filename=str(f),source_class=(
                        "PRIMARY" if f==primary else "ERA5_COMPANION" if f==era else "OTHER_SAME_RELEASE"),
                    candidate_humidity_columns="|".join(hits),
                    n_columns=len(columns),
                    caveat="Presence of a field is not validation or proof of independent provenance"))
        e=pd.read_csv(era,usecols=["TIMESTAMP_START","TA_ERA","VPD_ERA"],dtype={"TIMESTAMP_START":str})
        e["time"]=timeparse(e.TIMESTAMP_START)
        if e.time.duplicated().any(): raise ValueError("Duplicate ERA timestamps: "+site)
        e=e.set_index("time")
        tt=pd.to_datetime(one.time)
        if not tt.isin(e.index).all(): raise ValueError("ERA timestamps missing: "+site)
        pair=e.loc[tt,["TA_ERA","VPD_ERA"]].reset_index(drop=True)
        ta=pd.to_numeric(pair.TA_ERA,errors="coerce").to_numpy(float)
        v=pd.to_numeric(pair.VPD_ERA,errors="coerce").to_numpy(float)
        ta[ta<=-9990]=np.nan
        v[v<=-9990]=np.nan
        tower=pd.to_numeric(one.retained_TA_C,errors="coerce").to_numpy(float)
        vprior=pd.to_numeric(one.prior_VPD_hPa,errors="coerce").to_numpy(float)
        trial=pd.to_numeric(one.proposed_VPD_hPa,errors="coerce").to_numpy(float)
        with np.errstate(all="ignore"):
            esw=es_water(ta); esi=es_ice(ta)
            rhw=100*(1-v/esw)
            rhi=100*(1-v/esi)
            tower_esw=es_water(tower)
            tower_esi=es_ice(tower)
            tower_rhw=100*(1-vprior/tower_esw)
            tower_rhi=100*(1-vprior/tower_esi)
            change_fraction=np.abs(trial-vprior)/tower_esw
        saved=pd.to_numeric(one.ERA_RH_impossible_pct,errors="coerce").to_numpy(float)
        if not np.isclose(saved,rhw,atol=1e-7,rtol=1e-8,equal_nan=True).all():
            raise ValueError("Stage11 ERA RH not reproduced at same native timestamp: "+site)
        physics=one[["site","time","decision","source_csv_row","retained_TA_C",
                     "prior_VPD_hPa","proposed_VPD_hPa","donor_count"]].copy()
        physics["TA_ERA_C"]=ta
        physics["VPD_ERA_hPa"]=v
        physics["ERA_RH_water_pct"]=rhw
        physics["ERA_RH_ice_pct"]=np.where(ta<0,rhi,np.nan)
        physics["retained_TA_RH_water_from_prior_VPD_pct"]=tower_rhw
        physics["retained_TA_RH_ice_from_prior_VPD_pct"]=np.where(tower<0,tower_rhi,np.nan)
        physics["abs_VPD_change_over_es_water"]=change_fraction
        physics["review_large_change"]=change_fraction>.5
        physics["ERA_water_impossible"]=~(np.isfinite(rhw)&(rhw>0)&(rhw<=100.05))
        physics["ERA_ice_impossible_below_zero"]=np.where(ta<0,~(np.isfinite(rhi)&(rhi>0)&(rhi<=100.05)),False)
        science.append(physics)
        provisional=one.decision.eq("PROVISIONAL_ANALOGUE_REVIEW_REQUIRED")
        held=~provisional
        sums.append(dict(
            site=site,total=len(one),provisional=int(provisional.sum()),held=int(held.sum()),
            large_change=int(np.count_nonzero((change_fraction>.5)&provisional.to_numpy())),
            ERA_water_impossible=int(physics.ERA_water_impossible.sum()),
            ERA_ice_impossible_subzero=int(physics.ERA_ice_impossible_below_zero.sum()),
            companion_subzero=int(np.count_nonzero(ta<0)),
            source_ERA_min_RH_water=float(np.nanmin(rhw))))
        print(f"{site}: {len(one)} targets, {int(held.sum())} held, "
              f"{sums[-1]['large_change']} high-change proposals; "
              f"{sums[-1]['ERA_ice_impossible_subzero']} ice-infeasible ERA cases",flush=True)
    science=pd.concat(science,ignore_index=True)
    totals=sum(s["large_change"] for s in sums)
    if totals!=1851: raise ValueError("Unexpected VPD-change screen total; inspect source/algorithm")
    changed=[p for p,d in pins.items() if digest(Path(p))!=d]
    if changed:raise ValueError("Inputs modified during audit: "+str(changed))
    print("STAGE12 SUMMARY: 4884 records, 4870 provisional, 14 holds, "
          "1851 high-change flags; source hashes unchanged")
    for s in sums: print("SITE:",s,flush=True)
    inv=pd.DataFrame(source_inventory)
    print("\nSAME-RELEASE POTENTIAL HUMIDITY COLUMNS (NOT VALIDATED):")
    if len(inv):
        print(inv[["site","source_class","candidate_humidity_columns"]].to_string(index=False))
    else:
        print("NONE FOUND")
    print("\nCAUTION: ICE e_sat IS LOWER THAN WATER BELOW FREEZING. "
          "An impossible water-RH pair does not become physically valid merely by switching to ice.")
    if args.check:
        print("CHECK ONLY, no reports created")
        return 0
    out=args.output_root.expanduser().resolve() if args.output_root else (
        Path.home()/("AmeriFlux_Batch02_stage12_"+
                     datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
                     "_"+uuid4().hex[:8]))
    if out.exists() or out==old or out in old.parents or old in out.parents or out==source8 or out in source8.parents or source8 in out.parents:
        raise ValueError("Unsafe/existing output location")
    out.mkdir(parents=True,exist_ok=False)
    science.to_csv(out/"all_4884_source_physics.csv",index=False)
    science.loc[(science.review_large_change)|(science.decision=="HOLD_NO_SUPPORTED_ANALOGUE")].to_csv(
        out/"high_change_and_unresolved.csv",index=False)
    inv.to_csv(out/"available_humidity_column_inventory.csv",index=False)
    pd.DataFrame(sums).to_csv(out/"site_summary.csv",index=False)
    (out/"manifest.json").write_text(json.dumps(dict(
        source_stage11=str(old),inputs_sha256=pins,software_sha256=digest(Path(__file__)),
        scientific_status="SOURCE_DIAGNOSTIC_ONLY_NO_FORCING_APPROVAL",
        required_next_evidence="Independent ERA5 dewpoint/specific humidity or verified tower humidity with time/height/phase QC",
        never_modified=["Stage07","Stage08","Stage11","raw meteorology","DATM","CIME","Slurm"]
    ),indent=2)+"\n")
    print("STAGE12 REPORT:",out)
    print("No DATM or spin-up generated.")
    return 0

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage11-root",type=Path,default=DEFAULT_STAGE11)
    parser.add_argument("--output-root",type=Path)
    parser.add_argument("--check",action="store_true")
    raise SystemExit(run(parser.parse_args()))

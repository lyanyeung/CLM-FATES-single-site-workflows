#!/usr/bin/env python3
"""Read-only Stage05: summarize existing AmeriFlux Stage04 reports."""
import csv
from pathlib import Path
from collections import Counter
root=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports")
def report(pattern,file):
    choices=sorted(p for p in root.glob(pattern) if (p/file).is_file())
    if not choices: raise SystemExit("Missing "+pattern+"/"+file)
    return choices[-1]/file
def rows(path):
    with path.open(newline="") as f:return list(csv.DictReader(f))
def n(row,key):
    try:return float(row.get(key) or 0)
    except ValueError:return 0
s=rows(report("stage04a_surface_*","surface_summary.csv"))
m=rows(report("stage04b_met_*","annual_source_coverage_and_QC.csv"))
assert len(s)==10 and len(m)==426,(len(s),len(m))
vars=("TA","VPD","PA","SW_IN","LW_IN","WS","P")
totals=Counter()
for surface in s:
    site=surface["site"]
    print("\n==",site,"IGBP",surface["igbp"],"==")
    print("SURFACE NATVEG",surface.get("PCT_NATVEG"),"CROP",surface.get("PCT_CROP"),"TREE",surface.get("forest_natural_pct"),"GRASS",surface.get("grass_natural_pct"))
    for source in ("FLUXMET_HH","ERA5_HH"):
        yearly=sorted((r for r in m if r["site"]==site and r["source"]==source),key=lambda x:int(x["year"]))
        flagged=[r for r in yearly if r["status"]=="REVIEW"]
        totals[source]+=len(flagged)
        print(source,":",len(flagged),"/",len(yearly),"REVIEW years")
        for r in flagged:
            bad={v:int(n(r,v+"_range_bad")) for v in vars if n(r,v+"_range_bad")>0}
            low={v:round(n(r,v+"_valid_pct"),1) for v in vars if n(r,v+"_valid_pct")<95}
            print("  YEAR",r["year"],"MIN_COVERAGE",r.get("min_variable_coverage_pct"),"MISSING_TIME",r.get("missing_timestamps"),"INVALID_RH",r.get("humidity_invalid"),"RANGE_BAD",bad,"LOW_VARS",low)
        if source=="ERA5_HH" and yearly:
            print("ERA OUTSIDE RELEASE (informational):",yearly[0].get("outside_release_records"))
print("\nSUMMARY:",sum(totals.values()),"/",len(m),"REVIEW; FLUXMET",totals["FLUXMET_HH"],"ERA5",totals["ERA5_HH"])
print("No data edited. Review physical source events before changing forcing or surfaces.")

from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")

TARGETS = {
    "DE-Hzd": ["PA_F", "P_F"],
    "BE-Vie": ["PA_F", "LW_IN_F"],
    "FR-Hes": ["LW_IN_F"],
    "IT-Ren": ["P_F", "LW_IN_F"],
    "CZ-BK1": ["PA_F"],
    "CH-Dav": ["LW_IN_F"],
}

results = []

for site, variables in TARGETS.items():
    files = list((ROOT / site / "forcing/raw").rglob("*FLUXMET_HH*.csv"))
    if len(files) != 1:
        raise RuntimeError(f"{site}: FLUXMET file ambiguous")

    cols = ["TIMESTAMP_START"]
    for v in variables:
        cols.extend([v, v + "_QC"])

    d = pd.read_csv(
        files[0],
        usecols=cols,
        dtype={"TIMESTAMP_START": str},
        low_memory=False
    )

    t = d.TIMESTAMP_START.str.replace(r"\.0$", "", regex=True)
    d["year"] = pd.to_datetime(t, format="%Y%m%d%H%M").dt.year

    d = d[d.year <= 2025]

    for year, g in d.groupby("year"):
        for var in variables:
            x = pd.to_numeric(g[var], errors="coerce")
            qc = pd.to_numeric(g[var + "_QC"], errors="coerce")
            valid = np.isfinite(x) & (x > -9990)
            n = int(valid.sum())

            era_pct = 100 * ((qc == 2) & valid).sum() / n if n else np.nan
            measured_pct = 100 * ((qc == 0) & valid).sum() / n if n else np.nan

            results.append({
                "site": site,
                "year": int(year),
                "variable": var,
                "ERA_pct": round(era_pct, 2),
                "measured_pct": round(measured_pct, 2),
                "annual_precip_mm": (
                    round(float(x[valid].sum()), 2)
                    if var == "P_F" else np.nan
                )
            })

out = Path.home() / "eight_site_annual_era_usage.csv"
df = pd.DataFrame(results)
df.to_csv(out, index=False)

print("\nERA percentage ranges by site and variable:")
print(
    df.groupby(["site", "variable"])
      .ERA_pct.agg(["min", "max", "mean"])
      .round(2)
      .to_string()
)

print("\nDE-Hzd annual precipitation (mm/year):")
print(
    df[(df.site == "DE-Hzd") & (df.variable == "P_F")]
    [["year", "ERA_pct", "annual_precip_mm"]]
    .to_string(index=False)
)

print("\nSaved:", out)

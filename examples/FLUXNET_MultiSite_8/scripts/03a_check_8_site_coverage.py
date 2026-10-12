from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE")

SITES = {
    "CZ-BK1": (2004, 2025),
    "IT-Ren": (1999, 2025),
    "FR-Hes": (1997, 2025),
    "FR-FBn": (2008, 2024),
    "DE-Hzd": (2010, 2025),
    "CH-Dav": (1997, 2025),
    "BE-Vie": (1996, 2025),
    "IT-Lav": (2003, 2020),
}

VARS = [
    "TA_F", "VPD_F", "PA_F", "SW_IN_F",
    "LW_IN_F", "WS_F", "P_F"
]

rows = []
failures = []

for site, (first, last) in SITES.items():
    print(f"\n========== {site} ==========", flush=True)

    try:
        root = ROOT / site / "forcing/raw"
        matches = list(root.rglob("*FLUXMET_HH*.csv"))

        if len(matches) != 1:
            raise RuntimeError(
                f"Expected one FLUXMET_HH file, got {len(matches)}"
            )

        path = matches[0]
        header = set(pd.read_csv(path, nrows=0).columns)
        required = ["TIMESTAMP_START"] + VARS
        missing = [c for c in required if c not in header]

        if missing:
            raise RuntimeError(f"Missing columns: {missing}")

        qc_cols = [
            f"{v}_QC" for v in VARS
            if f"{v}_QC" in header
        ]

        df = pd.read_csv(
            path,
            usecols=required + qc_cols,
            dtype={"TIMESTAMP_START": str},
            low_memory=False
        )

        stamp = df["TIMESTAMP_START"].str.strip()
        stamp = stamp.str.replace(r"\.0$", "", regex=True)

        df["time"] = pd.to_datetime(
            stamp, format="%Y%m%d%H%M", errors="coerce"
        )

        if df.time.isna().any():
            raise RuntimeError("Unparseable timestamps detected")

        df = df[df.time.dt.year.between(first, last)].copy()
        df = df[
            ~((df.time.dt.month == 2) & (df.time.dt.day == 29))
        ].copy()

        duplicates = int(df.time.duplicated().sum())

        for v in VARS:
            x = pd.to_numeric(df[v], errors="coerce")
            df[v] = x.where(np.isfinite(x) & (x > -9990))

        flagged = []

        for year in range(first, last + 1):
            part = df[df.time.dt.year == year]
            n = part.time.nunique()

            fractions = {
                v: 100 * part[v].notna().sum() / 17520
                for v in VARS
            }

            min_var = min(fractions, key=fractions.get)
            min_pct = fractions[min_var]

            issues = []
            if n != 17520:
                issues.append(f"timestamps={n}/17520")
            if min_pct < 90:
                issues.append(f"{min_var}={min_pct:.1f}%")
            if duplicates:
                issues.append(f"duplicate timestamps={duplicates}")

            status = "REVIEW" if issues else "OK_CANDIDATE"

            rows.append({
                "site": site,
                "year": year,
                "timestamps": n,
                "minimum_F_variable": min_var,
                "minimum_F_pct": round(min_pct, 2),
                "status": status,
                **{
                    v + "_pct": round(fractions[v], 2)
                    for v in VARS
                }
            })

            if issues:
                flagged.append((year, ", ".join(issues)))

        print(f"Years: {first}-{last}")
        print(f"Years requiring review: {len(flagged)}")

        for year, issue in flagged:
            print(f"  {year}: {issue}")

        if not flagged:
            print("All years passed preliminary coverage screening")

    except Exception as exc:
        failures.append((site, str(exc)))
        print(f"ERROR: {exc}", flush=True)

out = Path.home() / "eight_site_yearly_coverage.csv"
pd.DataFrame(rows).to_csv(out, index=False)

print("\n=====================================")
print("ANNUAL COVERAGE AUDIT COMPLETED")
print("Report:", out)
print("Site failures:", failures if failures else "None")

if failures:
    raise SystemExit(1)

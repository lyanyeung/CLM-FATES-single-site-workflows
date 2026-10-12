from pathlib import Path
import pandas as pd
import numpy as np

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

results = []

for site, (start, end) in SITES.items():
    root = ROOT / site / "forcing"
    files = list((root / "raw").rglob("*FLUXMET_HH*.csv"))

    if len(files) != 1:
        raise RuntimeError(f"{site}: expected one FLUXMET_HH")

    cols = ["TIMESTAMP_START"] + VARS + [v + "_QC" for v in VARS]
    header = set(pd.read_csv(files[0], nrows=0).columns)
    usecols = [c for c in cols if c in header]

    df = pd.read_csv(
        files[0],
        usecols=usecols,
        dtype={"TIMESTAMP_START": str},
        low_memory=False
    )

    stamp = df.TIMESTAMP_START.str.replace(r"\.0$", "", regex=True)
    t = pd.to_datetime(stamp, format="%Y%m%d%H%M")

    keep = (
        t.dt.year.between(start, end)
        & ~((t.dt.month == 2) & (t.dt.day == 29))
    )
    df = df.loc[keep].copy()

    events = pd.read_csv(
        root / "qc_v5" / f"{site}_replacement_events.csv"
    )
    reasons = events["reason"].fillna("").astype(str)

    direct_era = int(reasons.str.contains(
        "remaining_gap_filled_ERA", regex=False
    ).sum())

    rh_candidate = int(reasons.str.contains(
        "near_zero_vapor_pressure_strong_ERA_wet_candidate",
        regex=False
    ).sum())

    qc0_changes = int(
        (pd.to_numeric(events["official_qc"], errors="coerce") == 0).sum()
    )

    print(f"\n========== {site} ==========")
    print("New direct ERA gap fills:", direct_era)
    print("New low-RH ERA reconstructions:", rh_candidate)
    print("Modified official QC=0:", qc0_changes)
    print(f"{'Variable':12} {'Measured':>10} {'Gapfilled':>10} {'ERA':>10} {'ERA %':>9}")

    for v in VARS:
        value = pd.to_numeric(df[v], errors="coerce")
        valid = np.isfinite(value) & (value > -9990)

        qcname = v + "_QC"
        if qcname in df:
            qc = pd.to_numeric(df[qcname], errors="coerce")
        else:
            qc = pd.Series(np.nan, index=df.index)

        measured = int((valid & (qc == 0)).sum())
        gapfilled = int((valid & (qc == 1)).sum())
        era = int((valid & (qc == 2)).sum())
        total = int(valid.sum())

        pct = 100 * era / total if total else np.nan

        print(
            f"{v:12} {measured:10d} {gapfilled:10d} "
            f"{era:10d} {pct:8.2f}%"
        )

        results.append({
            "site": site,
            "variable": v,
            "valid_F": total,
            "official_measured": measured,
            "official_gapfilled": gapfilled,
            "official_ERA": era,
            "official_ERA_pct": pct,
            "new_site_ERA_gap_fills": direct_era,
            "new_site_low_RH_reconstructions": rh_candidate
        })

out = Path.home() / "eight_site_era_provenance_audit.csv"
pd.DataFrame(results).to_csv(out, index=False)

print("\nSaved:", out)

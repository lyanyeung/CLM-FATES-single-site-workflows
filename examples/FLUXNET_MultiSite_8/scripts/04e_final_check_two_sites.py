from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(
    "/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"
)

EVENTS = {
    "CZ-BK1": ("2013-04-22 15:00", 2004, 2025),
    "FR-Hes": ("2022-07-03 17:00", 1997, 2025),
}

def read_time(df):
    text = df["TIMESTAMP_START"].astype(str).str.strip()
    text = text.str.replace(r"\.0$", "", regex=True)
    df["time"] = pd.to_datetime(text, format="%Y%m%d%H%M")
    return df

def rh(t, v):
    es = 6.112 * np.exp(17.67 * t / (t + 243.5))
    return 100 * (1 - v / es)

outputs = []

for site, (stamp, first, last) in EVENTS.items():
    base = ROOT / site / "forcing"
    raw = base / "raw"

    flux_files = list(raw.rglob("*FLUXMET_HH*.csv"))
    era_files = list(raw.rglob("*ERA5_HH*.csv"))

    if len(flux_files) != 1 or len(era_files) != 1:
        raise RuntimeError(f"{site}: raw files ambiguous")

    cols = [
        "TIMESTAMP_START",
        "TA_F", "TA_F_QC",
        "VPD_F", "VPD_F_QC",
        "TA_ERA", "VPD_ERA"
    ]

    header = set(pd.read_csv(flux_files[0], nrows=0).columns)

    d = pd.read_csv(
        flux_files[0],
        usecols=[c for c in cols if c in header],
        dtype={"TIMESTAMP_START": str},
        low_memory=False
    )
    d = read_time(d)

    target = pd.Timestamp(stamp)
    begin = target - pd.Timedelta(hours=2)
    end = target + pd.Timedelta(hours=2)

    d = d[d.time.between(begin, end)].copy()

    missing = [
        c for c in ("TA_ERA", "VPD_ERA")
        if c not in d.columns
    ]

    if missing:
        e = pd.read_csv(
            era_files[0],
            usecols=["TIMESTAMP_START"] + missing,
            dtype={"TIMESTAMP_START": str},
            low_memory=False
        )
        e = read_time(e)
        e = e[e.time.between(begin, end)]

        d = d.merge(
            e[["time"] + missing],
            on="time", how="left",
            validate="one_to_one"
        )

    forcing_file = (
        base / "processed_v5"
        / f"{site}_CLM_forcing_{first}_{last}.csv"
    )

    f = pd.read_csv(
        forcing_file,
        usecols=["time", "TA_USE", "VPD_USE"],
        low_memory=False
    )
    f["time"] = pd.to_datetime(f["time"])
    f = f[f.time.between(begin, end)]

    d = d.merge(
        f, on="time", how="left",
        validate="one_to_one"
    )

    for c in [
        "TA_F", "TA_F_QC", "TA_ERA",
        "VPD_F", "VPD_F_QC", "VPD_ERA",
        "TA_USE", "VPD_USE"
    ]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
        d.loc[d[c] <= -9990, c] = np.nan

    d["TA_minus_ERA"] = d.TA_F - d.TA_ERA
    d["RH_original"] = rh(d.TA_F, d.VPD_F)
    d["RH_v5"] = rh(d.TA_USE, d.VPD_USE)
    d["RH_ERA"] = rh(d.TA_ERA, d.VPD_ERA)
    d["site"] = site

    columns = [
        "time", "TA_F", "TA_F_QC",
        "TA_ERA", "TA_minus_ERA",
        "TA_USE", "VPD_F", "VPD_F_QC",
        "VPD_USE", "RH_original",
        "RH_v5", "RH_ERA"
    ]

    print("\n" + "=" * 85)
    print(site, stamp)
    print("=" * 85)
    print(d[columns].round(3).to_string(index=False))

    event = d[d.time == target]

    if len(event) != 1:
        raise RuntimeError(f"{site}: target timestamp not unique")

    if not (
        np.isfinite(event.RH_v5.iloc[0])
        and 0 < event.RH_v5.iloc[0] <= 100.05
    ):
        raise RuntimeError(
            f"{site}: QC v5 humidity still physically invalid"
        )

    print("QC v5 humidity: physically valid")
    print("Temperature provenance: manual interpretation required")

    outputs.append(d)

out = Path.home() / "eight_site_final_two_site_check.csv"

pd.concat(outputs).to_csv(out, index=False)

print("\nSaved:", out)

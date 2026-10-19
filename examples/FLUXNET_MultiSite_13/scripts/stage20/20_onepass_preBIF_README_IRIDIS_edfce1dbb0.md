# FLUXNET 13-site Stage 20 — one-pass pre-BIF meteorology trial

**Scope:** DE-Lnf, DE-Obe, ES-Agu, ES-LJu, IT-Col, DE-Gri, DE-RuR, FI-Hyy, FI-Let, FR-Pue, GF-Guy, IT-MBo, IT-Tor.

## Research status

This reproducible workflow uses the user's completed Stage12, Stage15, Stage18 and Stage19 data. It creates **non-overwriting candidate trials**, not a declaration that 13 meteorological sites are scientifically approved. ERA5 and ERA5-Land are related reanalysis products, **not independent observations**. The script will not invent a source for unsupported precipitation or automatically alter valid QC=0 measurements. It explicitly leaves a closed BIF gate when scientific issues remain.

Stage 19's 13 full-block eligible screenings are only *numerically* tested. Acceptance requires all: (i) original ICOS paired TA and VPD QC=1 at each candidate record; (ii) prior Stage18 dual-model T+RH support; (iii) candidate ERA5 values and original forcing match Stage19 proposal; (iv) max candidate boundary |ΔTA| ≤4°C and less than the original max; (v) max candidate boundary |ΔVPD|≤12 hPa; (vi) RH/QBOT physical consistency. These are **heuristic conservatism gates**, not universal climate thresholds. No partial or inconsistent block is modified.

## WSL upload

Download `20_onepass_13site_meteorology_preBIF.py` into the Windows Downloads directory, then run:

```bash
SCRIPT=$(find /mnt/c/Users -maxdepth 4 -type f -name '20_onepass_13site_meteorology_preBIF.py' -print -quit)
test -n "$SCRIPT" || { echo 'Script not found in Windows Downloads or user folders'; exit 1; }
scp "$SCRIPT" ly3n24@iridis6.soton.ac.uk:~/
```

## IRIDIS run (single invocation, includes source checks)

```bash
conda activate clm_fates_env
set -o pipefail
python ~/20_onepass_13site_meteorology_preBIF.py --mode run 2>&1 | tee ~/FLUXNET_13_stage20_onepass.log
```

Optional *read-only* preview:

```bash
python ~/20_onepass_13site_meteorology_preBIF.py --mode check
```

A run refuses to overwrite an existing output directory. If a run fails midway, **do not rerun blindly**: inspect partial results and choose a fresh `--out` path once the issue is resolved.

## Output

Default root:

```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET_MultiSite_13_meteorology_stage20_trial_v1_20261015/
```

The two target sites may get new forcing CSVs under `DE-Gri/forcing/` and `FI-Let/forcing/` if there are permitted edits; other site manifest rows retain original Stage12, Stage15 or QC_v5 source paths. The `reports/` directory contains:

- `stage20_selected_13site_meteorology_manifest.csv`: exact 13-site selected version, path, SHA256, parent SHA256 and half-hour edit count.
- `01_13_fullblock_numeric_trial_policy.csv`: all 13 preselected blocks and acceptance/rejection reasons.
- `02_exact_T_VPD_TBOT_QBOT_change_ledger.csv`: exact site/time old/new paired meteorology and retained station PSRF.
- `03_full13_meteorology_numeric_and_extremes.csv`: independent full-year NOLEAP, range and thermodynamics audit for all 13 sites.
- `04_remaining_meteorology_flagged_events.csv`: T/pressure/radiation/rain/low-RH events for manual scientific decisions.
- `05_82_original_MDS_blocks_action_and_pending.csv`: per-block retained/replaced status; includes unsupported source/QC1 blocks.
- `06_preBIF_gate_status.json`: numerical and scientific status, BIF gate.
- `TECHNICAL_METHOD_AND_PENDING_SCIENCE_DECISIONS.md`: provenance and methodology discussion for later GitHub use.

## What remains after this one pass

Remaining unapproved DE-Gri and FI-Let MDS sections, adjacent local-source transition anomalies, FI-Hyy/IT-Col/IT-MBo/IT-Tor and DE-Lnf temperature events, ES-LJu 23:00 precipitation accumulation, GF-Guy intense tropical rain, and any other full-site rain/pressure flags must be scientifically documented as valid or corrected. The current code is intentionally **unable to identify a genuine storm from a time-allocated rainfall measurement error without source metadata**. BIF starts only when those scientific decisions and final audit are documented. This prevents silently passing unreasonable forcing into 500-year FATES experiments.

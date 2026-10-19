# Stage 26 — FI-Hyy, DE-Lnf, IT-Tor meteorological evidence and conservative trial

## Purpose

One-pass, source-verified targeted test after the completed Stage22 13-site candidate. This **does not** automatically certify any station as meteorologically valid. It is deliberately designed to **leave unresolved events unchanged** when there is not sufficient evidence to support replacement.

### Scientific policy

- **Do not overwrite official FLUXNET/ICOS or prior Stage20–25 outputs.** Preserve the original 13-site Stage22 selected manifest and all parent SHA256 digests.
- No `QC=0` tower temperature or VPD is automatically replaced. DE-Lnf's two jumps involve measured QC=0, so they will normally remain **HOLD** pending station metadata/instrument evidence.
- For temperature jumps, only an entire, *short* run of paired source TA/VPD QC=1/2 (at most four consecutive half-hours) enclosed by **both-side original QC=0 TA and VPD** is considered for a linear temperature and RH trial. The proposed temperature must resemble original FLUXNET ERA source temperature (within 4°C), show a significant improvement, and have transition jumps no greater than 5°C. This is a *numerical candidate*, not observation-based truth: FLUXNET ERA may supply the same gapfill lineage as QC=2.
- For RH below 1%, only an entire short VPD QC=1/2 run (at most four half-hours) bounded by plausible original VPD QC=0 humidity anchors qualifies for a VPD-only trial, checked against source ERA RH and QBOT physics. QC=0 VPD is never changed automatically. **Never clip RH artificially to 1%**.
- No precipitation, pressure, radiation or wind values are modified. IT-Tor alpine topography and 2025 source switches remain under scientific review even if a bounded trial passes numeric QA.
- `13/13 numeric hard failures=0` does not equal approval for BIF/DATM/production spin-up.

## Upload using WSL

Save `26_three_site_MET_conservative_trial.py` to Windows Downloads, then:

```bash
scp /mnt/c/Users/ly3n24/Downloads/26_three_site_MET_conservative_trial.py ly3n24@iridis6.soton.ac.uk:~/
```

## Execute in IRIDIS6

```bash
conda activate clm_fates_env
set -o pipefail
python ~/26_three_site_MET_conservative_trial.py --mode check \
  2>&1 | tee ~/FLUXNET_13_stage26_check.log

OUT="/iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET_MultiSite_13_MET_stage26_$(date +%Y%m%d_%H%M%S)_$$"
python ~/26_three_site_MET_conservative_trial.py --mode run --out "$OUT" \
  2>&1 | tee ~/FLUXNET_13_stage26_trial.log
```

Requires `~/20_onepass_13site_meteorology_preBIF.py` (previously run on IRIDIS), the original input audit manifest in `~/FLUXNET_13_input_audit/site_input_summary.csv`, and the existing Stage22 reports. If Stage20 script lives elsewhere, pass `--stage20-script /absolute/path/to/20_onepass_13site_meteorology_preBIF.py`. If Stage22 reports moved, pass `--reports /absolute/path/to/reports`.

## Outputs under `$OUT/reports/`

- `01_selected_13site_stage26_provisional_manifest.csv` — references all 13 candidates by their actual file paths and freshly computed SHA256; unchanged stations point back to Stage22.
- `02_all13_numeric_QC_after_trial.csv` — newly audited three target sites + inherited Stage22 QC for the other ten (whose SHA256 parents were verified).
- `03_3site_original_temperature_RH_event_evidence.csv` — exact source, QC0/1/2, ERA and parent forcing values for >12°C/30min T steps and RH<1% records.
- `04_3site_interval_trial_and_hold_reasons.csv` — reason for *each* attempted full source QC1/2 interval, or why it was held.
- `05_exact_stage26_trial_ledger.csv` — before/after T/VPD/RH/QBOT, source QC, and ERA reference for every actual changed half-hour. May be empty.
- `06_3site_remaining_warnings.csv` — fresh full-audit warning events for the three sites.
- `07_status_limitations.json` and `README_SCIENCE_DECISIONS.md` — immutable lineage and explicit scientific caveats.

The script will output a non-overwriting new CSV only at sites with an accepted bounded candidate. All other records are reused without change. Never commit proprietary EC/met data or source URLs with tokens into a public GitHub repo.

## What to send back

```bash
tail -50 ~/FLUXNET_13_stage26_trial.log

REPORT=$(awk '/^REPORTS:/{print $2}' ~/FLUXNET_13_stage26_trial.log | tail -1)
python - "$REPORT" <<'PY'
from pathlib import Path
import sys,pandas as pd
r=Path(sys.argv[1])
a=pd.read_csv(r/'04_3site_interval_trial_and_hold_reasons.csv')
print('\n=== CANDIDATE/HOLD REASONS ===')
print(a.groupby(['site','action','reason'],dropna=False).size().to_string() if len(a) else 'NONE')
q=pd.read_csv(r/'02_all13_numeric_QC_after_trial.csv')
print('\n=== NEW TARGET QC ===')
print(q[q.site.isin(['FI-Hyy','DE-Lnf','IT-Tor'])][['site','numeric_hard_failures','TA_step_gt_12C','RH_below_1pct']].to_string(index=False))
PY
```

If there are zero new edits, this is **not a software failure**: it means the missing external/local observational support prevents safe automatic correction. The next action is an explicit retain/repair/sensitivity decision, not relaxed thresholds.

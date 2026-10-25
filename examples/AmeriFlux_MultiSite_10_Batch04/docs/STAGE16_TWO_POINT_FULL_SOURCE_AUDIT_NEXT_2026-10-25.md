# Batch04 Stage16 — next operator action: full source and ten-site manifest audit

**Status (2026-10-25, GitHub-side review):** Stage15 alternative sensitivity trial has **already run** on IRIDIS6, as recorded in [Stage15 operator-verified report](STAGE15_VERIFIED_TWO_POINT_ALTERNATIVE_2026-10-25.md). Stage16 code was committed and reviewed for its intended checks, but **Stage16 IRIDIS6 `--audit` output has not been supplied or verified**. Do not mark Stage16 executed or passed yet.

## What has actually been demonstrated

* Ten-site Batch04 derived candidates exist, but **none is Post-v5 approved or DATM/model ready**.
* Stage12 resolved **148/156** selected non-Syv humidity events, leaving eight original QC0-temperature conflicts.
* Stage14 recomputed numerically physically closed RH/VPD at those eight timestamps **without changing original QC0 tower temperatures**. All eight scientific temperature HOLDs remain.
* Stage15 created an **isolated**, unapproved US-SP1 two-half-hour alternative: original T −6.9/−7.1 C at 2000-10-09 18:00/18:30 native time, proposed interpolated T 13.1816667/15.3633333 C, TA_F_QC only in alternative changed QC0→QC1; VPD was recalculated from the same independent humidity. Stage14 baseline and originals were not overwritten.
* Stage15 output was reported at `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage15_sp1_two_point_temperature_sensitivity/candidate_20261025T080658Z_cca73e0e`. Stage16 pins this path and Stage14's source SHA.

## Exact runnable Stage16 check — IRIDIS6 only

The version below pins the script to commit `9be06860ee3e9f14e08fb078d22d0090b49d58d4` (GitHub blob SHA `bb32418aaafde4152b0b94ed6a1285020740f02c`) and does **not** use git pull or update working forcing.

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_stage16"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts/stage16/16_verify_sp1_stage14_vs_stage15_exact_two_cell_trial.py"
  COMMIT="9be06860ee3e9f14e08fb078d22d0090b49d58d4"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  mkdir -p "$BASE"
  SCRIPT="$BASE/16_verify_sp1_stage14_vs_stage15_exact_two_cell_trial.py"
  curl -fLsS --retry 3 "$RAW/$REL" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --audit 2>&1 | tee "$BASE/stage16_full_source_audit.log"
)
```

A valid `--audit` must read all **368208** US-SP1 native HH rows; verify both receipts, both complete source SHA256 checksums and the two ten-site manifest checksums; establish that the **only** cell changes are TA_F, VPD_F, TA_F_QC at native timestamps `200010091800` and `200010091830`; verify trial RH/VPD closure; establish **identical pointers and SHAs for the other nine sites**. It prints `STAGE16 OTHER 9 SITE PATHS & SHAs IDENTICAL` and `STAGE16 PHYSICAL HUMIDITY CLOSURE PASS AT BOTH TRIAL T VALUES` only if those checks pass.

If an audit fails, **do not rerun Stage15 with new outputs, bypass checks, copy a different candidate into the pinned path, or promote the candidate**. Inspect and retain the exact failure log.

## Remaining science decision ledger (not approved)

| Site | Native timestamp | Reason to retain scientific HOLD |
| --- | --- | --- |
| US-SP1 | 200010091800 | Stage15 trial only; official original QC0 truth unresolved |
| US-SP1 | 200010091830 | Stage15 trial only; official original QC0 truth unresolved |
| US-SP1 | 200710151730 | T=11.150 C vs grid T=25.547 C; original source VPD impossible at tower T |
| US-SP1 | 200801160800 | T=−8.211 C vs grid T=8.173 C; original source VPD impossible |
| US-SP1 | 200801160830 | T=−4.365 C vs grid T=8.720 C; original source VPD impossible |
| US-SP1 | 200802030800 | T=−3.613 C vs grid T=13.005 C; original source VPD impossible |
| US-SRG | 201903191200 | T=0.718 C vs grid T=18.865 C; no reliable two-sided original tower reference |
| US-Seg | 201612271800 | T=0.015 C vs grid T=6.689 C; unstable original tower neighbours |

**Additional independent gate:** US-Syv's **606 old science HOLDs** and **10 failed Stage07 ERA jump endpoints** remain deferred. Stage15 cannot resolve them. It is not scientifically valid to accept a tower temperature merely because recomputing RH/VPD restores physical closure.

**What to send back:** the full text of `$HOME/ameriflux_batch04_stage16/stage16_full_source_audit.log`. Only the resulting IRIDIS6 operator log can upgrade Stage16 status to **VERIFIED PASS**; next inspect the six other original temperature conflicts and the site-specific native instrument/source metadata.

**Restrictions:** no original ZIP, FLUXMET, previous Stage files, Post-v5, DATM, CIME, Slurm, model spinup or station PFT change is authorised in Stage16.

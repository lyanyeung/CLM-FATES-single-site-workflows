# AmeriFlux Batch02: Stage11–31 scientific audit and provenance
**Snapshot: 24 October 2026. All forcing repairs remain on scientific HOLD.** No DATM, CIME, or model run was approved. No data or NetCDF files are stored in GitHub.

## 1. Historical scripts recovered as exact Git blobs
Stage11–22 restored from the prior commit [880b3b62](https://github.com/lyanyeung/CLM-FATES-single-site-workflows/commit/880b3b62ad43f0bcdacc49b58a859abc7ac0dca3); these are the original scripts, not reconstructed substitutes.

- Stage11 and 11b: 4,884 unresolved cold-humidity rows, proposal and audit; all provisional.
- Stage12: humidity physical/source review.
- Stage13, 13b–13f: ERA5 dewpoint pilot, comparison, timezone and drought checks.
- Stage14: adjacent tower QC study.
- Stage15 and 16: verified five ERA5 one-year pilot and full-year comparison.
- Stage17 and 18: exact anomaly-year retrieval plan and previously downloaded ERA5 grid-year receipts. **Do not re-download unnecessarily.**
- Stage19: all 4,884 target timestamps independently examined with CDS ERA5 T, dewpoint and pressure.
- Stage20: water/ice saturation and RH-vs-dewpoint transfer.
- Stage21: 3,947 unapproved risk-screen candidates and 937 additional HOLD.
- Stage22: A/B/C risk tier; categories do **not** constitute approval.

## 2. Operator's original inline Stage23–30 audit findings
The original Stage23–30 code ran as inline Python in IRIDIS6 shells, not as files committed to GitHub. The new **read-only reproducibility scripts** under scripts/stage23–stage30 use a common implementation in scripts/diagnostics; they reproduce the scientific screens, but are not byte-for-byte copies of the original ephemeral commands. Until rerun, the following remain historical operator-reported evidence.

| Stage | Key result |
|---|---|
| 23 | 4,879/4,884 original final T/VPD pairs violate the 0.005-hPa-tolerant water-saturation condition; 4,884/4,884 FLUXNET ERA pairs violate it |
| 24 | Outside Stage19, 19,734 additional final violations and 10,268 additional embedded ERA violations; these sets overlap |
| 25 | 29,504 distinct outside-Stage19 flagged times = 19,236 FINAL_ONLY + 9,770 ERA_ONLY + 498 BOTH |
| 26 | Ho1: 15,446/15,459 mixed observed-TA/ERA-VPD failures have physically consistent companion ERA pairs; EML: 2,039 bad measured-TA/MDS-VPD pairs are also bad as MDS pairs |
| 27 | Ho1 median ERA-minus-tower T gap +14.062°C across mixed failures, with multiple multi-day winter episodes; EML MDS VPD QC=1 for all 2,039 records; one borderline 2010 QC0/QC0 exceedance ~0.0092 hPa |
| 28 | FLUXMET-embedded and standalone ERA T/VPD are equal for all 4,884 Stage08 unresolved timestamps; all companion ERA inferred RH values below −2% and equal to Stage08 diagnostics |
| 29 | Independently downloaded CDS ERA5 RH numeric valid 4,884/4,884; 431 dewpoint transferred VPD values negative at retained T (Ho1 425, GLE 6); 2,782 ice supersaturation cautions; still no observed humidity validation |
| 30 | Conditional QC0 measured-T comparison at held timestamps: 938 independent paired anchors across sites |

### Stage30 observed-temperature comparison (at selected Stage19 timestamps only)
| Site | QC0 anchors | FLUXNET-downscaled T MAE °C | CDS ERA5 T MAE °C | CDS closer | FLUXNET closer |
|---|---:|---:|---:|---:|---:|
| US-EML | 618 | 2.379 | 3.978 | 209 | 408 |
| US-GLE | 103 | 2.525 | 3.033 | 46 | 57 |
| US-Ho1 | 216 | 2.804 | 1.481 | 147 | 69 |
| US-ICh | 0 | — | — | 0 | 0 |
| US-ICt | 1 | 3.776 | 2.103 | 1 | 0 |

The comparison is **conditional on the held anomaly selection**, not full-year model performance. VPD positivity under a water-saturation constraint is necessary, not sufficient, evidence for a scientifically valid replacement. FLUXNET internal ERA and independent CDS ERA5 are different processing chains; ice-saturation and altitude uncertainty remain. US-Ho1 UTC offset is **provisional**. No RH floor clipping or QC0 alteration is authorised.

## 3. Stage31 next: source-aware sensitivity design gate
Read-only compare retained measured temperature (QC0), ERA-origin temperature (QC2), and other sources with CDS ERA5 RH transfer and dewpoint actual-vapour-pressure transfer, including ice and physical-caution flags. No forcing files are created and no spin-up should be submitted. Independent humidity/timing/altitude checks are still needed.

## 4. GitHub → IRIDIS6 reproducible execution
Download the common engine plus requested stage wrapper from the canonical main branch into a clean folder (no `git pull`, especially if the working tree has conflicts):

```bash
set -euo pipefail
RAW=https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/examples/AmeriFlux_MultiSite_10_Batch02
D="$HOME/Batch02_science_audits"
mkdir -p "$D/diagnostics" "$D/stage31"
curl -fLsS "$RAW/scripts/diagnostics/batch02_stage23_31_audits.py" -o "$D/diagnostics/batch02_stage23_31_audits.py"
curl -fLsS "$RAW/scripts/stage31/31_sensitivity_design_gate.py" -o "$D/stage31/31_sensitivity_design_gate.py"
PY=/home/ly3n24/.conda/envs/clm_fates_env/bin/python
"$PY" "$D/stage31/31_sensitivity_design_gate.py" --check
"$PY" "$D/stage31/31_sensitivity_design_gate.py" --audit
```

Both script modes are read-only; they verify source SHA256 and scientific HOLD before reporting. The `curl` steps write **only downloaded script copies** to home. No source CSV, forcing, NetCDF, DATM, case, or Slurm job is modified.

## 5. Existing candidate protection
The five Stage07 numeric-only candidates US-BZS, US-CMW, US-Ha1, US-Ho2, US-Ho3 remain preserved; they are not approved. The Stage08 incomplete marker, 4,884 HOLD rows and CDS source receipts remain protected. OSH-site eligibility and reference land cover/PFT, ZBOT, and flux-footprint representation are separate pre-model scientific reviews.

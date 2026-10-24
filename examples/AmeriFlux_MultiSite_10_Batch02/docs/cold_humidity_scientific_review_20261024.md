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

## Stage31 measured output and Stage32 continuation — 24 October 2026

IRIDIS6 operator ran the published Stage31 wrapper with `--check` and `--audit`, both successfully. All 4,884 Stage08 held timestamps were retained; source groups were QC0 measured temperature **938**, QC2 ERA-origin temperature **3,945**, and one other QC1. The RH-transfer variant passed its constructed numerical water-saturation screen for all 4,884, **which is not independent humidity validation**. Dewpoint actual-vapour-pressure transfer to retained site T produced **431 negative VPD values** (US-Ho1 425 in QC2 group, US-GLE 6: 4 QC0 and 2 QC2). ERA5 ice supersaturation cautions: **2,782** (EML 815, GLE 194, Ho1 29, ICh 141, ICt 1,603). All zero science approvals.

**Stage32** (`scripts/stage32/32_review_humidity_source_phase_risks.py`) checks the mathematical A/B/C alternatives **without creating a repaired forcing**: (A) transfer ERA5 water RH to retained site T; (B) transfer ERA5 dewpoint-derived vapour pressure to retained site T; and (C) use ERA5 T + ERA5 RH as a numerically paired *reference only*. It separates recorded source QC0/QC2, subzero water/ice physical constraints, phase warnings, temperature differences, and a hierarchical HOLD review priority. US-Ho1 clock remains an overriding hold. Stage32 is a new executable script: live IRIDIS output pending and should be reported separately from Stage31 operator evidence.

Download and run Stage32 on IRIDIS6 using a specific GitHub commit hash instead of `git pull` into an unresolved working tree:

```bash
set -euo pipefail
RAW=https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/examples/AmeriFlux_MultiSite_10_Batch02
DIR="$HOME/Batch02_science_audits/stage32"
mkdir -p "$DIR"
curl -fLsS "$RAW/scripts/stage32/32_review_humidity_source_phase_risks.py" -o "$DIR/32_review_humidity_source_phase_risks.py"
PY=/home/ly3n24/.conda/envs/clm_fates_env/bin/python
"$PY" "$DIR/32_review_humidity_source_phase_risks.py" --check
"$PY" "$DIR/32_review_humidity_source_phase_risks.py" --audit
```

The `curl` command writes only the local downloaded script copy to HOME; the script itself does not write output files or change original data, forcing, DATM, CIME, or jobs. Old Stage11–22 data retrievals must not be rerun without need.

## Stage32 completed and Stage33 next (24 October 2026)

Stage32 was executed successfully on IRIDIS6 (both --check and --audit). All 4,884 Stage19–21 source records matched their pinned SHA256 lineage and remain SCIENTIFIC HOLD, with 0 approved repairs.

**Stage32 summary:** 4,884 RH-transferred water-VPD numerical candidates are physically bounded by construction (not independently humidity-validated). Td-transfer water-negative VPD occurs 431 times: US-Ho1 425 (all source QC2 temperature), US-GLE 6 (4 QC0, 2 QC2). 2,782 grid-ERA5 ice-RH warnings were recorded. At the *retained site temperature*, RH-transfer ice saturation is exceeded 1,616 times (EML 540, GLE 171, Ho1 160, ICh 30, ICt 715); Td-transfer ice saturation is exceeded 529 times (EML 13, GLE 47, Ho1 469, ICh 0, ICt 0). Counts overlap and should not be summed as unique events.

**Mutually exclusive review routes:** P0_HO1_CLOCK_HOLD 917; P1_TD_WATER_SUPERSAT_HOLD 6; P2_ICE_PHASE_HOLD 2,773; P3_TEMPERATURE_REPRESENTATIVENESS_HOLD 818; P4_UNVALIDATED_HUMIDITY_HOLD 370. All are HOLD, including P4.

Strong Ho1 temperature inconsistency: 1999-02-13 01:00 retained TA -12.561 C, CDS ERA5 TA +9.2454 C, dewpoint +8.7993 C, hence Td-transfer water VPD -8.9817 hPa. Do not blindly substitute dewpoint or alter tower observations.

**Stage33** script: scripts/stage33/33_audit_US_Ho1_clock_alignment.py. It reuses the existing receipt- and SHA256-verified Stage15/18 NetCDF site-years, verifies Stage19 nominal local-UTC=-5 interpolation and the 425 negative water-VPD count, and tests offsets -7..-3h against all original tower QC0 observations in covered years, winter QC0, and the held QC0 subset. Offset sensitivity is NOT independent UTC/BADM certification, and full site grid orography remains unknown. Original US-Ho1 FULLSET 3-6 has no BIF. AmeriFlux official site https://ameriflux.lbl.gov/sites/siteinfo/US-Ho1 reports 45.2040 N, -68.7402 longitude and 60m elevation but does not alone establish the release UTC offset. No additional CDS download is needed. Stage33 live IRIDIS results are not yet verified.

Stage33 usage: download the single Python source to HOME from a pinned GitHub commit, then run --check followed by --audit. Both operations read only scientific/source data and never modify forcing, CIME, DATM or Slurm.

### Stage33 v2 receipt-path verification fix (24 October 2026)

First operator test: Python compilation passed, but `--check` stopped at the US-Ho1 1996 Stage15 `verified_receipt.json`: `Pinned verified receipt differs`. Root-cause in code: Stage19 stored receipt ledger keys using original `Path.home()` spelling without calling `resolve()`, while the initial Stage33 revision resolved the candidate receipt path **before** performing exact-string dictionary lookup. On systems with `/home/ly3n24` and `/iridisfs/home/ly3n24` aliases, an absent dictionary key was treated as a hash mismatch. This is an identified code-path bug; a true on-disk source mismatch has **not** been established by that traceback alone.

V2 `verify_ledger_file` locates ledger entries referring to the *same resolved file*, requires one unambiguous expected digest across matching aliases, computes and verifies the actual file SHA256, and still verifies the NetCDF against both Stage19 and its verified receipt. It never weakens hashes or silently skips missing files. After the fix, re-run `--check` and only then `--audit`. A future failure indicates a separate mismatch requiring diagnosis. Shells configured with interactive `set -e` may close on failed `python` commands; run inside an `if ...; then ...; else ...; fi` guard or `set +e` when troubleshooting. No forcing edits or scientific approvals.


## Stage33 VERIFIED and Stage34 next (24 October 2026)

Stage33 v2 successfully completed on IRIDIS6 with exit code 0: 16 ERA5 grid-year receipts/NetCDF hashes verified; the original US-Ho1 meteorological release pinned; 917 Stage19 anomalous timestamps reproduced; and Stage32's 425 negative dewpoint-transfer VPD events reproduced. There was no source change, download or job submission.

Local-minus-UTC sensitivity MAE for 106,336 observed QC0 temperature comparisons, from -7 to -3 hours, was 2.153, 1.708, **1.472 (nominal -5)**, 1.558, 1.889 degrees C respectively. Winter QC0 (n=35,409) MAE was 1.999, 1.641, **1.482**, 1.587, 1.850 degrees C. Selected held QC0 (n=216) MAE was 1.894, 1.566, **1.481**, 1.544, 1.634 degrees C. Negative Td-transfer VPD counts across same hypothetical offsets were **421, 425, 425, 427, 425** (out of 917). Therefore clock choice alone cannot explain or resolve the 425 conflicts.

Original QC0 temperatures are missing in the Stage19 years 1997, 1998, 2001-2005 and 2022, with only one source QC0 record in 2007. The dramatic gapfill source discrepancies are in years lacking direct temperature confirmation. Time offset -5 is the **best tested** temperature fit, but NOT officially certified without US-Ho1 BADM UTC_OFFSET. The FLUXNET2015/ONEFlux convention is local standard time (no daylight-saving changes); the authoritative offset should be checked from site metadata: https://fluxnet.org/data/fluxnet2015-dataset/ and https://ameriflux.lbl.gov/sites/siteinfo/US-Ho1 .

Stage34 script: scripts/stage34/34_audit_US_Ho1_QC2_temperature_provenance.py . This new READ-ONLY audit verifies Stage19-21 and original source SHA256/row identities, then compares 917 held US-Ho1 cases and the 425 QC2 negative-Td-transfer cases by year, including observed QC0 coverage and FLUXNET downscaled versus CDS ERA5 temperature divergence. It reproduces Stage30 selected QC0 MAEs before drawing a source-specific scientific interpretation. It does not infer or approve any correction, or modify forcing, NetCDF, CIME, DATM or Slurm. It still requires first IRIDIS6 execution to validate.

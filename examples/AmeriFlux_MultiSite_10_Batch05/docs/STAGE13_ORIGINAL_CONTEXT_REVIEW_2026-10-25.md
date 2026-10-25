# Batch05 Stage13 — original native-context verification and 27 measured RH threshold cases

**Operator execution 2026-10-25 19:35 UK (BST ended 2026-10-25; quoted times in inputs are native FLUXNET local standard):** Git script hash verified; syntax and Stage13 self-test PASS. Final output:

```text
STAGE13 SUMMARY sites=10/10 priority=382 context=4966 interpolations_reverified=229 approved=0
NO REPORT OR SOURCE WRITES; NO MODEL/FORCING MODIFICATIONS; NO SLURM
```

The Stage13 script rechecked all original 13 x half-hour source context windows, center source meteorology, original TA/VPD consolidated QC, original Stage10 low-RH condition, and physical/temporal eligibility of 229 previously generated QC0/0 anchor-based linear interpolation candidates. It rejected all 11 previously identified mathematically nonphysical interpolation candidates and preserved 170 ERA pairing holds, 27 measured QC0/0 formula-negative RH cases. **Zero candidate approvals or forcing writes.**

## Verified categories (membership counts overlap)

| Criterion | Number |
|---|---:|
| Unique source priority timestamps | 382 |
| Original native half-hour context rows (13 per timestamp) | 4,966 |
| Interpolation math reconstructed from original brackets, still unapproved | 229 |
| Interpolation result remains nonphysical | 11 |
| Original measured `TA_F_QC/VPD_F_QC=0/0` with water-formula negative RH | 27 |
| ERA self-pair or ERA water-vapour-pressure/tower-T mixing physically inconsistent | 170 |
| Measured QC0/0 near-threshold RH: native RH vs current formula within **0.2 percentage points** | **27/27** |
| Approved replacements or altered forcing | **0** |

### 27 measured QC0/0 formula-negative source records

**US-WCr: 26 source rows** from `2025-08-25 13:00` through `2025-08-26 01:30` (native printed tower time), original RH mostly `0.0%` with a few values within ~±7e-6 percentage points, while the chosen Magnus-type water formula yields RH approximately `-0.108` to `-0.084%` among these; **US-Vcm: 1 record** on `2025-10-13 17:00`, original RH `0.08066284%` vs water formula `-0.022119%`. All 27 differences range **0.084182 to 0.108221 percentage points**, mean **0.101051 percentage points**, without evidence these original RH values are independent direct sensor measurements.

**Do not label every tiny formula-negative derived RH value an instrument failure.** Preliminary evaluation of alternative standard water saturation curves on two examples supports sensitivity of near-zero RH to formula constants. Different vapor pressure conventions, rounding/precision and source algorithms need checking against provenance. This does not establish the correctness of an RH at exactly 0%, nor scientific approval to retain all extreme values in forcing without further review.

### 229 verified but highly divergent linear-interpolation hypotheses

The largest original-to-unapproved-linear interpolation differences printed were:

| Site | Original native time | Original consolidated VPD (hPa) | Linear candidate (hPa) | Candidate - original (hPa) | Anchor gap (hours) |
|---|---|---:|---:|---:|---:|
| US-Var | 2019-08-19 06:00 | 21.747 | 0.11271 | **-21.63429** | 3.5 |
| US-Var | 2019-06-14 05:30 | 22.658 | 1.21557 | **-21.44243** | 3.5 |
| US-Var | 2020-07-22 05:30 | 22.680 | 1.73720 | **-20.94280** | 2.5 |
| US-Var | 2019-09-18 12:00 | 21.736 | 0.92833 | **-20.80767** | 1.5 |
| US-Wjs | 2020-06-24 05:00 | 16.543 | 0.00000 | **-16.54300** | 2.0 |

These results are **not** evidence that interpolation is automatically preferable: the bracket endpoints are mathematically coherent, but temporal representativeness, potential source discontinuities, units, gap length, local meteorology, and independent humidity must be investigated. Some hypotheticals give VPD exactly zero; that requires particular caution.

## Next gate

Stage14 should examine **all 229** candidate differences, classify them by magnitude (including >5 and >10 hPa), and perform water-saturation-formula sensitivity on all **27 QC0/0 measured source exceptions** using original Stage12 CSVs, without changing original data or forcing. The actual FLUXNET-source VPD calculation convention is not yet established. A mathematical PASS is not a scientific repair approval. The remaining **1,368** low-RH HH outside the four Stage12 priority categories still require a separate event-resolution workflow.

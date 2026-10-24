# Stage54 — completed 444 vs 4,884 site-local timestamp crosswalk

Date: 24 October 2026. Source: operator-pasted IRIDIS6 stdout.
Stage54 pinned Git blob `f74d004bf9277c0583309387ea1352703da76db7`
was verified; syntax, self-test, read-only source check and full audit PASSED.

Report on IRIDIS6:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage54_444_vs_4884_timestamp_crosswalk_20261024T101940Z_bac3a939`

## Verified result

**Exact same-site and original tower-local-start-timestamp intersection: 0.**

| Site | Stage53 separate ERA5 RH replacement proposals | Stage11 independent scientific HOLD records | Shared timestamps |
| --- | ---: | ---: | ---: |
| US-EML | 0 | 1327 | 0 |
| US-GLE | 0 | 295 | 0 |
| US-Ha1 | 398 | 0 | 0 |
| US-Ho1 | 0 | 917 | 0 |
| US-Ho2 | 7 | 0 | 0 |
| US-ICh | 9 | 169 | 0 |
| US-ICt | 30 | 2176 | 0 |
| **Total** | **444** | **4,884** | **0** |

The union of the **two audited target sets** is therefore 5,328
distinct site-local timestamp identities, but this is **not** a census
of all scientifically problematic original Batch02 humidity records.
Stage48 observed 26,332 unique source hard-physics cases, and
Stage07's initial 4,904 or Stage08's 4,884 represent distinct
filtered selections, not additive counts.

Stage53 has 444 traceable independent CDS ERA5 RH/VPD/QBOT proposals,
with 405 original RH>100 phase flags and 27 US-ICt original T QC1/2
review flags. **No model forcing or original input was modified.**
The other **4,884** Stage11 targets still have no scientific release.

The zero-intersection result is exact only for the compared
(site, tower-local-time) coordinates. It does not license release
of Stage11 candidates or the Stage53 phase/temperature review flags.

## Scientific next steps

Reuse the pre-existing [Stage19 external CDS ERA5 review
code](../scripts/stage19/19_audit_all_era5_dewpoint_targets.py), which
computes same-product t2m/d2m/sp ERA5 RH and consistent VPD/QBOT for
all 4,884 Stage11 targets (five sites, 42 site-years), while respecting
source QC, subzero water-phase concerns, and **US-Ho1 UTC−5 offset
provisional**. A new read-only triage step can reconcile the Stage19
report with this exact zero-overlap Stage54 audit before any separate
forcing-integration approval.

**This GitHub entry records operator-supplied results, not an upload
of the original IRIDIS6 Stage54 CSVs or an independent rerun here.**

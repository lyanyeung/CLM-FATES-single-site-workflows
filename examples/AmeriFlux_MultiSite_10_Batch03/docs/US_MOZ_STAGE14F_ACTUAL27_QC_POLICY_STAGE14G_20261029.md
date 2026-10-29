# US-MOz Oct 29 — actual Stage14F 27 new isolated numerical RH/T scenario and operator's QC-class interpolation policy

**ACTUAL IRIDIS6 source result** supplied by operator on 2026-10-29 04:18 UTC. SHA-pinned Stage14F script syntax PASS and signed original source checks PASS. Original **27/27** Jan2005 QC1 TA/VPD values were numerically reconstructed in a new isolated **315360 native 30-min row** experiment and full-site water/QBOT passed. All previously **40 operator-approved Stage13L** native records were preserved exactly, original FLUXMET and old source trials unchanged, zero Slurm.

Actual output:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/US_MOz_Jan2005_first27_REANALYSIS_SENSITIVITY_20261029T041812Z_f629fa16`.

Actual 27 source QC1 original tower temperature fell from artificially warm ~+5.29 to +8.02°C to matching separate ERA5-Land source values −0.70 to −5.74°C. The new water RH spans 96.36% to 57.62%, VPD ~0.211 to 1.690 hPa, valid QBOT; these are **ERA5-Land sensitivity**, not independently measured tower corrections.

The native LEFT edge 2005-01-05 19:30→20:00 has **5.884515°C temperature jump**, VPD jump only 0.031690 hPa. Native RIGHT edge 2005-01-06 09:00→09:30 has 1.445860°C T jump, 0.009262 hPa VPD jump.

## Subsequent explicit operator QC-aware interpolation rule

**User instruction:** when the real source QC transition is `0→1`, rely on a valid QC0 measured anchor and interpolate; for `1→2`, handle the trusted QC1 side, without treating QC2 downscaled ERA as an observed QC0. Critically, the historical signed Stage13I already established an uninterrupted original **TA_F_QC=1** regime 2005-01-03 12:30 through Jan06 09:00 (138 native HH). Therefore the problematic LEFT edge 19:30→20:00 is **QC1→QC1, not 0→1**. The RIGHT 09:00→09:30 original T is **QC1→QC2** but already physically continuous. Do not modify it.

**Concrete one-hour bounded sensitivity operator decision:** use existing selected 19:00 **QC1** T/VPD as left endpoint and signed Stage14F 20:00 reanalysis T/VPD as right endpoint; apply a single new correction **at 19:30 only** by midpoint interpolation of *temperature and actual water vapor pressure e*, then set `TBOT=273.15+T`, `VPD=es_water(T)-e`, `QBOT=0.622 * 100e / (PSRF−0.378*100e)`. This should split the 5.885°C one-half-hour jump into two shorter (~2.94°C) edges without changing the 27 or 40 previous source hours, provided actual source T/VPD at 19:00 and 19:30 are both QC1. **The script fails closed if the actual QC, physical bounds, original SHA, or edge constraints disagree**, rather than blindly interpolating a QC0 anchor not actually observed.

[Stage14G one-hour QC-aware script](../scripts/stage14/14g_US_MOz_QC1_to_QC1_left_edge_one_hour_interpolation.py), Git fixed revision `4b04f73557066893be18e9172fa4e4d903d0d13a`, blob `8cc1e6f2347c4606aa23779d06739e3f7eb7e0ff`. **Not yet executed on IRIDIS6.** Run once in existing conda environment, original SHA-checked source, report exact 5 anchor QC and all 3 local native boundaries. An isolated new research version will be saved only after full 315360 water VPD/QBOT/TBOT closure and all 3 boundaries <=4°C/4hPa pass. No Post-v5/DATM/AD400/Slurm authorization and NO assertion this is an observed correction. Jan09 separate QC1 opposite-biased source episode remains entirely unchanged/pending later decision.

```bash
(
 set -euo pipefail
 F="$HOME/US_MOz_qc1_edge_once.py"
 curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/4b04f73557066893be18e9172fa4e4d903d0d13a/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage14/14g_US_MOz_QC1_to_QC1_left_edge_one_hour_interpolation.py" -o "$F"
 test "$(git hash-object "$F")" = "8cc1e6f2347c4606aa23779d06739e3f7eb7e0ff"
 python3 -B "$F" --run 2>&1 | tee "$HOME/US_MOz_qc1_edge_once.log"
)
```

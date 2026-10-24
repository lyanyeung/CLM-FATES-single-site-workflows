# Stage72 — CA-Man ERA temperature substitution: relative humidity and vapor-pressure deficit consequences

Stage71 read-only audit found **36 isolated QC1 half-hour air-temperature substitutions** bracketed by QC0. Substituting the source `TA_ERA` value would leave **35 cases** with both incoming and outgoing temperature jumps ≤10°C; `2007-03-10 11:30` remains a special HOLD (entry jump still 17.3°C).

`72_CA_Man_ERA_QC1_RH_VPD_shadow.py` independently checks Stage61 and Stage70B event temperatures and QC0–QC1–QC0 boundaries against the **SHA-pinned 15-year original CA-Man forcing**, recomputes humidity, and produces a **non-production** fixed-Q ERA TA shadow *only for proposals that pass explicit basic physical gates*. It never changes the original.

## Source and calculation caution
The ERA reference here is the **FLUXNET ERA5_HH `TA_ERA` field** from existing Stage61 (possibly processed/bias-corrected). It is **NOT an independently downloaded ERA5 or ERA5-Land grid-cell series**, and tower averaging window, lag, sensor identity, and source independence remain unverified.

The 35 cases use these counterfactuals to reveal humidity consequences:
1. **Fixed specific humidity QBOT**: replace TBOT and TA_USE with ERA `TA_ERA`, keep `QBOT` and `PSRF` unchanged, and calculate RH/VPD from the same water vapor: `e=q (p/100)/(0.622+0.378q)`, `es(T)=6.112 exp(17.67T/(T+243.5))`, `RH=100 e/es`, `VPD=es-e`. Physically nonviable combinations (RH<1%, RH>100.1%, VPD<−0.05hPa, invalid T/P/Q) are **HOLD_NO_EDIT**.
2. **Preserve original implied RH**: report (do not apply) the QBOT change necessary for this alternative at the new temperature.
3. **Preserve original VPD**: report (do not apply) the QBOT change necessary for this alternative at the new temperature; impossible water vapor pressure is rejected.

The diagnostic CSV includes before/after QC0 temperatures, original and fixed-Q ERA temperatures, RH and VPD at all three points, boundary changes of RH/VPD, hypothetical QBOT percent changes required by the other two scenarios, and per-event science holds.

**Mode `--self-test`** uses internally constructed physical calculations; **`--check`** reads source reports and original forcing, lists all 35 RH/VPD consequences, and creates *no files*. **`--trial`** creates only a new timestamped `reports/stage72_CA-Man_ERA_QC1_T_RH_VPD_*` with a 35-row science ledger and an independently named `*_SHADOW_NOT_PRODUCTION.csv` for physical-gate-passing events. It checks all 262,800 rows for unplanned differences and reuses the complete Stage58 NOLEAP/structural/RH/VPD scanner. If all 35 fail the physics screen, no shadow forcing is created.

**Science status:** 0 approved repairs. A good jump count or plausible RH range is not proof of meteorological accuracy. Do not submit CIME/DATM or alter forcing, original ZIP, selected site forcings, QC0 observations, or Slurm jobs. The 2007-03-10 anchor anomaly and remaining P1/P2/RH issues remain separately on HOLD. The next evidence gate is independent tower humidity/dewpoint and the ERA5-Land comparison (hourly native data with documented interpolation/time semantics).

# Batch05 US-WCr — Stage75 source audit and Stage76 direct user-approved versioned fixes

## Actual original source 24 events/62 HH (29 October 2026)

The operator executed Stage75 on IRIDIS6 and supplied the full, original measured tower T/VPD/QC and processed source ERA context for **24 original US-WCr P2/P3 episodes, 62 native half-hours**. Original source FLUXMET ZIP SHA256 `f13c3a26a051bbe351fe5aa66a2cd7eef3849b33645732810bfc74a34c5e6f75`. Stage75 verified **62/62** matched original Stage27 source T/VPD/QC and original Stage63 episode keys.

Actual Stage75 summary:
```
STAGE75 CLASSIFIED original_RH_negative 61 original_RH_nonnegative 1
STAGE75 FLAGGED_TA_VPD_QC_PAIRS {('0', '1'): 60, ('1', '2'): 2}
STAGE75 TEMPERATURE_NUMERICAL_EXCEPTIONS 2
STAGE75 CHECK_SOURCE_TA 201610011000 TA_F -13.734 TA_ERA 13.568 prev_TA -21.173 next_TA -43.523
STAGE75 CHECK_SOURCE_TA 201610011130 TA_F -13.734 TA_ERA 15.844 prev_TA 16.055 next_TA 16.910
```

One flagged `201105260800` source RH 0.33% is mathematically nonnegative and **PASS_KEEP_ORIGINAL**, no numerical change. This follows the investigator's exact rule: derived RH<0 directly repair; RH>=0 original flags are accepted unless clearly wrong; original source-QC provenance always immutable.

For **59 of the 61 original negative RH HH**, tower-selected original `TA_F` is retained while erroneous VPD is corrected. RH is linearly interpolated between the nearest source-native *physically nonnegative RH* records on both sides (preserving native half-hour clock/time weighting) and used to recompute VPD at original selected TA; when two finite valid RH anchors are not available within 72h, fallback is same-native **original source processed ERA RH**, not unrelated reanalysis or an invented donor. The source-processed ERA companion is labeled appropriately and is **not independently downloaded ERA5-Land**. Only source flagged selected native times are altered; nonflagged negative RH neighbors are not silently bulk-rewritten.

### Exception: 2016-10-01 source-native TA clearly corrupted despite QC flags

Stage75's original half-hour context proves a temperature source fault across 08:30–11:30, not merely two source QCs:
| Native time | Original TA °C | Original TA QC | Original VPD QC | Source processed TA_ERA °C | Stage76 versioned approved TA policy |
|---|---:|---|---|---:|---|
| 08:00 | 11.783 | 0 | 0 | 10.128 | native credible donor, unchanged |
| 08:30 | 1.178 | 0 | 0 | 10.878 | interpolate 08:00 QC0 and 09:00 QC1 = **11.742** |
| 09:00 | 11.701 | 1 | 1 | 11.629 | native credible donor, unchanged |
| 09:30 | −21.173 | 1 | 1 | 12.598 | interpolate 09:00 QC1 and 11:00 QC0 = **12.790** |
| 10:00 | −13.734 | 1 | 2 | 13.568 | interpolate 09:00 QC1 and 11:00 QC0 = **13.878** |
| 10:30 | −43.523 | 0 | 0 | 14.173 | interpolate 09:00 QC1 and 11:00 QC0 = **14.967** |
| 11:00 | 16.055 | 0 | 2 | 14.779 | native credible donor, unchanged |
| 11:30 | −13.734 | 1 | 2 | 15.844 | interpolate 11:00 QC0 and 12:00 QC2 = **16.483** |
| 12:00 | 16.910 | 2 | 2 | 16.910 | native credible donor, unchanged |

Original 2016 `201610011000` and `201610011130` had negative implied RH due to corrupted source T, rather than physically impossible VPD2 when coupled with a realistic TA. Correct their TA **first** and preserve source VPD2; this makes the thermodynamic RH physically feasible. Three additional original-source context half-hours (`08:30, 09:30, 10:30`) also need source TA repaired in versioned overlay because the original period is visibly corrupted, even though these three weren't in Stage63's selected 62 flags. Keep original source QC0/1/2 labels and original archived values unchanged. This is an **explicit local native temperature science exception**, using credible local native time donors of mixed provenance; do **not** present these repairs as standard QC0→QC1 two-QC0 donor interpolation (two original QC0 values at 08:30 and 10:30 are themselves corrupt). Original source `09:00` 11.701°C remains unchanged.

### Result to be verified by IRIDIS6 run

**Expected new versioned approval table: 259 previous approved exact rows + 59 standard RH/VPD repairs + 2 flagged 2016 TA repairs + 3 additional original 2016 TA context repairs = 323 HH.** The 62 original US-WCr flagged HH are all dispositioned: 61 directly repaired, one retained unchanged, 0 new per-event operator HOLD. Original source ZIP, historical T/VPD/QC, old 259 overlay, active DATM/CIME and Slurm are not modified. This output is a **versioned science-approved research repair**, not a production-forcing transformation.

[Stage76 source script](../scripts/stage76/76_US_WCr_61_negative_RH_plus_3_temperature_context_direct_approved_323.py) commit `e264d4504622c1d4f66e27358fdc052fd699b995`, Git blob `936a46921df2fc1bd5eff8c56dc66547592527b6`.

[SHA-pinned Stage76 launcher](../scripts/stage76/run_stage76_US_WCr_61_RHplus2016_T_direct_323_iridis6.sh) commit `06ff3815a01b498cc984148e7976c6c5092f52f3`, Git blob `197992e3e30be03df9cd8eca1e64561655103c2d`.

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/06ff3815a01b498cc984148e7976c6c5092f52f3/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage76/run_stage76_US_WCr_61_RHplus2016_T_direct_323_iridis6.sh" -o "$HOME/run_stage76_WCr.sh" && test "$(git hash-object "$HOME/run_stage76_WCr.sh")" = "197992e3e30be03df9cd8eca1e64561655103c2d" && bash "$HOME/run_stage76_WCr.sh"
```

Current status: Stage75 read-only source review actual SUCCESS, Stage76 SHA-pinned code/launcher published; actual IRIDIS6 Stage76 run is **not yet** reported. The next user step is run exactly once, paste `STAGE76 SUCCESS` and `STAGE76 TA_EXCEPTION` lines.

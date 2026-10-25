# AmeriFlux Batch04 Stage17 — operator-verified six-event native tower / ERA5-Land diagnostic

**Date:** 2026-10-25. **Execution:** IRIDIS6 operator output supplied verbatim in the 2026-10-25 conversation. Script self-test PASS (printed twice); read-only six-event diagnostic **6/6 complete**, **zero official tower-temperature science HOLDs cleared**. This record describes *operator stdout*, not GitHub running IRIDIS6.

## Integrity and input coordinates

| Site | Original FLUXMET SHA256 | Stage14 derived FLUXMET SHA256 | BIF location | BIF UTC offset |
| --- | --- | --- | --- | --- |
| US-SP1 | `d5fe39d617e1e7964542cf3d3f8f068e00b028a37e4db7814b77c6cd813e1963` | `3f2489eea6e7016b3c184bd90c93acd6597d32fc3d4cc8872ac28237a5181806` | 29.7381, −82.2188 | −5 h |
| US-SRG | `bce57eebcce1babf9f9310e76c8f41451a8e3632c8d08a95f03345e35a189567` | `57f650493a510cffe3146e3371599479f243ee188fb676b55c269683a1a63f39` | 31.7894, −110.8277 | −7 h |
| US-Seg | `2fc2fc1c846749070f62c981b0f71789bdc9dae7585eeb0b0f30455a9e88034d` | `22db08e969883cb7f5bc0dd7c3b161c60582c6fe6fe8715a0c9e23598cafbea6` | 34.3623, −106.7020 (approved BIF group 1495) | −7 h |

## Exact observed six-event findings

All original event TA values are **QC0**. The original VPD exceeded saturation at these recorded temperatures; Stage14 only recalculated humidity/VPD, *not temperature*. `T_minus_grid` is original TA minus independent ERA5-Land 2-m temperature in °C. The median/MAD comparisons are the script's **full ±6 h neighbour baseline** and must not be misread as a solely locally independent sensor measurement.

| Site | Native timestamp | Original TA °C | Original VPD hPa | Stage14 VPD hPa | ERA5-Land T °C | TA−grid °C | ±6 h baseline residual median °C | MAD °C | Event−baseline °C |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| US-SP1 | 200710151730 | 11.150 | 14.025 | 5.569 | 25.547 | −14.397 | −8.480 | 6.213 | −5.918 |
| US-SP1 | 200801160800 | −8.211 | 6.148 | 0.928 | 8.173 | −16.384 | −15.679 | 3.568 | −0.705 |
| US-SP1 | 200801160830 | −4.365 | 6.597 | 1.188 | 8.720 | −13.085 | −10.575 | 2.874 | −2.509 |
| US-SP1 | 200802030800 | −3.613 | 4.717 | 0.047 | 13.005 | −16.618 | −14.651 | 2.767 | −1.968 |
| US-SRG | 201903191200 | 0.718 | 17.133 | 4.660 | 18.865 | −18.147 | 6.778 | 0.837 | −24.925 |
| US-Seg | 201612271800 | 0.015 | 7.037 | 2.631 | 6.689 | −6.674 | −3.923 | 2.224 | −2.751 |

### Interpreting the original 30-minute context (observations vs hypotheses)

**US-SP1 October 2007:** original TA=11.251°C QC0 at 17:00, 11.150°C QC0 at 17:30, **23.220°C QC0 at 18:00** (an increase of **12.070°C/30 min**). Through 15:30–17:30 the tower is 14–16°C colder than gridded T, then 18:00–19:30 is only ~1.6–2.2°C colder. This is suggestive of a **temperature regime/source discontinuity**, not proof which segment is wrong. Examine original ancillary TA channels and native QC/source lineage, not a one-point interpolation.

**US-SP1 January/February 2008:** 2008-01-16 06:00–08:30 original QC0 TA remains ~−11.1 to −4.4°C while ERA5-Land is ~8–9°C. There is a *multi-hour* residual and continuous warming through 10:00. 2008-02-03 06:00–08:00 tower T remains ~−6.6 to −3.6°C while grid is ~12.7–13.0°C and also warms subsequently. In each event the full-window residual outlier is small relative to the sustained deviation. A single-point replacement is **not defensible** solely from the grid discrepancy. Investigate clock/sensor/source metadata, geographic context and other measured meteorological channels.

**US-SRG March 2019:** 11:30 **19.668°C QC2**; 12:00 **0.718°C QC0**; 12:30 **20.605°C QC2**. Largest local excursion: −18.950°C then +19.887°C in consecutive half-hours; independent ERA5-Land at 12:00 is **18.865°C**. Strong **candidate** single-point anomaly, but surrounding QC2 values are not independently verified raw tower readings (possibly ERA-derived fills); *do not claim two native QC0 anchors*. Check raw met channel / flag and do a sensitivity branch only if justified.

**US-Seg December 2016:** 17:30 **4.332°C QC0**, 18:00 **0.015°C QC0** (−4.317°C/30 min), 18:30 **−0.512°C QC0**, 19:00 **−0.863°C QC0**, continuing near/below 0°C. This is a cooling sequence rather than a uniquely isolated spike; cannot infer invalid TA solely from ERA5-Land mismatch. Verify local weather/meteorological features and source provenance.

## Scientific decision gates

- **0/6 official new science HOLDs cleared.** The two US-SP1 2000-10-09 Stage15 alternatives remain held too (**8/8** original temperature disputes still held).
- **US-Syv** inherited 606 science HOLDs and 10 skipped Stage07 ERA jump endpoints remain deferred.
- The Stage14 VPD/RH physics closure does not validate original temperature. The Stage15 isolated alternative is not a production temperature update.
- No original/derived source writes, Post-v5 approval, DATM, CIME, Slurm or spinup occurred in Stage17.
- **Next scientific check (Stage18):** audit *native* temperature/QC/ERA-or-other source lineage and 1–2 day neighbourhood transitions for the six times; do not infer valid independent observations from QC2. Only afterwards assess whether separate temperature sensitivity branches are scientifically supportable.

## Output confirmation

```text
STAGE17 RESULT: 6/6 ORIGINAL QC0 T CONFLICTS DIAGNOSED, 0 OFFICIAL SCIENCE HOLDS CLEARED
STAGE17 DEFERRED: two Stage15 temperature trial times remain science HOLD; US-Syv 606 old HOLDs + 10 ERA jump skips
STAGE17 READ ONLY: NO SOURCE/FLUXMET/DATM/CIME/SLURM WRITES OR CDS REQUESTS
```

Stage17 command/source: [pinned operator instructions](STAGE17_REMAINING_SIX_TEMPERATURE_QC_READONLY_2026-10-25.md).

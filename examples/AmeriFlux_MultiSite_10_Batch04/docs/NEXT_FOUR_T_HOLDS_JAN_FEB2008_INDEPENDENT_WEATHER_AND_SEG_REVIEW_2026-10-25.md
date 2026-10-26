# Batch04 — remaining four original T science holds: 2008 US-SP1 independent airport weather evidence and US-Seg preserve T

**Date:** 2026-10-25. **Input evidence:** Exact **operator-returned read-only** [four-HOLD review script](../scripts/manual_review/next_four_temperature_holds_science_review_readonly.py) output, showing original US-SP1 `368208` HH, SHA `d5fe39d617e1e7964542cf3d3f8f068e00b028a37e4db7814b77c6cd813e1963`, and US-Seg `333120` HH, SHA `2fc2fc1c846749070f62c981b0f71789bdc9dae7585eeb0b0f30455a9e88034d`, with **all four science hold original `TA_F_QC=0`**.

## Scientific triage result

**US-SP1, 2008-01-16 08:00/08:30, and 2008-02-03 08:00:** **need an explicit treatment decision at the continuous-interval scale, NOT automatic isolated three-cell linear interpolation**. These original readings fit very cold extended low-TA sequences relative to processed source `TA_ERA`, including two Jan and four Feb separate consecutive source temperature discrepancy runs. Full local-standard context:

| Window | Original TA_F vs processed TA_ERA screen | Exact longest-run extent | Highlight |
| --- | --- | --- | --- |
| 2008-01-15 17:00 to Jan17 14:00, 91 HH | mean ΔT = −13.989°C; min ΔT = −20.067°C | 2008-01-15 19:30→Jan16 08:30: **27 HH/13.5h**; Jan16 15:30→Jan17 13:00: **44 HH/22h** | Jan16 07:00 TA=−11.144°C; Jan16 08:00 TA=−8.211°C QC0 VPD=6.148 hPa > es(T)≈3.30 hPa; 08:30 TA=−4.365°C QC0 VPD=6.597 hPa > es(T)≈4.43 hPa |
| 2008-02-02 18:00 to Feb04 12:00, 85 HH | mean ΔT=−8.508°C; min ΔT=−17.751°C | 2008-02-02 23:30→Feb03 08:30: **19 HH/9.5h**; Feb03 23:30→Feb04 01:30: 5 HH; Feb04 03:30→06:30: 7 HH | Feb03 07:30 TA=−6.588°C and 08:00 TA=−3.613°C QC0; temperature matches processed ERA near Feb03 15:30–16:30, implying variable site−ERA difference over the day |

These original VPD physical failures at focal timestamps were **already** addressed by Stage14's **RH and VPD-only** research candidates without changing original temperature, so **do not rerun Stage14**. [Stage14 eight corrected VPD ledger](STAGE14_VERIFIED_8_HUMIDITY_CLOSURE_QC0_T_HOLDS_2026-10-25.md).

### Independent *observed*, off-tower meteorological checks

A nearby independent observing station, Gainesville Regional Airport (station `GHCND:USW00012816`, altitude 40.7 m; US-SP1 tower reported altitude 50 m), has the following **2008 daily observed minimum temperatures**. These observations are **not the same sensor, terrain, native HH or source clock** as US-SP1, but refute the notion that the extraordinarily cold tower values were simply an ordinary broad regional frost during the checked dates.

| Local date | US-SP1 original extreme | Gainesville Regional Airport observed daily min | Source |
| --- | ---: | ---: | --- |
| 2008-01-16 | **−11.144°C** | **44°F = +6.67°C** | National Weather Service historical preliminary Gainesville CF6 climate report, **Jan16 63°F high / 44°F low**: https://mesonet.agron.iastate.edu/wx/afos/p.php?e=200801300800&pil=CF6GNV |
| 2008-02-03 | **−6.588°C** | **49°F = +9.44°C** | Gainesville airport daily weather table: https://www.extremeweatherwatch.com/cities/gainesville/day/february-3, 2008 line **79°F high / 49°F low** |

The Jan16 FAA/NWS airport low **+6.67°C** is ~**17.81°C warmer** than the most extreme original tower 07:00 **−11.144°C**. On Feb03 airport observed min **+9.44°C** is ~**16.03°C warmer** than the original tower 07:30 **−6.588°C**. The airport/flux tower are different locations separated by several km and measured daily/half-hour values are not timestamp-matched; these comparisons **strongly suggest** a tower source/provenance problem but **do not reveal the exact invalid HH boundaries, nighttime lapse/microclimate differences, or unbiased replacement temperatures**.

**Recommended operator scientific decision:** if choosing to substitute the temperature, treat the **whole suspect Jan/Feb multi-hour episodes** as an independently documented **ERA5-Land / independent nearby observation** sensitivity scenario, after independently selecting the bad intervals and checking calibration on truly healthy tower times. The original extreme nighttime series may reflect a processing/sensor issue; **do not apply Oct 2007's 06:30–17:30 daytime rule to Jan/Feb 2008**. Jan15–17 shows no clean within-window same-day ERA residual baseline; Feb03 has some near-zero afternoon residuals but strongly negative pre-dawn residuals. The 2007 −2°C mean bias is not transferable without evidence.

**US-Seg, 2016-12-27 18:00:** **do not change original tower T without a new independent temperature observation**. Source TA at 18:00 is 0.015°C, 18:30 −0.512°C, 19:00 −0.863°C; continued overnight freezing with 03:00 Dec28 −3.948°C, while processed `TA_ERA` eventually also falls below zero at Dec28 04:00. Original 18:00 VPD was **7.037 hPa**, exceeding es(0.015°C)≈**6.119 hPa**; Stage14 already created the humidity-only alternative **2.63121106028 hPa at unchanged TA 0.015°C**, with retained original source temperature/QC, US-Seg full derived Stage14 CSV SHA `22db08e969883cb7f5bc0dd7c3b161c60582c6fe6fe8715a0c9e23598cafbea6`. This is a plausible wintertime subfreezing trajectory for a ~1596 m NM tower, but regional context alone is **not conclusive source proof**. **No new Seg candidate needs to be written in this stage**, and retain original science source HOLD pending signoff.

## Current workflow / what not to repeat

Already operator-verified **US-SP1 Oct2007 137-HH six-day repaired research candidate** sits at:

```text
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_sp1_six_day_bias_adjusted_research_not_approved/candidate_20261025T231828Z_ed7de7ac
US-SP1 full research CSV SHA256: 357a0c89892365e41e1b932663953fcff33487a2cbf6171ba3b9347b7482a9b0
```

The ten-site research manifest preserves the previous **US-SP1 Oct2000 two-HH ERA5-Land trial** and **US-SRG Mar2019 one-HH ERA-flank trial**. Do **not re-run** the 137-HH repair or overwrite those full source products. The original 8 science HOLDs and US-Syv **606+10** remain logged in the **original scientific ledger** regardless of separate trial alternative status. No official Post-v5/DATM/CIME/Slurm/spinup release.

**Required remaining human judgement: ONE decision on 2008 US-SP1 episodes**: whether the investigator authorises a **separate ERA5-Land/FLUXNET TA_ERA based *extended winter-episode sensitivity trial*** with explicit interval selection and uncertainty/provenance, or wishes to **preserve original tower T pending raw instrument / adjacent SP2/SP3 BASE comparisons**. The evidence now excludes treating the three HOLD timestamps as isolated point outliers without examining the full suspect 2008 periods. No additional human judgement needed to keep US-Seg temperature provisionally unchanged and reuse its already available Stage14 humidity-only science candidate.


# US-Me6 original 2017-07-04 QC1 MDS VPD right boundary — operator-verified 2026-10-25

**Source:** IRIDIS6 operator's SHA-verified, read-only original FLUXMET/native paired ERA inspection. Checks successfully validated original Stage07 input SHA manifests, Stage12y report hashes, and Stage12g research-only shadow SHA. This was a **one-off read-only inspection**, not a new Stage12z automated report.

The original tower `TA_F_QC=0` and source `VPD_F_QC=1` at each of four original half-hours; every `VPD_F` equals `VPD_F_MDS`, with `VPD_F_MDS_QC=1` (high-confidence MDS gapfill, NOT directly measured humidity). Source-vs-temperature water saturation computed from `es_water(T)=6.112*exp(17.67*T/(T+243.5))`; original implied `RH=100*(es(T)-VPD)/es(T)`.

| Local native time 2017-07-04 | TA_F °C, measured QC0 | Original MDS VPD hPa QC1 | Original MDS VPD implied RH % | Paired native ERA TA °C | Paired ERA VPD hPa | Paired ERA implied RH % | RH-transferred ERA VPD at original tower T hPa | Original RH physical? |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 06:30 | 11.95 | 15.816 | -13.22 | 9.955 | 3.481 | 71.55 | 3.974495 | No |
| 07:00 | 15.01 | 17.597 | -3.20 | 10.795 | 3.912 | 69.77 | 5.154795 | No |
| 07:30 | 17.33 | 20.445 | -3.40 | 14.417 | 7.757 | 52.73 | 9.345609 | No |
| **08:00** | **18.96** | **21.391** | **2.35** | **18.039** | **11.603** | **43.88** | **12.292544** | Technically yes, but caution |

08:00 source MDS VPD is **9.098456 hPa** greater than ERA-RH-transferred VPD at original measured tower T. The original MDS value passes `0<=VPD<es_water(T)` merely because `es_water(18.96°C)≈21.905274 hPa`, leaving implied actual vapour pressure ≈0.514274 hPa / RH≈2.35%. This is physically possible but climatologically suspicious and unverified, not evidence to edit it.

The original-source search found **ZERO source QC0 VPD+QC0 T physically-valid reference records in the full ±24h centered 2017-07-04 07:30**. Therefore 08:00 is NOT an independent tower observation supporting the Stage12g held-source transition. Under the Stage12y sealed existing research-shadow values 06:30=3.974495 hPa, 07:00=missing, 07:30=missing, 08:00=21.391 hPa; the new hypothetical 07:00 and 07:30 companion-source choices create adjacent true native 30min jumps 1.180300, **4.190815**, **12.045391 hPa**. The 4 hPa original scientific guard fails for the last two actual 30min transitions.

**Science decision:** retain 07:00 and 07:30 original HOLDs; separately flag source-original **08:00 QC1 MDS** as a manual-audit right boundary (not a verified QC0 humidity measurement). Do NOT automatically replace or remove 08:00 from Stage12g. Do NOT relax original 4 hPa per 30min guard, use time shifts as fact, or declare any companion ERA/RH source observational truth. All original 86 original science-hold records, 233 older physical holds, source native time, site tower T/P, model forcing, Post-v5/DATM/spinup remain untouched.

**Next best diagnostic:** read-only examine original 08:00 `TA_F_MDS`, MDS QC, its original `VPD_F_MDS` versus ERA and Stage12c/d/e/g VPD lineage, ±6h daytime and full-day behavior; find nearest genuine physically valid QC0 VPD reference **outside** ±24h (report absolute time separation, no interpolating). If an alternate temperature hypothesis arises, test independently and never adjust native clocks automatically.

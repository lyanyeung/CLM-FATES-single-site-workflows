# Batch04 after Stage21 — verified station contacts and native temperature evidence requests

**Status: research/data-contact preparation ONLY. No messages sent and no AmeriFlux BASE or unpublished raw TA files downloaded or independently verified.** Stage21 [verified 3 × 16 FLUXNET CSV headers](STAGE21_VERIFIED_ORIGINAL_TEMPERATURE_SOURCE_COVERAGE_2026-10-25.md) and detected **zero separate native sensor-temperature-channel candidates**. STOP repetitive FLUXNET-vs-ERA internal-only QC. Original `TA_F_QC=0` is a processing provenance designation, not a guarantee that a suspicious measurement was physically correct; `TA_F_QC=2` indicates ERA-derived fill, not an independent observed temperature.

The official AmeriFlux site pages below list dataset creator/site team contacts. **These are publicly listed contacts as of a site-page check on 2026-10-25; do not assume a reply or permission to redistribute raw data.**

| Site | Official site contact(s) | Public site page | What to request |
| --- | --- | --- | --- |
| US-SP1, Slashpine-Austin Cary | Rosvel Bracho (`rbracho@ufl.edu`), Timothy Martin (`tamartin@ufl.edu`) | https://ameriflux.lbl.gov/sites/siteinfo/US-SP1 | 2000-10-09 two isolated trial points; Oct 15–18, 2007 recurring daytime cold-vs-ERA segments; Jan 15–17 and Feb 2–3, 2008 sustained cold-vs-ERA periods |
| US-SRG, Santa Rita Grassland | Russell Scott (`russ.scott@ars.usda.gov`) | https://ameriflux.lbl.gov/sites/siteinfo/US-SRG | Mar 19, 2019 11:00–13:30 local-standard clock, especially 12:00 raw TA=0.718°C QC0 versus TA_ERA=20.399°C; adjoining processed QC2 temperatures are not original tower measurements |
| US-Seg, Sevilleta grassland | Marcy Litvak (`mlitvak@unm.edu`); data manager Kai Del Regno (`kaidelregno@unm.edu`) | https://ameriflux.lbl.gov/sites/siteinfo/US-Seg | Dec 27, 2016 16:00–20:00 local-standard clock, including the 18:00 QC0 0.015°C and ongoing cooling below 0°C |

**Dataset distinction:** the inspected version is the AmeriFlux **FLUXNET v1.3_r1** product (processed FLUXMET/ERA5/BIF/BIFVARINFO files), not every available AmeriFlux **BASE** product or raw logger file. Official AmeriFlux station pages advertise BASE products for all three stations:
- https://doi.org/10.17190/AMF/1246100 (US-SP1 BASE)
- https://doi.org/10.17190/AMF/1246154 (US-SRG BASE)
- https://doi.org/10.17190/AMF/1246124 (US-Seg BASE)

Check whether relevant BASE meteorology variables or unpublished tower logger channels are available **without assuming that a BASE value automatically gives independent validation**. Source-side QA/QC, original sampling time and native instrumentation are still needed.

## Evidence specification to request

For each target station ask for:
1. **Original observed air-temperature time series** at native 30-min or finer resolution, including raw site-specific variable name/channel(s), sensor ID, height above ground/canopy, logger timezone and UTC offset, and whether DST was ever applied. Confirm whether original TA time series were computed from multiple channels.
2. **Original source-side QC flags and raw/logger audit trail** for affected timestamps, including any anomalous, physically impossible or saturated measurements, and whether QC=0 in the FLUXNET/ONEFlux product came from instrument data, an aggregation choice, or a post-processing/crosswalk step.
3. **Maintenance, sensor relocation/calibration, duplicate data, clock changes, and site metadata** around the affected episodes.
4. **Independent humidity/VPD/pressure values** and sensor heights where available so the physically inconsistent original VPD-vs-TA pair can be assessed using contemporaneous instruments rather than ERA data alone.
5. If original data cannot be shared, request an **operator's scientific determination** for the exact timestamp(s), and whether the research team recommends a corrected measurement, gap flag, or retention of native QC0. Ask about redistribution/citation/data-use restrictions.

## Prepared site-specific requests — NOT SENT

### US-SP1 — proposed email

**To:** rbracho@ufl.edu  
**Cc:** tamartin@ufl.edu  
**Subject:** US-SP1 original tower air-temperature/QC provenance for selected 2000, 2007 and 2008 periods

Dear Dr Bracho and Dr Martin,

I am evaluating CLM-FATES simulations against AmeriFlux US-SP1 and conducting source-provenance checks on the FLUXNET v1.3_r1 meteorological inputs. We are retaining the original tower temperature and have not changed any production forcing.

The supplied FLUXNET `TA_F` and `TA_F_MDS` both carry QC0 during several periods with large differences relative to `TA_ERA`. Examples include 15–18 October 2007, with recurring daytime differences greater than 10°C and an 11.150°C to 23.220°C half-hour transition on 15 October (17:30–18:00 local standard time); 15–17 January 2008 and 2–3 February 2008, with multi-hour cool periods; and two held half-hours on 9 October 2000 (18:00 and 18:30).

Might you be able to advise whether original sensor-level TA (and, if available, humidity/VPD) logger measurements, original QC flags, sensor height and instrument/clock metadata are available for these dates, or whether the FLUXNET data were derived from other channels? We are particularly interested in whether these discrepancies reflect local meteorology, instrumentation or data-processing issues. Even a source-side judgement would be useful if raw data cannot be shared.

We would follow any applicable data-sharing and citation requirements and would not redistribute raw records without permission. Thank you for your help.

Best regards,

### US-SRG — proposed email

**To:** russ.scott@ars.usda.gov  
**Subject:** US-SRG 19 March 2019, 12:00 — raw tower TA/QC provenance question

Dear Dr Scott,

I am assessing CLM-FATES forcing inputs from AmeriFlux US-SRG, using the FLUXNET v1.3_r1 meteorological product. At 12:00 local standard time on 19 March 2019, `TA_F=0.718°C` is marked QC0 whereas the product `TA_ERA=20.399°C`. Immediately adjacent `TA_F` values are QC2 ERA-derived substitutions, not independently measured tower observations. The original VPD paired with 0.718°C is also physically inconsistent.

Could you advise whether native tower air-temperature measurements and source QC, ideally from 11:00–13:30 on this date, are available, and whether the 12:00 QC0 reading is known to be valid or erroneous? Sensor height, instrument maintenance and logger timestamp conventions would also help. We have not modified the original forcing, and would use any supplied data only under the relevant permissions.

Best regards,

### US-Seg — proposed email

**To:** mlitvak@unm.edu  
**Cc:** kaidelregno@unm.edu  
**Subject:** US-Seg original air-temperature observations during 27 December 2016 evening cooling

Dear Dr Litvak and Ms Del Regno,

I am evaluating CLM-FATES forcing for AmeriFlux US-Seg and am checking the original observation provenance in the FLUXNET v1.3_r1 product. On 27 December 2016 at 18:00 local standard time, `TA_F=0.015°C` is marked QC0 and continues cooling below 0°C afterwards, while `TA_ERA` is substantially warmer and the original VPD/temperature pairing is physically inconsistent. Unlike an isolated spike, the original tower sequence appears to be part of a cooling period.

Would you be able to confirm the original air-temperature sensor/QC data, measurement height, logger clock, and any available independent humidity measurements for 16:00–20:00 on that day? We are not planning to overwrite QC0 observations without stronger evidence. We would respect any data-sharing restrictions and cite the source appropriately.

Best regards,

## Science and operations release gate

- **All eight** original tower-temperature science HOLDs remain unresolved: US-SP1 six HH (including two 2000 trial-only alternatives), US-SRG one HH, US-Seg one HH.
- **US-Syv** 606 inherited scientific HOLDs and 10 skipped Stage07 ERA end-point cases remain deferred.
- Do not interpret a **contact recommendation** as a message sent, data received, permission granted or a scientifically validated correction.
- **No Post-v5 approval, no DATM/CIME forcing release and no CLM-FATES spinup execution** from this evidence.

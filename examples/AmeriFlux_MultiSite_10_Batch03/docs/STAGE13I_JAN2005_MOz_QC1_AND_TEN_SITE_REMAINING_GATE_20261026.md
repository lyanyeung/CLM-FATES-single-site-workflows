# Batch03 Stage13i verified source QC1 science gate and ten-site completion blocker summary — 2026-10-26

> **2026-10-26 OPERATOR CONDITIONAL APPROVAL (Stage13j):** The prior manual decision needed for US-MOz was granted for two exactly bounded QC1 events (27+40=67 native halfhours), conditional upon signed CDS ERA5-Land cross-product verification, published BIF -6h clock independently validated with measured QC0 analogues, measured QC0 on both original event sides, original release time/QC, and humidity/T/QBOT physics plus event edges. This is NOT a blanket acceptance of other original source QC1; the Jan09 negative-bias event remains held. **Do not claim the new 67 rows were actually changed yet.** The [scoped Stage13j decision](../decisions/STAGE13J_OPERATOR_CONDITIONAL_US_MOz_2005_TWO_QC1_EVENTS_20261026.json), [fail-closed Stage13j scientific script](../scripts/stage13/13j_conditional_two_US_MOz_QC1_ERA5Land_SCOPED.py) and [BIF/ERA5-Land runbook](STAGE13J_TWO_MOz_QC1_CONDITIONAL_APPROVAL_AND_CDS_ERA5LAND_20261026.md) are committed on GitHub. US-MOz original uploaded BIF: LOCATION_LAT 38.7441, LOCATION_LONG -92.2000 and UTC_OFFSET -6.00; height of canopy=24.2m is not ZBOT. Stage13g original remains immutable, Postv5/DATM/spinup NOT approved. 

## Verified Stage13i from IRIDIS6 user's 18:29 log

Stage13i original pinned source and all preflight/readonly run checks **PASSED**, with sealed report at

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage13i_US_MOz_Jan2005_QC1_multiday_episode_20261026T182923Z_bc9d9b34`

The **US-MOz Stage13g full 315,360 half-hour / 18-year science shadow** is present and retained SHA `f6b740491fd3b7d9b66fe9bc33c20586db6124442b93df72273410d761bd6b27`. Previously signed six Stage07 temperature/VPD edits and five Stage13g native time repairs remain approved. Stage13i is **source/ERA comparison only**, 0 additional forcing edits, 0 Post-v5/DATM/Spinup approvals.

Stage13i year-2005 original tower `TA_F_QC=1` count **361**, paired ERA temperature discrepancy >5C **118**, >8C **70**. Original 2005-01-06: 42 QC1 T half-hours, six QC2. 40 QC1 T slots differ from ERA by >5C, 37 by >8C. Exactly one Jan6 Stage13g source QC1 temperature at 10:00 had *already* been separately repaired and authorised; 41 Jan6 source QC1 temperatures remain unmodified.

Critically, there are TWO unbroken original gapfilled-temperature QC1 runs crossing Jan6:

- 2005-01-03 12:30 – 2005-01-06 09:00: **138 halfhours (69h)**, 47 slots >3C discrepancy, 27 >5C and 16 >8C. Importantly most of the 138 have **no strong measured-vs-ERA disagreement**; do not replace the whole 138 automatically.
- 2005-01-06 13:00 – 2005-01-09 10:00: **139 halfhours (69.5h)**, 74 slots >3C, 55 >5C, 35 >8C. Includes both positive and negative source-vs-ERA discrepancies near Jan9; do not assume all towers are anomalously warm.

There are additional QC1 runs 2005-01-09 11:30–12:30 (3HH) and 13:30–2005-01-10 09:00 (40HH), with some **negative** tower-vs-ERA differences reaching −18.14C.

At thresholds >3,5,8,10C, run boundaries change materially. For example Jan05 10:30–Jan06 09:00 (46HH) at >3C; Jan05 20:00–Jan06 09:00 (27HH) at >5C; Jan06 01:30–09:00 (16HH) at >8C; Jan06 04:00–09:00 (11HH) at >10C. These are **screening thresholds, not the true start of an invalid gapfill regime**. Stage13i confirms all original paired ERA TA/VPD candidates over listed QC1 multiday runs pass a basic RH/water physics screen (but not a station clock, independent provenance, or external reference validation). Paired ERA is only a companion; a source QC2 point exactly equal to ERA is not independent confirmation. DO NOT silently blanket-replace QC1 source T/VPD by a threshold or entire QC1 run.

**Science decision needed:** operator may approve a tightly scoped, evidence-screened study (shadow forcing only) to repair demonstrably contaminated source QC1 T+VPD episodes with companion ERA paired T/RH if (and only if) independent source provenance/calendar clock checks and original QC0 anchor continuity pass. Failures and conflicting negative/positive cases retain explicit HOLD. This authorization has not been given and **no application** is made by this note.

## Latest ten-site validated numerical source status

Source: [Stage12ai last verified ten-site all-input census](STAGE12AI_20261026_TEN_SITE_STATUS_AFTER_KON_12AH.md), 2026-10-26 03:00 UTC, updated conceptually by Stage13a/13g for the three numerically complete stations. These are **last verified counts, not a live IRIDIS6 rerun**.

| Site | Most recently verified missing humidity half-hours | Other barrier |
| --- | ---: | --- |
| US-MOz | 0 | Stage13g 9 new repairs PASS; multi-day Jan2005 original QC1 source provenance HOLD; ZBOT measurement-height and implementation audit; 50-site recommended PFT DBF90/ENF10 |
| US-Mpj | 0 | Stage13b source 5 VPD manual reviews; 50-site recommended PFT ENF60/C4 20/bare20; source/production gates |
| US-NC2 | 0 | Stage13b source 13 VPD manual reviews; original 2025 clock/ERA-source hold; PFT ENF90/DBF10 |
| US-Kon | 389 | Stage12am source 57 reviewed companion ERA RH events: 55 plausible isolated centers but connected neighborhood science and 2 hard T conflicts; other gaps |
| US-MMS | 16 | gridded-source and original science holds |
| US-Me6 | 65 | Stage12ac 5HH humidity accepted; remaining held source episodes and complete production QA |
| US-MtB | 2840 | high-elevation site-gridded temperature discrepancy; 4/4 bulk methods did not pass QC0 analog gate; cannot auto-fill |
| US-NR1 | 240 | 6 specific held humidity slots around previously approved 3 temperature corrections, additional source gaps |
| US-NR3 | 238 | source-year and original physics holds |
| US-Me2 | Not available | Original clock/BIF FULLSET four scientific source-metadata holds; cannot count as comparable fully assembled selected forcing |

Totals among six current incomplete numerical candidates: **3,788 humidity-missing halfhour rows**, not double counted; additional nonhumidity missing rows and one unique nonhumidity gap in NR1. Me2 lacks comparable approved source-native release clock. Original 50-site curated PFT recommendations are explicitly defined with numeric mapping/round-trip PASS; they are *model hypotheses*, and current active case/surface implementation is still not verified, not grounds for restarting PFT literature work.

**Site scientific completion / Post-v5 / DATM-ready / spinup:** none of the ten has verified production admission or a submitted model in this workflow. Numeric completeness of 3/10 is not 3/10 complete models.

### Delivery risk and completion horizon

No reliable finish date may be inferred from this progress snapshot. Even resolving US-MOz doesn't unblock MtB=2840, Kon=389, NR1=240, NR3=238, Me6=65, MMS=16, or Me2 clock. The critical path includes science-source adequacy and original time/provenance in addition to data filling. Avoid speculative multi-day or multi-week completion promises.

**Next critical scientific authorizations:** one bounded user policy for MOz Jan2005, paired ERA-RH source scoping for Kon/NR1/Me6, independent MtB source/terrain/ice humidity validation, and Me2 true clock metadata. Original tower, paired ERA, current Stage07/Stage13g and PFT remain unchanged.

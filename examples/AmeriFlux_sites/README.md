# AmeriFlux sites — CLM-FATES experiment collection

This collection keeps AmeriFlux batches separate from the existing [ICOS multi-site campaigns](../ICOS_sites/) and the [AmeriFlux US-Ha1 single-site example](../AmeriFlux_US-Ha1/).

| Batch | Sites | Current record |
| --- | ---: | --- |
| [AmeriFlux Batch 01](../AmeriFlux_MultiSite_10/) | 10 | See the batch-specific operational record and scripts |
| **[AmeriFlux Batch 02](../AmeriFlux_MultiSite_10_Batch02/)** | 10 | Stages00–10 published. Operator Stage07: 5 numeric candidates; 5 sites blocked by 4,904 unresolved humidity pairs. Stage08 sensitivity and the follow-on Post-v5 gates/runner are ready for execution. |
| **[AmeriFlux Batch 03](../AmeriFlux_MultiSite_10_Batch03/)** | 10 | Stages00–01 ready: single-connection WSL upload and recursive extraction; live transfer pending. |

Batch03 sites: US-Kon, US-Me2, US-Me6, US-MMS, US-MOz, US-Mpj, US-MtB, US-NC2, US-NR1 and US-NR3. See its [exact releases](../AmeriFlux_MultiSite_10_Batch03/sites.tsv) and [instructions](../AmeriFlux_MultiSite_10_Batch03/README.md). Later processing includes QCv5 and a separate Post-QCv5 audit before DATM or spin-up.

Batch02 sites: US-BZS, US-CMW, US-EML, US-GLE, US-Ha1, US-Ho1, US-Ho2, US-Ho3, US-ICh and US-ICt. Its [exact releases](../AmeriFlux_MultiSite_10_Batch02/sites.tsv), [operating instructions](../AmeriFlux_MultiSite_10_Batch02/README.md) and [stage scripts](../AmeriFlux_MultiSite_10_Batch02/scripts/) are maintained as a separate case under `main/examples/`.

Batch02 candidates are not approved forcing or model cases. No DATM or Slurm jobs were created for this batch. Raw tower packages and large model NetCDFs remain on local/IRIDIS storage rather than GitHub.

## Shared measurement-height metadata for ALL AmeriFlux batches

Use the versioned, **complete** user-supplied [2026-09-08 BASE Measurement Height CSV](metadata/BASE_MeasurementHeight_20260908.csv) and the [shared height candidate auditor](scripts/28_audit_shared_BASE_measurement_heights.py). This covers 40,306 source rows and 587 AmeriFlux sites. Raw upload SHA256: `1c1e4171d295406a13d503f877b58661a651c88ffb6f0b6ec498f56bb1fcec5a`.

The older Batch01 Stage26/27 BIF-height scripts were retired and deleted; they assumed FLUXNET BIF `VAR_INFO_*` fields that the ten AmeriFlux BIF files do not contain. **BIF coordinates remain valid as a separate workflow.**

For any batch, supply that batch's `sites.tsv` via `--sites-tsv`. All candidate TA/WS heights retain their original variable names, missing/partial dates, instruments and comments. Do not automatically map an indexed TA level, wind height or EC measurement height to model `ZBOT`. Create a new separately versioned snapshot when the monthly BASE metadata changes; do not overwrite this source file. The numerical QC and meteorological science gates are also separate from the height source audit.

## Stage30 — open height-science decisions

[Stage30 read-only mapping/date audit](scripts/30_audit_BASE_height_mapping_gaps_and_date_windows.py) follows Stage29. Batch01 has 5 unapproved static candidates, 3 dynamic candidates with partial dates, and 2 unresolved multi-layer TA arrays (CA-Cbo, CA-Man). Stage30 writes only candidate evidence, blocked sensor alternatives, uncertain date windows, and blank approval decisions. It does not equate `TA_PI_F` with FLUXNET `TA_F` or create ZBOT/DATM. Scientific approval remains pending.

## Stage31 — user-selected static/dynamic height policy, provisional scenarios

The user selected the same practical policy as the earlier ICOS/FLUXNET work: use **dynamic TA measurement heights when changes are documented**, otherwise a **static single TA measurement height**, and apply the first known TA height backward over earlier forcing years **as an explicitly flagged model assumption**. [Stage31](scripts/31_build_provisional_ZBOT_policy_scenarios.py) implements this rule for independently auditable source candidates. It models incomplete month/year change dates as two bracketing scenarios (earliest vs upper-bound effective date) and reports the number of affected half-hours. It **does not** silently fix a date or claim sensor matching to `TA_F` has been verified. Multi-layer sites CA-Cbo and CA-Man remain blocked pending specific TA-level mapping. This produces only JSON/CSV policies and comparisons, not a ZBOT NetCDF or a model job. Scientific sign-off is still required before final DATM use.

## Stage32 unresolved scientific issue — multi-layer TA heights in CA-Cbo and CA-Man (22 October 2026)

**Status: READ-ONLY AUDIT COMPLETE; SENSOR-TO-FLUXNET MAPPING UNRESOLVED; ZBOT NOT APPROVED.** The fixed [Stage32 sensor-audit script](scripts/32_review_CA_Cbo_CA_Man_TA_mapping_and_dates.py) successfully ran on IRIDIS6 using the pinned [BASE Measurement Height 2026-09-08 snapshot](metadata/BASE_MeasurementHeight_20260908.csv), SHA256 `1c1e4171d295406a13d503f877b58661a651c88ffb6f0b6ec498f56bb1fcec5a`. The earlier Stage32 draft contained three misspelled `ashheight()` calls; GitHub commit `d2b976bd3fb0d0ebe41061623abc04323399067c` changed them to `asheight()`. The corrected audit passed.

| Site | BASE TA sensor-height options (m) | WS sensor-height options (m) | Resolved FLUXNET `TA_F` mapping? |
| --- | --- | --- | --- |
| **CA-Cbo** | **1.7, 3.3, 6.3, 10.4, 13.5, 16.5, 19.6, 22.6, 25.7, 29, 33, 34.8, 40.7, 42** (**14 options**) | 33, 42.7, 44 | **NO — BLOCKED** |
| **CA-Man** | **2, 10, 30** (**3 options**) | 29 | **NO — BLOCKED** |

**Why this is a real scientific ambiguity:** the FLUXNET package supplies `TA_F` forcing, but BASE enumerates *several* TA measurement sensors at different heights. The presence of an upper-canopy sensor, the numerically highest TA level (e.g. CA-Cbo 42 m), or closeness to an anemometer (e.g. CA-Man 30 m vs WS 29 m) **does not prove which specific TA sensor the FLUXNET `TA_F` product uses**. Similarly, `TA_PI_F` / indexed BASE names are candidate source mappings, not a demonstrated crosswalk. Do **not** infer ZBOT from EC flux measurement height, canopy height, WS height, or a default 2 m. Treat these two sites as *missing a validated source-to-forcing mapping*, **not** as lacking any measurements. Do not classify one of the options as static ZBOT until the source layer is identified and its date coverage assessed.

**Reproducibility:** completed IRIDIS6 report:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports/stage32_CA_Cbo_CA_Man_height_decision_20261022T023048634999Z/`

Reports: `01_all_original_TA_WS_sensor_metadata.csv` (each original TA and WS entry, including instrument and comments); `02_suggested_sensor_height_evidence_priorities_NOT_APPROVED.csv` (investigation priority only); and `03_blank_scientific_decision_template.csv` (deliberately **no approved choices**). Stage32 summary: **2 sites, 17 TA height options, 0 approved**.

**Required next evidence:** site documentation, sensor/instrument logs and/or processing metadata that explicitly connects the published FLUXNET `TA_F` meteorological series with the applicable BASE TA variable and sensor height, including any instrument relocations. Review whether the source documents one level or a combined/derived temperature product. If the mapping remains unknown, explicitly document a model sensitivity/proxy height only as a **separate provisional assumption**, not a verified measurement level; do not silently remove the site or assign a number as fact.

**Policy for other sites:** Stage31 currently has **5 static + 3 dynamic height candidates** for the other 8 sites. The user-selected approach is static where only one applicable TA level is documented, dynamic when dated height changes are documented, and first-known-height extrapolation for earlier forcing years **labelled as an assumption**. Three dynamic stations have unresolved date precision: CA-TP1 **4,416**, CA-TP3 **17,520**, US-Aud **1,440** half-hours differ between earliest/latest event-date scenarios; these counts are date-assignment uncertainty, not observed meteorological errors. Existing 8 candidates still require the source-to-`TA_F` mapping and date-policy review. **No site has a scientifically approved production DATM/ZBOT as a result of these audits.** Meteorological Stage25 science review and land-cover/PFT checks also remain independent gates before production spin-up.

## Stage34 — use actual EC-tower vegetation as FATES ecological target (user policy)

**Scientific policy:** For every AmeriFlux tower, official site-level vegetation/ecological information is the reference for deciding relevant FATES PFTs. A coarse-grid CTSM `PCT_NAT_PFT` majority must **not** become the EC tower's FATES PFT automatically. Source evidence for Batch01 is stored in [the ten-site tower-vegetation table](metadata/Batch01_tower_vegetation_evidence_20261022.tsv), including site history, broad functional type and outstanding uncertainties. Metadata are an **initial evidence ledger**, not a complete species/footprint validation.

The reusable [Stage34 EC-to-FATES mapping gate](scripts/34_ec_tower_vegetation_to_FATES_pft_gate.py) uses the tower ledger and **the actual existing FATES JSON paramfile supplied by `--paramfile`** to list exact parameter-file PFT names and make strictly provisional textual candidate suggestions. Run `--check` then `--audit`. It writes a scientific decision CSV to a new reports directory **without editing model files**. Without an actual paramfile, the output must explicitly retain the mapping as unavailable; no fabricated PFT numbers or names.

**Important limitations:** Forest/grassland IGBP labels do not determine exact ecological PFTs; FATES cold starts may allow several PFTs, and the actual viable PFT set depends on FATES parameters, biogeography/competition, crop-landunit constraints and initialization choices. Some sites have plantation establishment or disturbance histories (e.g., CA-TP1 white pine planted 2002, CA-TP3 planted 1974, CA-TP4 planted 1939) relevant to model initialization. Do not confuse site-level vegetation *target*, the CLM host surface fractions, and the FATES actual initialized PFTs. **Setting FATES occurs only in a separate versioned case-configuration stage after reviewing the actual case and paramfile, never in Stage34.** Until then ecological production gate remains HOLD.

## Stage37 — EC tower PFT percentage evidence search, tiered source policy (22 October 2026)

[Batch01 ten-site source-priority ledger](metadata/Batch01_EC_PFT_evidence_priority_review_20261022.tsv) records the current site-by-site status and next source to retrieve, following this **strict hierarchy**: **(1)** site/tower footprint-representative field inventory or published composition with a stated measurement basis, **(2)** footprint-relevant high-resolution cover / forest species mapping, **(3)** original 2000 CTSM point surface *only as a last-resort model assumption*. Never report (2) or (3) as observed EC-tower vegetation percentages.

Current **numeric evidence exists for 4/10 sites**: CA-Cbo has *stem-count* broadleaf/conifer proportions (approximately 81%/19%; not canopy area/biomass), and CA-TP1/3/4 have published *stand tree composition* figures (100% needleleaf; ~99% needleleaf/1% deciduous broadleaf; ~93% needleleaf/7% broadleaf, respectively), but their published percentage denominator/footprint suitability still needs independent verification. **Six remain without defensible tower-footprint PFT percentages:** BR-Ma2, CA-Ca3, CA-LP1, CA-Man, US-Aud, US-Bar. Not finding percentages in ten FLUXNET BIF files (Stage36 BIF SPP hits=0) does not establish that separate AmeriFlux BADM, biometric datasets or papers lack such information.

Priority-1 leads include NASA BOREAS NSA-OBS tree plots for CA-Man, Bartlett Experimental Forest tree plots for US-Bar, site inventories for Campbell River CA-Ca3 and bark-beetle affected CA-LP1, K34 Manaus inventory for BR-Ma2, and footprint-relevant Audubon grass C3/C4 vegetation plots for US-Aud. If these cannot produce usable percentages, evaluate spatially and temporally appropriate species-cover mapping (e.g. Canadian SCANFI products) against the tower footprint, not the entire coarse grid. **No FATES PFT percentage, initial cohort carbon, seed fraction, or NetCDF has been set or approved.**

## Stage37 v2 — quantitative tower PFT evidence update

[Ten-site PFT percentage evidence v2](metadata/Batch01_EC_PFT_percentage_status_v2_20261022.tsv) expands the research literature inventory. **7/10** sites have published quantitative tree species, stand tree type or overstory basal-area composition: CA-Ca3, CA-Cbo, CA-Man, CA-TP1, CA-TP3, CA-TP4, US-Bar. All percentages are tagged with their denominator and time/spatial scope; none is an approved FATES cohort, seed, biomass or land-area allocation. **US-Aud** has a published site-model *70% C4 grass / 30% bare soil* configuration, specifically **not** an independently measured EC-footprint percentage. **BR-Ma2 and CA-LP1** still lack usable verified numerical species composition. Do not fill these missing cells with 100% by assumption. CA-Man's ~99% black spruce refers to overstory basal area, not C3/C4 or whole land area. US-Bar's published composition has an unresolved minor remainder and unclear percentage denominator. Preserve spatial and year differences when deciding whether literature observations are transportable to a forcing period. Apply prioritized site inventory/footprint data, then high-resolution mapped cover, then the old 2000 grid surface only if needed. **No spin-up production PFT percentage approved**.

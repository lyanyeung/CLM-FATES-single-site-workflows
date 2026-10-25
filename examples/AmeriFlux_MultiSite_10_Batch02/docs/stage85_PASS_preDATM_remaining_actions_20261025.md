# Stage85 operator PASS — Ho1 2000 manual tower-T retained; Batch02 pre-DATM remaining gates

Date: 2026-10-25 23:55 UTC. **ACTUAL IRIDIS6 OPERATOR LOG**, exact 2026-10-25 user message:

```text
STAGE85 MANUAL DECISION APPLIED | original tower T unchanged 17568/17568; QC0 approved 17294
STAGE85 ORIGINAL VPD RETAINED FOR 32 ERA-SELF JAN SOURCE CASES
STAGE85 HUMIDITY-ONLY SATURATION-FRACTION REMAP 1068 QC0 HH; tower T never modified
STAGE85 NONQC0 ORIGINAL T SCIENCE HOLD 274
STAGE85 QBOT AVAILABLE QC0 17294 MISSING 0
REPORT /iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch02/reports/stage85_Ho1_2000_MANUAL_KEEP_TOWER_T_humidity_candidate_20261025T235555Z_12086954
STAGE85 CANDIDATE CREATED | new isolated CSV only; no formal DATM forcing/model jobs
```

Stage85 source Git commit `982e1e8919b5b9bb9ce3998f067c577bd74ad40d`, Git blob `e09676acaf05b21fa10eff3aace38cdd47880e41`.

## Completed versus remaining work

- **Ho1 original native 2000:** 17,568 source HH; all original air T unchanged. **17,294 measured-source QC0** temperature records now have a physically consistent candidate VPD/RH/QBOT with original source pressure. **1,068** source QC0 HH humidity-only saturation-fraction remap, **32** originally reviewed ERA-self-incompatible at TA_ERA records unchanged at tower-T basis. **0** QC0 candidate QBOT missing. Source/sensor provenance of original VPD is unchanged.
- **Not closed by Stage85:** **274 native TA_F QC!=0** original Ho1 2000 HH. These remain source-QC HOLDS; approval to use `TA_F` gapfilled source values is a different decision from preserving originally measured QC0 values. This can be handled with an explicit quality-policy decision; avoid inventing per-row measured provenance.
- Historical Stage74/75 full **16,874** original Ho1+BZS source hard humidity event audit (26/26 independent CDS target gridyears covered), **15,199** numerical humidity-only source shadows, and **1,675** initial temperature review flags are ARCHIVED, not retroactively edited or all automatically released by the new scoped decision. There can be overlap with Ho1 year-2000 Stage85; counts are not additive. Stage64 other-site **9,389** candidate records still separate.
- **Timing:** Site original release local-standard timestamps and an approved local-to-UTC/NO_LEAP/time-centering rule remain a distinct blocker for production DATM. Original site BIF nominal Ho1 -5 and BZS -9 were observed, but publisher effective historical period was not established from the newer BIF alone. If run in a strictly tower-local fixed-offset DATM context, method must be documented and validated explicitly before active CIME streaming.
- **Whole Batch02 10 sites:** raw/surface ten sites exist; science repair candidates and historical Stage08 / Stage09 Post-v5 work are separate. Not all ten selected end-to-end native meteorological releases and Post-v5 science gates have been shown approved; this Ho1-year2000 change must be reconciled into the site-wide/year-wide candidate without overwriting other source versions.
- **Technical NetCDF build remains to do for Batch02:** full continuous per-site/year meteorological data with seven forcing fields, native HH/HR handling (Ho1 HH, Ha1 HR), leap-day removal and noleap time axis, proper units, humidity/provenance, precipitation, stream template names and NetCDF readback all need an explicit Batch02 selection and builder. Use Batch01 successful source as a reusable SOFTWARE REFERENCE only: `examples/AmeriFlux_MultiSite_10/scripts/stage81/81_build_DATM_from_Stage80.py`. Batch01's exact 213 annual NC and stream templates were already built, but Batch02 cannot reuse Batch01's source manifest as though it contained Batch02 stations.
- **Actual DATM coupling** requires verifying domain, CIME DATM vs CDEPS, station heights/ZBOT, stream time centering, initial/terminal years and a short smoke test. Forest/OSH/wetland/crop/footprint representativeness and FATES PFT/landunits remain separate production model science gates rather than prerequisites for file-format construction.

## Remaining human decisions (not new review of previously approved 32/1068)
1. Approve a provenance-aware rule for 274 Ho1 2000 non-QC0 `TA_F` source rows (can use original gap-filled `TA_F` if those are what user intends to accept, but do not relabel these as measured); determine whether other Ho1 years share this policy.
2. Authorize time interpretation/local standard clock and site-specific actual DATM time coordinate alignment from supported metadata and dynamic observation conventions; source BIF nominal offsets are not a blanket historical certification.
3. For entire Batch02, close remaining source-QC0 edits / genuinely unresolved invalid pressure/humidity/gap and per-site ZBOT/PFT science concerns; no automatic direct ERA replacement of measured QC0 solely for >8 C contextual difference.

## Recommended next execution order
1. SHA-verify the Stage85 emitted `stage85_source_decision_manifest.json` and source/full-year CSV (already Stage85 printed success; this is a deployment integrity step, not a new science review).
2. Build **a combined annual source selection**, insert the newly approved Ho1 2000 source **by exact timestamp** into complete site-year forcing selection, keep source QC1/2 as separate provenance flags until policy is set, and run Batch02 Post-v5 numerical + extremes/QC0 event gates on the resulting COMPLETE exact ten-site selection.
3. Generate Batch02 `TECHNICAL_PREVIEW_ONLY` per-year NOLEAP NetCDF, CF-checked 7 variables and unchanged CIME stream placeholders (like Batch01 Stage81); record source SHA and 10-site 7-variable coverage. This is distinct from claim of approved production forcing.
4. Audit actual model case DATM/CDEPS syntax, calendar, height and time offsets; run isolated 1–5-day smoke-test case; production spinup only once science decisions are closed.

No validated runtime/ETA can be stated solely from this report because the remaining model input source selection, external historical clock evidence, operator QC policy and site metadata gates are not resolved. This log shows zero Batch02 DATM NetCDF produced by Stage85. 

**Manual decision is already done:** do not reopen original Ho1 2000 QC0/505 selected or the Jan 32 temperature review. Preserve original historical SHA and original tower T. No source/active forcing/CIME/Slurm writes occurred with Stage85.

# AmeriFlux Batch03 — execution ledger and scientific review status

**Evidence cut-off:** 2026-10-24, after successful IRIDIS6 Stage10d \`--check\` and \`--run\` logs provided by the operator.  
**Scope:** 10 exact AmeriFlux packages; 7 humidity-blocked stations; 32 site-years requiring additional ERA5-Land evidence; 1,924 residual cold-humidity blocker records.  
**Status:** **DATA/DIAGNOSTIC AUDITS COMPLETED; SCIENTIFIC HOLD; NOT DATM-/SPINUP-READY.**  
**Provenance boundary:** This Markdown file transcribes operator-reported terminal summaries. It is **not** a substitute for the SHA-pinned original CSV, receipts, source NetCDF/ZIP, or detailed per-event reports stored on IRIDIS6. Individual execution logs/reports were **not uploaded to GitHub** merely by adding this document.

## 1. Stage register: implemented code vs. observed execution

| Stage | Main purpose | Script directory | Latest verified status / limits |
| --- | --- | --- | --- |
| 00 | Upload exact ten raw packages | [stage00](../scripts/stage00) | 10/10 uploaded, transfer checksums verified; originals retained |
| 01 | Extract and inventory mixed FLUXMET/FULLSET releases | [stage01](../scripts/stage01) | 10/10 extracted; US-Me2 FULLSET_HH and US-MMS FLUXMET_HR preserved |
| 02 | Coordinates and metadata decisions | [stage02](../scripts/stage02) | Metadata inventory implemented; US-Me2 exact release lacks BIF UTC_OFFSET; known coordinate fallback does not constitute a clock |
| 03 | Isolated CTSM reference year-2000 surfaces | [stage03](../scripts/stage03) | 10/10 surface candidates built; site PFT/ecological representation still requires science review |
| 04a | Landunit/PFT structural QC | [stage04](../scripts/stage04) | 10/10 surface structural audit passed; does not establish vegetation/PFT suitability |
| 04b | Raw FLUXMET/FULLSET and ERA5 anomaly screening | [stage04](../scripts/stage04) | 20/20 source files screened; 292 source-years and 83,082 flagged records for review |
| 05 | Paired event provenance | [stage05](../scripts/stage05) | 20 raw source files paired; 16,820 anomaly episodes; no source event mismatch reported |
| 06 | Native timestamps and source repair scope | [stage06](../scripts/stage06) | Input and timestamp audit passed; 53,357 repair-scope rows diagnosed; no source changes |
| 07 | Isolated native QC-v5 candidate trial | [stage07](../scripts/stage07) | **3/10 numeric candidates** completed (US-MOz, US-Mpj, US-NC2); **7/10 blocked**, 2,273 unresolved humidity events; trial marker retained |
| 08–08f | Raw RH, ERA5 and MDS provenance/sensitivity | [stage08](../scripts/stage08) | 349 same-release RH reconstructions numerically eligible **but unapproved**; 1,924 residual blockers. MDS is not independent source evidence |
| 09a | Build pinned ERA5-Land dewpoint requests | [stage09](../scripts/stage09) | 32 year-site requests for 7 stations, covering 1,924/1,924 scoped events |
| 09b–09g | Download, integrity/QC and incremental complete queue | [stage09](../scripts/stage09) | Stage09g \`--check\`: **VERIFIED=32/32, REMAINING=0, BLOCKER_EVIDENCE=1924/1924**; external files do not approve humidity replacement |
| 09h | BIF UTC_OFFSET, timestamp cadence, SHA256 | [09h](../scripts/stage09/09h_audit_clock_metadata.py) | 7/7 tower and companion timelines passed; 6 sites have one published BIF offset; US-Me2 has no release BIF |
| 09i | Temperature-based time offset sensitivities | [09i](../scripts/stage09/09i_audit_external_time_alignment.py) | 32/32 site-years examined; temperature residual minimum often differs by 1h from BIF; this is **not** proof of wrong time metadata |
| 10a | Solar-position / shortwave-radiation clock sensitivity | [10a](../scripts/stage10/10a_audit_solar_clock_sensitivity.py) | 32/32 site-years; solar score favors each published BIF offset and US-Me2 hypothetical -8h among tested values; zero formally approved offsets |
| 10b | Two ERA5-Land humidity transfer sensitivities | [10b](../scripts/stage10/10b_audit_external_humidity_1924.py) | 1,924/1,924 rows processed: absolute vapour pressure 1,897 physical pass; gridded RH transfer 1,924 physical pass; **0 approvals** |
| 10c | Independent thermodynamic and MDS-key audit | [10c](../scripts/stage10/10c_independent_cold_humidity_audit.py) | Independent formula checks passed; 27 A-water failures; A ice supersaturation=170, B ice supersaturation=78; 0 approvals |
| 10d | SHA-pinned manual scientific review priorities and episode clustering | [10d](../scripts/stage10/10d_build_humidity_review_queue.py) | **1,924/1,924 classified into mutually exclusive priorities; 183 event clusters; 0 repair approvals** |

**Important historical nuance:** Early README subsections describe checkpoints as they occurred (e.g., Stage09f 20/32 before Stage09g). Those interim counts must not be interpreted as the latest status. The latest definitive Stage09g verification is 32/32.

## 2. Exact 1,924-event humidity scope

The original Stage07 residual-scope tally was 2,273. Under Stage08, 349 events were **numerically eligible** for same-release RH reconstruction, but these did **not** receive independent provenance approval and **none** of the seven blocked-site sensitivity runs completed. The subsequent Stage08b–Stage10d pinned investigation scope is **1,924 remaining events**. Do **not** interpret 2,273 - 1,924 = 349 as 349 approved/fully repaired records.

| Station | Residual events | Native interval | Published release BIF offset | Stage10a daylight evidence |
| --- | ---: | --- | --- | --- |
| US-Kon | 229 | 30 min | -6 h | Consistent with BIF -6 |
| US-MMS | 18 | 60 min | -5 h | Consistent with BIF -5 |
| US-Me2 | 4 | 30 min | **None in selected FULLSET** | -8 h strongest tested **hypothesis, NOT release metadata** |
| US-Me6 | 1 | 30 min | -8 h | Consistent with BIF -8 |
| US-MtB | 15 | 30 min | -7 h | Consistent with BIF -7 |
| US-NR1 | 173 | 30 min | -7 h | Consistent with BIF -7 |
| US-NR3 | 1,484 | 30 min | -7 h | Consistent with BIF -7 |
| **Total** | **1,924** | | **6 published, 0 formally approved** | **32 site-years reviewed** |

All Stage09h primary and companion ERA timelines were complete and uniformly spaced, with no invalid/duplicate/reversed timestamps in those exact releases. Stage10a compared \`SW_IN_F\` with astronomical solar geometry using native interval midpoints and candidate UTC offsets; solar diagnostics are supportive but not definitive clock approval. Time is interpreted as tower **local standard time**, without automatically adding DST. Stage09i air-temperature residual minima must **not** override BIF or definitive site documentation. US-Me2 needs an exact-release or official BADM/metadata clock check.

All 1,924 scoped records are below 0 °C at the retained tower temperature, so saturation over liquid water versus ice is a scientifically consequential distinction. ERA5-Land is driven by ERA5 and is not fully independent of source-provided ERA5 fields. No site-height/terrain adjustment or forcing conversion has been approved.

## 3. Stage10b–10c independent physics results

These results are **physical plausibility screens**, not replacement decisions or independent measurement validation.

| Site | Events | A absolute-e pass | B grid-RH pass | A fail/B pass | Ice RH>100%: A | Ice RH>100%: B | Tower/grid \|ΔT\|>5 °C |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| US-Kon | 229 | 229 | 229 | 0 | 0 | 0 | 2 |
| US-MMS | 18 | 18 | 18 | 0 | 2 | 1 | 0 |
| US-Me2 | 4 | 4 | 4 | 0 | 0 | 0 | 0 |
| US-Me6 | 1 | 1 | 1 | 0 | 1 | 0 | 0 |
| US-MtB | 15 | 14 | 15 | 1 | 4 | 0 | 0 |
| US-NR1 | 173 | 173 | 173 | 0 | 0 | 0 | 57 |
| US-NR3 | 1,484 | 1,458 | 1,484 | 26 | 163 | 77 | 91 |
| **TOTAL** | **1,924** | **1,897** | **1,924** | **27** | **170** | **78** | **150** |

**A:** use absolute vapor pressure derived from ERA5-Land dewpoint, evaluated with retained tower temperature and pressure.  
**B:** transfer ERA5-Land gridded relative humidity to retained tower temperature and pressure.

The independent Stage10c calculation reproduced Stage10b's vapor pressure, RH, VPD, specific humidity, UTC midpoint and paired event identity results. The **27 failures of A** comprise 26 US-NR3 and one US-MtB events; they yield **negative water-based VPD and/or water-based RH above 100%** after transfer. In the A failure set, 20 also have a B ice-supersaturation caution and seven do not. Ice supersaturation is a **caution rather than a universal physical impossibility**, and 78 B values with RH relative to ice above 100% need review despite B passing all liquid-water checks.

Stage10b's \`absolute_minus_mds_vpd_hPa\` output was not populated by its original join, as confirmed by Stage10c; Stage10c independently restores comparison with original Stage08f \`VPD_F_MDS\`. MDS values may be gap-filled or lower-quality and are not automatically independent observations. Stage10d reports **zero** pairs meeting both its original MDS-pair-physical and both-QC0-or-QC1 criteria. Do not equate 1,625 finite MDS VPD values with validated replacement values.

Notable site limitations: Stage09i US-MtB year-sample tower/grid *median absolute* temperature mismatch was about 7 °C, while the **event-only signed median** in Stage10b was about -0.72 °C; these statistics use different subsets and should not be conflated. US-NR1 and US-NR3 have 57 and 91 event-specific \|ΔT\|>5 °C cautions, respectively. Stage09i US-NR3 temperatures in some years used finite values because QC0 observations were insufficient; the limitations must be retained in any scientific interpretation.

## 4. Stage10d completed, mutually exclusive review priorities

Priority is determined sequentially. Overlap among individual physical caution flags is separately recorded in the detailed CSV; priority categories partition the events **without granting an approval**.

| Site | P0 | P1 | P2 | P3 | P4 | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| US-Kon | 0 | 0 | 0 | 2 | 227 | 229 |
| US-MMS | 0 | 1 | 1 | 0 | 16 | 18 |
| US-Me2 | 4 | 0 | 0 | 0 | 0 | 4 |
| US-Me6 | 0 | 0 | 1 | 0 | 0 | 1 |
| US-MtB | 1 | 0 | 3 | 0 | 11 | 15 |
| US-NR1 | 0 | 0 | 0 | 57 | 116 | 173 |
| US-NR3 | 26 | 57 | 86 | 87 | 1,228 | 1,484 |
| **Total** | **31** | **58** | **91** | **146** | **1,598** | **1,924** |

Definitions:
- **P0:** 27 records with water-based A transfer failure (negative VPD / RH too high), plus **four US-Me2 clock-metadata holds**. Do not mislabel all 31 P0 rows as thermodynamic failures.
- **P1:** remaining cases with B relative-to-ice RH >100%.
- **P2:** remaining cases with A relative-to-ice RH >100%.
- **P3:** remaining cases with tower versus ERA5-Land grid temperature difference >5 °C.
- **P4:** remaining cold-humidity events still requiring scientific review despite no earlier priority condition.

Operator Stage10d \`--check\` and \`--run\` both reported: **1,924/1,924 classified, A_failed=27, B_ice=78, A_ice=170, tower_grid_gt5C=150, 183 consecutive event clusters, repair_approvals=0**.

### Stage10d MDS support distinctions

The per-site \`MDS_numeric_VPD\` count sums to **1,625**, but only **421** were flagged \`MDS_VPD_valid_at_retained_T\` and **zero** simultaneously passed Stage10d's \`MDS_pair_physical_and_QC01\` criterion. Those are *different* tests: numerical presence, physical consistency with retained tower temperature, and measurement/gap-fill provenance. None is a repair permit.

## 5. IRIDIS source-of-truth paths (not GitHub-tracked raw reports)

Base:
\`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03\`

| Evidence | Exact existing directory |
| --- | --- |
| Stage07 isolated QC-v5 candidate trial | \`qcv5_native_trial_20261022T024559Z_36c46e58/\` |
| Stage08 original raw-RH sensitivity | \`raw_RH_sensitivity_20261022T025645Z_3c43eb8b/\` |
| Stage09a external request plan | \`reports/stage09a_external_dewpoint_plan_20261022T034051Z_437c9c0c/\` |
| 32 ERA5-Land original downloaded evidences + receipts | \`external_evidence/era5land_timeseries/\` |
| Stage10b per-event two-transfer results | \`reports/stage10b_external_humidity_20261024T040142Z_be6a9d78/\` |
| Stage10c independent thermodynamic audit | \`reports/stage10c_independent_cold_humidity_20261024T041355Z_36d578f4/\` |
| Stage10d scientific manual review and 183 clusters | \`reports/stage10d_humidity_manual_triage_20261024T042016Z_7fa50aaa/\` |

Stage10d principal CSVs:
- \`all_1924_manual_review.csv\` — every source-row identity and review flag.
- \`site_triage_summary.csv\` — P0–P4 counts and MDS distinctions by site.
- \`consecutive_event_clusters.csv\` — 183 temporal episode groups.
- \`P0_high_priority_events.csv\` — A-transfer failures and US-Me2 metadata hold.
- \`A_water_failure_27.csv\` — exact A failure subset.
- \`B_ice_supersaturation_78.csv\` — B low-temperature supersaturation subset.
- \`read_only_provenance.json\` — Stage10c SHA and report output hashes.

GitHub contains **the executable analysis methods and this operator-log-derived progress summary**. It does **not**, as of this documentation commit, contain the above IRIDIS per-event CSVs, large NetCDF/ZIP evidence or full terminal logs. This is intentional: avoid bulk data duplication and keep exact provenance/immutable original artifacts on institutional storage. Archive verified receipts and selected compact summaries separately if long-term reproducibility is needed; do not delete any currently required source, receipt, restart or report just because GitHub has a narrative summary.

## 6. Scientific decision ledger / gates

| Decision or concern | Current disposition |
| --- | --- |
| Original tower meteorology and exact releases | **Immutable**; source SHA verified; no overwrite |
| Stage07 3 numerical candidate completions | **Incomplete trial**; no Post-v5 acceptance; seven blocked |
| 349 native RH numeric sensitivities | **Not approved**; missing independently validated RH QC provenance |
| ERA5-Land 32/32 files | **Complete evidence availability**, not a validated forcing dataset |
| Six published BIF UTC offsets | Supported by Stage10a solar tests, but **not formally approved** |
| US-Me2 offset | -8 h diagnostic hypothesis only; release-specific documentation missing |
| ERA5-Land grid vs tower | Terrain/elevation/measurement-height and ERA5 dependence remain unresolved |
| A absolute-e humidity | 27 water-based physics fails; never force/clamp negative VPD |
| B gridded-RH humidity | 1,924 liquid-water screens pass, but 78 ice supersaturation cautions and source uncertainty remain |
| MDS alternative | No Stage10d MDS pair simultaneously passed physical and QC0/1 criteria |
| PFT/surface ecological suitability | Structural checks passed but PFT/community match unapproved |
| Forcing, DATM, Post-v5, spinup | **NOT APPROVED; 0 repairs; no Slurm submissions** |

## 7. Next steps (not yet implemented/approved)

1. Obtain official clock convention and release-specific/BADM \`UTC_OFFSET\` evidence for US-Me2; independently reconcile all tower time conventions and source variable interval definitions.
2. Investigate P0 A failures (27) and US-Me2 separate clock metadata holds (4); review 78 B ice-supersaturation flags, including overlaps.
3. Perform site-elevation / measurement-height and provenance review for temperature/grid discrepancies, notably US-MtB, US-NR1 and US-NR3. Evaluate subfreezing liquid-water vs ice conventions and physically appropriate supersaturation tolerance.
4. Evaluate accepted humidity science criteria and non-ERA-independent evidence where available; independently audit event continuity and flanking meteorology before proposing any final repair.
5. Only after explicit scientific approval, create a **new versioned candidate** without modifying original input, and undertake full post-QCv5 consistency/hash audits (humidity, QBOT, VPD, TA, PA, precipitation, time, retained QC0, source ledger).
6. Independently approve PFT/surface, forcing loop, time interval, atmospheric CO2 settings, and then design DATM/CIME/spinup cases. Nothing in Stage10a–10d is permission to start CLM-FATES jobs.

### Recheck workflow (safe)

From the existing IRIDIS checkout (with \`clm_fates_env\` active), the commands below are only retrospective checks and do not re-download ERA5-Land or submit model jobs:

\`\`\`bash
BASE="$HOME/CLM-FATES-single-site-workflows/examples/AmeriFlux_MultiSite_10_Batch03"
PY="$CONDA_PREFIX/bin/python"
"$PY" -B "$BASE/scripts/stage09/09g_download_all_remaining.py" --check
"$PY" -B "$BASE/scripts/stage09/09h_audit_clock_metadata.py"
"$PY" -B "$BASE/scripts/stage09/09i_audit_external_time_alignment.py" --check
"$PY" -B "$BASE/scripts/stage10/10a_audit_solar_clock_sensitivity.py" --check
"$PY" -B "$BASE/scripts/stage10/10b_audit_external_humidity_1924.py" --check
"$PY" -B "$BASE/scripts/stage10/10c_independent_cold_humidity_audit.py" --check
"$PY" -B "$BASE/scripts/stage10/10d_build_humidity_review_queue.py" --check
\`\`\`

The scientific hold remains in force even if every check prints PASS.

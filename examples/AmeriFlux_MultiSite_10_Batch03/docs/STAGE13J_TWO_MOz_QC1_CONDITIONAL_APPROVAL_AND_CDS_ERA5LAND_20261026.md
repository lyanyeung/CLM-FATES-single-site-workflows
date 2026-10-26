# Stage13j — Operator's two-event US-MOz 2005 QC1 *conditional* science authorization, 26 Oct 2026

## Operator has approved the conditional scientific rule (NOT a blanket substitution)

- Exactly **2005-01-05 20:00 to 2005-01-06 09:00**, source-native half-hour inclusive, **27** records.
- Exactly **2005-01-06 14:00 to 2005-01-07 09:30**, native time inclusive, **40** records.
- Combined science scope **67 records**, only if each *entire* event independently passes all required source and science tests.
- At passing native events only, new isolated forcing successor replaces BOTH `TA_USE` and `VPD_USE` with externally retrieved, aligned, source-verified ERA5-Land **T2m and T2m/dewpoint-derived VPD**; reconstruct `TBOT=TA_USE+273.15` and `QBOT` consistently using preserved `PSRF`. Both `TA_F_QC=1` and `VPD_F_QC=1` are required at every original half-hour in scope. Any failed event is left exactly unchanged and **HOLD**.
- The approved 2005-01-06 10:00 Stage07 TA/VPD repair remains retained, never reapplied. **2005-01-09 negative-bias QC1 and all other source events remain unapproved**, as do Post-v5, DATM, model spinup and Slurm.
- The latest 50-site recommended PFTs are curated separately; **US-MOz model hypothesis ENF10/DBF90**, and this does not imply the case/surface already implements it. Original BIF `HEIGHTC=24.2m` is not `ZBOT`.

## Verified original BIF metadata

User-uploaded `AMF_US-MOz_BIF_20230331.xlsx`, `AMF-BIF`, 439 row dataset:

- `LOCATION_LAT=38.7441` (row 174)
- `LOCATION_LONG=-92.2000` (row 175)
- `UTC_OFFSET=-6.00` (row 439); offset is **published metadata, not an independently demonstrated source/ERA clock alignment**
- `HEIGHTC=24.2` (row 117) **canopy only**, no per-variable meteorological sensor height.

Stage13j verifies that the **release original FLUXMET BIF CSV** agrees numerically with these three values, and verifies SHA of that source-specific original BIF before accessing ERA5-Land. It does not infer tower measurement height.

## Data-provenance limitation

The prior Stage09 external ERA5-Land download inventory included **seven** humidity-incomplete sites, **not US-MOz**; therefore **no known previously validated US-MOz 2005 external source** can be assumed. Stage13j can download a completely isolated *one-request*, signed CDS `reanalysis-era5-land-timeseries` 2005-01-03 through 2005-01-11 gridpoint series for official BIF 38.7441, -92.2000, requesting T2m, dewpoint, surface pressure. Requires `cdsapi` and valid IRIDIS6 `~/.cdsapirc`; the download does NOT change meteorological forcing or approve repairs. It never overwrites an earlier artifact.

**ERA5-Land is driven by ERA5 and therefore not statistically independent meteorological truth**; separately downloaded CDS grid is an external cross-product check, not an independent ground observation. Additional tested scientific gates are mandatory:

1. Exact SHA and source-native time of original tower/companion ERA, Stage07 approved original, Stage13g successful shadow and Stage13i original QC1 ledger.
2. Release-specific BIF UTC offset `-6` and native `TIMESTAMP_START +15min` translated into raw hourly UTC; independent analog comparison with **at least 12 measured QC0 tower TA+VPD slots** from Jan03–10. The published offset must outperform offsets `-7,-5` by at least 1°C temperature MAE and maintain T MAE <=3°C and VPD MAE <=2hPa; no assumed DST.
3. For each of the two proposed episodes separately, actual unaltered source `QC0` measured tower T+VPD anchors within six hours *on both sides*, within 2.5°C and 2.5hPa of aligned external ERA5-Land. This is deliberately strict and may HOLD both events if no anchors exist.
4. All episode source-QC1 points >5°C apart from original paired ERA (per signed Stage13i); actual CDS gridpoint and time complete, hourly UTC, 0.3 degree coordinate tolerance, Kelvin/Pa verified.
5. For every replacement, aligned CDS temperature differs from paired FLUXNET ERA temperature by <=3.5°C, inferred RH differs by <=15 percentage points; liquid-water RH strictly between 0 and 100%, VPD positive but below saturation, `QBOT` positive <0.08kg/kg, external pressure within 12 kPa of retained model `PSRF`, and outside-edge TA/VPD jumps <=4°C /4hPa.
6. Output differential only at passing event half-hours and variables TA/VPD/TBOT/QBOT, unchanged original source/candidate SHA and NOLEAP source index. Failed event is skipped entirely.

These are cautious **automated screening gates**, not proof of true cause. If either segment is blocked, do not change that episode or broaden the approval without new source evidence / user science decision.

## 2026-10-26 19:07 UTC IRIDIS6 actual CDS download verified; Stage13j v2 false coverage STOP fixed in v4

Operator IRIDIS6 log confirms the **new CDS data request succeeded**: `reanalysis-era5-land-timeseries`, BIF coordinate 38.7441/-92.2, 2005-01-03–2005-01-11, request `082878d6-33ec-448d-a93e-618abe5b5091`. Signed receipt file:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/external_evidence/era5land_timeseries/US-MOz/2005_stage13j/ERA5Land_US-MOz_Jan03_Jan11_2005_t2m_d2m_sp.receipt.json`.
Underlying downloaded CDS response SHA256: `5879ed81aca701d53b8b9674183556df7369861ce4a8cdca1ffd54126fb712ef`.

The subsequent Stage13j v2 `--check` stopped with `CDS response did not cover UTC 2005-01-04..10` at line 259. **Confirmed code defect:** the left coverage bound was reversed: it required `Jan04 <= earliest_UTC`, incorrectly excluding the valid earlier requested Jan03 starting timestamp. Correct bound is `earliest_UTC <= Jan04` and `latest_UTC >= Jan10 23:00`, followed by full hourly-interval checking. In [Stage13j v4 script](../scripts/stage13/13j_conditional_two_US_MOz_QC1_ERA5Land_SCOPED.py), `verify_utc_coverage` now prints actual min/max and has positive and negative synthetic date-range regressions in `--self-test`.

**NO RE-DOWNLOAD:** The SHA-receipted original CDS response is already present. Run only the pinned v4 `--self-test`, `--check --decision`, and `--apply --decision` if the scientific gate returns eligible rows. **No `--fetch` retry**: the original command correctly refuses to overwrite existing signed evidence.

**Anticipated conservative scientific HOLD:** Stage13i showed original 2005 Jan03–Jan06 and Jan06–Jan09 contiguous QC1 blocks; the operator explicitly required measured `TA_F_QC=0` **and** `VPD_F_QC=0` anchors on BOTH sides within 6h of each approved event. These may be absent. Stage13j v4 now always reports the exact native QC0 six-hour before/after counts for **both** scoped events, even when the broader time-alignment screen fails. If either condition fails, the event remains completely **HOLD**; do NOT relax QC0 to QC2 or increase window without a new operator science approval. No original or Stage13g forcing change from the observed failure.

## 2026-10-26 Stage13j v4 IRIDIS6 verified scientific HOLD — download complete, no replacements

User executed the pinned v4 Git blob `9283b411b49500428e7534b5f12041c71190e93b`, `--self-test` PASS and `--check` PASS as a read-only science diagnostic. Exact source `FLUXNET_BIF` SHA, original source/ERA, current Stage13g candidate SHA and CDS SHA all verified. CDS hourly UTC time range **2005-01-03 00:00 to 2005-01-11 23:00 inclusive, 216 h**. Exact required two events **27+40=67 native halfhours**.

**Why both events are scientifically held** (not a code/runtime exception):

- Jan05 20:00–Jan06 09:00, native original measured QC0 TA+VPD within 6 h: **before 0 / after 0**.
- Jan06 14:00–Jan07 09:30, native original measured QC0 TA+VPD within 6 h: **before 0 / after 0**.
- Jan03–Jan10 has **29 original TA_F_QC=0 + VPD_F_QC=0 paired measured** analogues in aggregate, but none near the required two event edges.
- BIF official `UTC_OFFSET=-6`. QC0 tower-vs-CDS grid 29-analogue T MAEs: UTC−7 **0.7761585°C**, UTC−6 **0.5937427°C**, UTC−5 **0.7098455°C**. VPD MAEs: −7 **0.2718506 hPa**, −6 **0.2455981 hPa**, −5 **0.2186896 hPa**. UTC−6 has the **lowest T MAE**, but Stage13j's chosen stringent time-offset superiority gate requires ≥1.0°C advantage over both neighbors; observed advantages only 0.1824°C and 0.1161°C. This **fails the original science rule**, not the source BIF metadata.
- Result: `overall=HOLD_MEASURED_QC0_CLOCK_OR_BOUNDARY`, exact new patches **0**, previously approved Stage13g **fully retained**; user code correctly skipped `--apply`.

**Next diagnostic already committed:** [Stage13k nearest true measured QC0/QC2 from full source and all 67 external ERA comparison, read-only](../scripts/stage13/13k_MOz_two_events_original_QC0_and_ERA5Land_evidence_READONLY.py). Its `--check` and `--run` require the existing already-downloaded CDS evidence and an unmodified adjacent signed Stage13j v4 source, and explicitly quantify nearest QC0 anchors beyond six hours, source-QC2 provenance and complete event grid-vs-companion humidity/time differences. It **does not** relax the operator's original approval, authorize a blanket 67-row ERA5Land substitution, or change any model file. `--run` creates a new versioned SHA report only.

To overcome absent local QC0 source measurement, a new documented operator-approved independent validation policy would be required; simply changing Stage13j's 1°C advantage cutoff or treating QC2 as QC0 is not sufficient.

## IRIDIS6 script and behavior

[Stage13j pinned fail-closed conditional script](../scripts/stage13/13j_conditional_two_US_MOz_QC1_ERA5Land_SCOPED.py). Use exact Git blob hash in the supplied command, pin the Stage13j decision JSON in the same commit.

`python3 -B "$SCRIPT" --self-test`: no file access or writes.
`python3 -B "$SCRIPT" --check --decision "$DECISION"`: recheck scientific SHA/metadata, if no CDS evidence outputs `HOLD_MISSING_DISTINCT_CDS_ERA5LAND_SOURCE`; **no writes**.
`python3 -B "$SCRIPT" --fetch --decision "$DECISION"`: **one CDS API request**, separately signed `external_evidence/era5land_timeseries/US-MOz/2005_stage13j` only. No forced retrieval if credentials unavailable.
`python3 -B "$SCRIPT" --check --decision "$DECISION"`: full source, grid, UTC/QC0/physics/event gate; produces HOLD or eligible count; **no writes**.
`python3 -B "$SCRIPT" --apply --decision "$DECISION"`: re-check and export an isolated complete NOLEAP successor with only individually fully passing approved events; if none pass, exit as HOLD and create **no forcing**. Always leave originals unchanged. No Slurm/model.

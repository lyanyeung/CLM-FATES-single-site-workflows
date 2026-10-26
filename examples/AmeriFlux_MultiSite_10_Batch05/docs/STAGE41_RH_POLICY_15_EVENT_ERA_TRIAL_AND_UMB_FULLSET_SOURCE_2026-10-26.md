# AmeriFlux Batch05 Stage41 — immediate event-level source policy candidate + real US-UMB FULLSET_HH source verification

## Stage40 IRIDIS6 operator execution (26 October 2026)

Actually executed source-verified Stage40, output:
`/home/ly3n24/ameriflux_batch05_stage40/source_humidity_physics_20261026T180721Z_1601029`.

Stage40 source physics test confirms 16 numeric candidate methods correspond to 15 original events: **14 original events with negative physically impossible implied RH over water** (from original tower/source T and original selected VPD), plus `US-Var_E0017` with original implied RH **0.393141%** and competing ERA vs MDS methods.

The 14 negative-source-RH events comprise: `US-Var_E0019` (−4.326995%), `US-Var_E0033` (−9.515558%), 9 original US-Vcp E0127/E0144/E0145/E0146/E0168/E0169/E0170/E0171/E0172 (RH minima between −59.194835 and −2.276611%), `US-WCr_E0013` (−5.171163%), `US-Wkg_E0009` (−112.008105%), and `US-Wkg_E0010` (−27.544695%).

**Scientific rule:** Earlier investigator policy in Batch05: negative RH or extremely low RH is an anomaly that should be prioritized for ERA5/ERA5-Land source repairs. *Proof that the original VPD/RH combination is physically invalid is NOT proof that a particular source ERA value is validated by in-situ measurements.* Even the 14 low-numerical-risk Stage38 source-ERA full-event trials include >10hPa candidate VPD differences (US-Var E0033 ~18.23 hPa; US-Var E0019 ~12.73hPa), requiring further method provenance and isolated post-v5 source-boundary QC. No new source or production forcing is authorized by Stage41.

**US-Var E0017:** MDS leaves original VPD unchanged (which implies 0.393% RH, extremely dry). Source-ERA RH gives 12.431942hPa VPD correction. The previously expressed near-zero-RH policy supports comparing ERA as a **candidate**, but does not justify marking a forcing patch approved without source/reference validation.

## Critical US-UMB source correction

Stage40 directly listed the following existing FULLSET source:
`/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/US-UMB/forcing/raw/AMF_US-UMB_FLUXNET_FULLSET_2007-2021_3-5/AMF_US-UMB_FLUXNET_FULLSET_HH_2007-2021_3-5.csv`.

The corresponding existing `FULLSET_2007-2021_3-5` source is NOT a `FLUXMET_HH` v1.3 archive. Therefore the earlier absence of FLUXMET_HH does **not** prove no native half-hour US-UMB T/VPD source data exist. Stage41 checks **all 23 original source P2/P3 native timestamps** against original Stage27 T/VPD/QC using FULLSET_HH `TIMESTAMP_START,TA_F,VPD_F`, plus `TA_F_QC,VPD_F_QC` if those fields exist. Requires numeric T/VPD match ±0.002 and exact QC (if present), never silently recodes QC0 or labels FULLSET gapfilled fluxes as measured observations. Missing/unmatched data stay `SOURCE_HOLD`.

## Stage41 research source

[Stage41 complete original 15-event source ERA RH research overlay and US-UMB actual FULLSET_HH 23 native source record verifier](../scripts/stage41/41_policy_negative_RH_ERA_overlay_trial_and_US_UMB_FULLSET_source.py), GitHub commit `6583ccdfd8b6195b1a5b291fb4c8199a4c3a990b`, blob SHA `2eeaf59d2aa53ed410af13620e6cbcb286dad3e6`.

[Stage41 one-click operator launcher](../scripts/stage41/run_stage41_iridis6.sh), GitHub commit `f992aff5cd780bd6d8963f20ead6282509fdf7da`, blob SHA `7d01f3744877c8b84fd6417f5e3607b93c784883`.

Stage41 reads completed original Stage40/39/38 reports and original Stage27 and Stage24 source statuses, checks exact source-native T/VPD and source QC0 guard, never overwrites original source or earlier 166 user-approved overlay. Requires the 15 actual Stage40 original episodes each has a source-ERA RH trial previously numerically checked for **zero newly introduced Stage39 >2/4hPa event internal/external jumps**, and each has at least one original negative or <1% RH native source record. Reconstructs full original native source episode using source processed ERA RH and original T, preserving the RH calculation and original source QC. The ERA-family trial is physically bounded but NOT a reanalysis-independent observation.

Outputs:
- `stage41_NEGATIVE_OR_LT1PCT_RH_ALL15_EVENT_ERA_RESEARCH_OVERLAY.csv`
- `stage41_ALL15_EVENT_SOURCE_SCIENCE_REPAIR_GATES.csv`
- `stage41_US_UMB_FULLSET_HH_EXACT23_SOURCE_QC_COMPARISON.csv`
- `STAGE41_SOURCE_POLICY_AND_UMB_FULLSET_REPORT.md`
- `stage41_manifest.json`

All rows are `manual_science_approval=NO_NEW_APPROVAL` and `production_forcing_authorized=NO`. There is no direct CIME/DATM/Slurm write. Existing Stage24 166 approved, original 46 P1 HOLD, 10 RH platforms and 1574 P2/P3 remains untouched. A preliminary hypothetical versioned overlay is not a production forcing patch.

### IRIDIS6: pinned three-line command

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/f992aff5cd780bd6d8963f20ead6282509fdf7da/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage41/run_stage41_iridis6.sh" -o "$HOME/run_stage41.sh"
test "$(git hash-object "$HOME/run_stage41.sh")" = "7d01f3744877c8b84fd6417f5e3607b93c784883"
bash "$HOME/run_stage41.sh"
```

**GitHub committed and SHA-checked. Actual IRIDIS6 execution still pending.**

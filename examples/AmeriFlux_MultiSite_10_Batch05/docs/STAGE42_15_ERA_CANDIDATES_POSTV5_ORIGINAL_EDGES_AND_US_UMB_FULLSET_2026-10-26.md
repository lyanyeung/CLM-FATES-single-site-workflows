# Batch05 Stage41 PASS and Stage42 next research-only original source validation

## Stage41 actually executed on IRIDIS6, October 26, 2026

```text
STAGE41 SOURCE VERIFIED
STAGE41 SELF-TEST PASS
STAGE41 SUCCESS | 15 original RH invalid or <1% events, ERA family full-event research candidate HH 21
STAGE41 GATES {"SEVERE_MAGNITUDE_GT10HPA_REVIEW": 4, "SOURCE_ERA_PROVENANCE_REVIEW_BEFORE_FORCING": 11}
STAGE41 UMB US_UMB_FULLSET_23_T_VPD_QC_IDENTICAL_SOURCE_PROXY_NOT_FLUXMET
  {"SOURCE_T_VPD_QC_MATCHED_FULLSET_NOT_FLUXMET": 23}
STAGE41_REPORTS=/home/ly3n24/ameriflux_batch05_stage41/ERA_original_RH_policy_20261026T182003Z_1665949
```

This resolves an **acquisition/provenance confusion, not scientific humidity validation**: US-UMB original FULLSET_HH (2007–2021) matches the original Stage27 selected source T, VPD and QC for all **23/23 native half-hours**. This product is FULLSET_HH, not FLUXMET_HH, and full forcing acceptance is not inferred from matching columns.

The 15 event / 21 half-hour previous negative-RH or original extremely-low-RH full-event *processed-source ERA* replacement research draft has four significant >10hPa event changes: US-Var E0017, E0019, E0033 and US-Vcp E0172. Remaining 11 events still require source-ERA provenance review. **Negative original RH validates an anomaly, NOT the particular new ERA RH truth**. Existing Stage24 166 approved, 46 manual P1 HOLD, ten saturation plateaus and all 1574 original P2/P3 are unchanged.

## Stage42: actual original ZIP/FULLSET native-time Post-v5 preflight

[Stage42 original SHA-verified native source and 15+US-UMB9×2 method-event science trial](../scripts/stage42/42_postv5_isolated_15_ERA_events_and_UMB23_fullset_source_trials.py)

Pinned code commit `ca8f49a048dcbe1036c150f950d1cda2d523bfae`, blob `b80320d75bfb404de4b8345340306399488b0e11`.

[One-click IRIDIS6 launcher](../scripts/stage42/run_stage42_iridis6.sh), commit `916eed0d5770ce40b038ec42b796644f47ffd58c`, blob SHA `644e63018c457341981dcbf67f9abb0ca279c07e`.

**Tracks:**

1. The 15 exact Stage41 original invalid/nearzero-RH events (21 native half-hours, US-Var/Vcp/WCr/Wkg) are checked against *actual SHA-pinned original AmeriFlux FLUXMET_HH ZIPs*, original selected QC, Stage27 original values and neighbouring original half-hours at ±30 minutes. Calculate original vs hypothetical source-ERA VPD jump magnitudes and *new* >2/>4hPa internal/external crossings. An event with new severe jump must HOLD. Source RH water saturation, original T, QC0 and Stage24 approved/HOLD exclusions are strict.
2. Now that UMB's actual original FULLSET_HH source has been matched for 23/23 original records, compare two full-event source RH methods `SOURCE_ERA` and `SOURCE_MDS` over all nine original P2/P3 episodes (**18 method×episode trials**); no automatic science approvals. Reject QC0 edits, noncontiguous original-source episode windows, incomplete RH, and unsafe VPD boundaries. No inventing missing original FLUXMET_HH; FULLSET_HH is explicitly recorded as source provenance.

Outputs:
- `stage42_ALL33_RESEARCH_EVENT_METHOD_QC_GATES.csv`: 15+18 source event×method classifications;
- `stage42_POSTV5_NATIVE_BOUNDARY_ORIGINAL_VS_TRIAL.csv`: before/after original native transitions;
- `stage42_RESEARCH_ONLY_NATIVE_METHOD_CANDIDATES_NO_FORCING.csv`: physically screened, **unapproved** source-native RH/VPD candidate values;
- `STAGE42_POSTV5_BOUNDARIES_AND_UMB_SOURCE_CLOSURE.md` and SHA-pinned `stage42_manifest.json`.

The study is an **original meteorology QC preflight**, not full forcing/DATM model acceptance. No production forcing input written. All 166 old approved, 46 human HOLD, ten RH saturation, original 1574 P2/P3, Slurm and source files remain unchanged.

### Three-line IRIDIS6

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/916eed0d5770ce40b038ec42b796644f47ffd58c/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage42/run_stage42_iridis6.sh" -o "$HOME/run_stage42.sh"
test "$(git hash-object "$HOME/run_stage42.sh")" = "644e63018c457341981dcbf67f9abb0ca279c07e"
bash "$HOME/run_stage42.sh"
```

**Code committed but IRIDIS6 execution pending.**

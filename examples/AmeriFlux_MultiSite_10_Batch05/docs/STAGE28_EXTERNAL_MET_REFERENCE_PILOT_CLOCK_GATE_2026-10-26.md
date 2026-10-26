# AmeriFlux Batch05 — Stage27 operator result / Stage28 independent weather reference prerequisites

## Stage27 executed successfully (operator output, 2026-10-26)

```text
STAGE27 SELF-TEST PASS
STAGE27 SUCCESS | P2/P3=1574 original HH, original episodes=483; no science approvals
STAGE27 REVIEW_LANES {
 "NATIVE_RH_PRESENT_PROVENANCE":5,
 "DUAL_AGREES_LE5PP_REVIEW":23,
 "DUAL_DISAGREES_5_TO20PP":115,
 "DUAL_CONFLICT_GT20PP":408,
 "ERA_ONLY_SOURCE_REFERENCE_REQUIRED":1023
}
STAGE27 T_DIFF_GT5 372
STAGE27 ERA_RH_VS_ERA_E_DIFF_GT2 66
STAGE27 ERA_CANDIDATE_VPD_CHANGE_GT5 715
STAGE27 P2/P3 science approvals=0; Stage24 overlay and 46 manual holds unchanged
STAGE27_REPORTS=/home/ly3n24/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604
```

The 546 native HH with both source MDS and source processed ERA humidity candidate split into **23 concordant within 5 percentage points**, **115 different by >5 and ≤20 pp**, and **408 conflicting by >20 pp**. 1023 HH have only source processed ERA RH (and possibly derived processed ERA vapor pressure as a non-independent shadow). Five contain original source RH.

**408 large source disagreements are concentrated in US-Vcp (339), followed by US-Wjs (37), US-Vcm (23)**. US-Vcp contains 626 original P2/P3 unapproved HH. US-Vcp, US-Wjs and US-Vcm together account for 1389/1574 (~88.2%) original P2/P3 HH. A physically feasible processed source ERA counterpart does NOT equal an independently validated meteorological replacement.

Selected tower TA exceeds/undershoots source processed ERA TA by >5°C at 372 HH, source ERA RH-conserving vs ERA actual-vapor-pressure-conserving VPD differs >2 hPa at 66 HH, and source ERA reconstructed VPD differs >5 hPa from selected original VPD at 715 HH. Risk flags can overlap.

### Critical official site metadata (public AmeriFlux sources)

| Site | Official AmeriFlux station | latitude | longitude | elevation m | source |
|---|---|---:|---:|---:|---|
| US-Vcp | Valles Caldera Ponderosa Pine | 35.8641 | -106.5965 | 2501 | https://ameriflux.lbl.gov/sites/siteinfo/US-Vcp |
| US-Wjs | Willard Juniper Savannah | 34.4258 | -105.8617 | 1931 | https://ameriflux.lbl.gov/sites/siteinfo/US-Wjs |
| US-Vcm | Valles Caldera Mixed Conifer | 35.8885 | -106.5322 | 3043 | https://ameriflux.lbl.gov/sites/siteinfo/US-Vcm |

The towers' elevations and habitat differences are **material** when comparing grid-scale ERA5-Land meteorology; the source release may involve elevation-adjusted downscaling. Do not mistake the bundled original `TA_ERA/VPD_ERA` source counterparts for a newly downloaded ERA5-Land reference.

**Fluxnet time convention**: Native `TIMESTAMP_START`/`TIMESTAMP_END` are LOCAL STANDARD TIME with no DST; the UTC offset is **site metadata-dependent** and is **not proven from geographic longitude alone**. See https://fluxnet.org/data/fluxnet2015-dataset/ (Time zone convention). Site BADM can provide `UTC_OFFSET` and `LOCATION_LAT/LONG/ELEV`; see https://ameriflux.lbl.gov/data/badm/badm-standards/LOCATION. Never shift hourly/half-hourly fluxnet timestamps to UTC until site-specific offset and source release alignment are verified.

## Stage28 read-only source metadata / high-risk independent reference pilot

[Stage28 source script](../scripts/stage28/28_independent_reference_metadata_and_priority_windows_readonly.py)

Pinned GitHub commit: `ae9133ebfb60571948f231dc77e9d3c17327afad`
Verified original Git blob SHA: `3c21a19ebcbb956beb07a5a088eb4e203294cf07`

Runs against the already successful Stage27 **1,574/483** native original evidence and Stage24 **166 approved, 46 original P1 HOLD and ten saturation-platform HH**. Creates new read-only review outputs for:
- Top 20 science-risk **original P2/P3 episodes**, all three priority sites only (number is user-controllable);
- All **five original P1 HOLD** native event windows, totaling 46 unchanged HH;
- Two **unapproved native near-saturation RH platform** windows (Vcm Oct 2025 4 HH; WCr Aug 2025 6 HH);
- For the three official site locations, read-only attempt to inventory the original ZIP contents and detect files potentially containing `UTC_OFFSET`; the script **never approves** those offsets just because a matching string exists.

Outputs:
- `stage28_SITE_METADATA_AND_UTC_OFFSET_GATES.csv` with official coordinates / elevation, original ZIP status and any UTC offset *source textual evidence* (review only), `verified_release_UTC_OFFSET` blank.
- `stage28_27_TOP_EPISODE_HOLD_PLATEAU_NATIVE_WINDOWS.csv` for 20 P2/P3 + 5 P1 HOLD + 2 plateau native windows with ±6-hour native context, no inferred UTC.
- `stage28_PILOT_ORIGINAL_P2P3_HH_FOR_INDEPENDENT_VALIDATION.csv` P2/P3 source HH with MDS/ERA RH and source temperature differences.
- `STAGE28_METADATA_CLOCK_AND_REFERENCE_PILOT_PLAN.md` operator-readable coordinates, top events and field evidence gaps.
- `stage28_summary.json` exact source hashes and no-writes statement.

### Run on IRIDIS6

```bash
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch05_stage28"
  COMMIT="ae9133ebfb60571948f231dc77e9d3c17327afad"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT"
  SCRIPT="$BASE/28_independent_reference_metadata_and_priority_windows_readonly.py"
  D27="$HOME/ameriflux_batch05_stage27/source_comparison_20261026T040257Z_1589604"
  D24="$HOME/ameriflux_batch05_stage24/four_approved_edges_20261026T033353Z_1589604"
  ROOT="/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 \
    "$RAW/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage28/28_independent_reference_metadata_and_priority_windows_readonly.py" -o "$SCRIPT"
  test "$(git hash-object "$SCRIPT")" = "3c21a19ebcbb956beb07a5a088eb4e203294cf07"
  echo "SOURCE VERIFIED"
  python3 -B -m py_compile "$SCRIPT"
  python3 -B "$SCRIPT" --self-test
  OUT="$BASE/reference_preflight_$(date -u +%Y%m%dT%H%M%SZ)_$$"
  python3 -B "$SCRIPT" --stage27-dir "$D27" --stage24-dir "$D24" \
    --site-root "$ROOT" --pilot-episodes 20 \
    --out "$OUT" 2>&1 | tee "$BASE/stage28.log"
  echo "STAGE28_REPORTS=$OUT"
  cat "$OUT/STAGE28_METADATA_CLOCK_AND_REFERENCE_PILOT_PLAN.md"
  cat "$OUT/stage28_SITE_METADATA_AND_UTC_OFFSET_GATES.csv"
)
```

### Next *data-changing* step only after science gate

1. Verify site-specific release BADM `UTC_OFFSET` (or documented site metadata time series) and epoch-specific applicability. **Do not assume −07:00 because sites are in New Mexico, or change clocks for DST.**
2. With source-native-clock–UTC alignment verified, build a small pilot independently downloaded **ERA5-Land hourly 2 m temperature / dewpoint temperature** set, preserving dataset units Kelvin (and surface pressure if humidity conversion requires it), source reanalysis vintage, native hourly UTC clock, and interpolation policy. Alternative independent station observations help as distinct evidence; ERA5-Land remains a reanalysis, not independent measured truth.
3. Validate elevation/time differences vs original tower/MDS and source processed ERA; examine 339 US-Vcp conflicts and top episode periods before choosing one consistent site-specific strategy.
4. Human science approval only after source reference validation, retain Stage24 approved 166, P1 HOLD 46 and saturation-platform 10; do not yet create model-ready DATM forcing or run CLM-FATES.

**Script committed to GitHub, operator Stage28 execution not yet confirmed. All source CSV/ZIP/forcing/CIME/Slurm unchanged.**

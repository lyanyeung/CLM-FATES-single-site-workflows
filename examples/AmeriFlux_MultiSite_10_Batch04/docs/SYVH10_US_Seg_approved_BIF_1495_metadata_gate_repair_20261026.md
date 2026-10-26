# Batch04 SYVH10 metadata Gate-1: US-Seg duplicate original BIF coordinates — retain previously user-approved GROUP_ID 1495

**Operator error (2026-10-26, read-only):**
```
SYVH10 SELF-TEST PASS ...
GATE1 SITE US-Rpf ... SURFACE SURFACE_MISSING_OR_MULTIPLE ...
GATE1 SITE US-SP1 ... SURFACE SURFACE_MISSING_OR_MULTIPLE ...
GATE1 SITE US-SRG ... SURFACE SURFACE_MISSING_OR_MULTIPLE ...
GATE1 SITE US-SRM ... SURFACE SURFACE_MISSING_OR_MULTIPLE ...
ValueError: Nonunique actual native BIF station location/UTC offset US-Seg
```
Previous source and surface files were unchanged; Gate-1 stopped **before** full ten-site metadata inventory. This does **not** invalidate completed **SYVH9 numerical seven-meteorology 10/10 NOLEAP Gate-0 PASS**.

## Original provenance and PREVIOUS operator's explicit approval

This is not an unknown choice: [Stage02 original metadata source](../scripts/stage02/02_check_batch04_metadata.py) explicitly requires and validates the single **user-approved** entry in [`coordinate_decisions.tsv`](../coordinate_decisions.tsv), which is original-GitHub source-verified, not inferred:

```tsv
site	package	group_id	latitude	longitude	elevation_m	location_date_start	approval
US-Seg	AMF_US-Seg_FLUXNET_2007-2025_v1.3_r1	1495	34.3623	-106.7020	1596	200701010000	APPROVED_BY_USER
```

The original release BIF also retains historical alternative **GROUP_ID 1479**, with longitude **−106.7019** and elevation **1622 m**. These groups must remain in the raw BIF archive without averaging or inventing physical relocation. **Existing Stage02 approved 1495 lat=34.3623 lon=−106.7020 elevation=1596m, location start 2007-01-01** stays binding. The independently verified original US-Seg `UTC_OFFSET=-7` must remain unique across original BIF observations. The UTC offset is **not** arbitrarily selected from the 1495 location grouping.

## Fixed SYVH10 — separate ambiguity from known operator approval

[Corrected `stage_syvh10_postv5_site_metadata_and_DATM_gate1_readonly.py`](../scripts/manual_review/stage_syvh10_postv5_site_metadata_and_DATM_gate1_readonly.py), pinned commit **`3b7f2db6e7be5ebe08e50b847db4837650b189d8`**:

1. Requires the **exact source** `coordinate_decisions.tsv` from the *same pinned GitHub commit*, downloaded as `Batch04_approved_coordinate_decisions.tsv` **beside the script**.
2. Verifies exact approval row, `APPROVED_BY_USER`, site, package, GROUP_ID, lat/lon/elevation/date, then checks the four values **co-occur in the original SHA-verified BIF GROUP_ID 1495**. It reports approval file SHA in the audit; retains alternative BIF coordinate values for traceability. No arbitrary choice for other nine sites.
3. Separately requires a **single valid original BIF UTC_OFFSET** and for US-Seg requires **−7**. If offset is genuinely conflicting, fail closed — don't invent an offset or silently shift source meteorology.
4. Removes false-positive height candidates (`FLUX_MEASUREMENTS_METHOD`, `TOWER_POWER`, `HEIGHTC_DATE`) from metadata inventory by requiring numerical height records; **does not** claim a selected station ZBOT or substitute canopy height.
5. The script still SHA-verifies the final SYVH9 10-site research manifest and Gate-0 receipt and only writes small HOME JSON/TSV reports on `--report`; **never** overwrites native met, source BIF or ERA, surface/PFT or models.

**Single corrected copy-paste command for IRIDIS6, no git pull or model writes:**

```bash
conda activate clm_fates_env
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_manual_review"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  COMMIT="3b7f2db6e7be5ebe08e50b847db4837650b189d8"
  REL="examples/AmeriFlux_MultiSite_10_Batch04"
  FINAL="/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_Batch04_SYVH9_12_low_LW_5sites_independent_ERA5Land_research_not_approved/candidate_20261026T121123Z_a8b8146f"
  mkdir -p "$BASE"
  curl -fLsS --retry 3 "$RAW/$COMMIT/$REL/coordinate_decisions.tsv" -o "$BASE/Batch04_approved_coordinate_decisions.tsv"
  SCRIPT="$BASE/stage_syvh10_postv5_site_metadata_and_DATM_gate1_readonly.py"
  curl -fLsS --retry 3 "$RAW/$COMMIT/$REL/scripts/manual_review/stage_syvh10_postv5_site_metadata_and_DATM_gate1_readonly.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -u -B "$SCRIPT" --candidate-dir "$FINAL" --report 2>&1 | tee "$BASE/Batch04_SYVH10_Gate1_approved_Seg_1495_FINAL.log"
)
```

Expected `US-SEG VERIFIED EARLIER USER APPROVAL GROUP_ID 1495 LAT 34.3623 LON -106.702 ...`, ten `GATE1 SITE` records, then `SYVH10 SOURCE PROVENANCE AND POSTV5 DATM METADATA GATE1 AUDIT COMPLETE`. If any remaining original BIF data conflicts, send exact offending site and exception only; no source/model writes.

**Separate Gate-1 limitation from first actual four site results:** `SURFACE_MISSING_OR_MULTIPLE`, with no verified point-surface candidate at the default `MY_EC_SITE/{site}/subset_data/surfdata*.nc` path, and 0 inspected domain file paths. This is a technical site-surface/domain *inventory blocker*, not an EC met data failure; actual file placement/creation needs to be resolved independently. If other sites are similarly affected, batch search known IRIDIS6 surface/inputdata locations after repaired inventory. No automatic assumption that the canonical point surface is entirely absent or that previously configured case/domain is safe.

**Current status:** fixed script committed to GitHub, **not yet re-run** on IRIDIS6. No model release or Slurm submission approved by this metadata check.

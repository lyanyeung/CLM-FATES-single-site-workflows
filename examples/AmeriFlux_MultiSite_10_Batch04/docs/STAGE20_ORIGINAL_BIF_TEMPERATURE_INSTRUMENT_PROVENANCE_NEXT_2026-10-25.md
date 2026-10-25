# Batch04 Stage20 — original air-temperature instrument/BIF provenance inventory (next IRIDIS6 run)

**Status (2026-10-25): Stage19 IRIDIS6 OPERATOR-VERIFIED PASS (6/6, 8 temperature holds retained). Stage20 Python source is committed but the operator has NOT yet run the Stage20 \`--audit\` on IRIDIS6.**

Scientific rationale: [Stage19 exact multi-day results](STAGE19_VERIFIED_MULTIDAY_TEMPERATURE_REGIMES_2026-10-25.md). The original US-SP1 temperature differs from the processed ERA reference over multiple hours on several days; repeated numeric values alone do not prove a stuck sensor. US-SRG has exactly one source-QC0 temperature difference below −10°C, surrounded by QC2 ERA-downscaled substitutions rather than independently measured tower flanks. US-Seg shows original contiguous cooling and zero events below that screening threshold. Identifying the raw **instrument and measurement-height provenance**, if exposed in the BIF metadata, is preferable to automatically replacing tower temperatures with an ERA product.

## Stage20 code and run command

[Stage20 temperature source metadata script](../scripts/stage20/20_audit_original_BIF_temperature_instrument_metadata.py) committed at \`0ebb29514c032d05b3f205cec42e67a7e60424f3\`.

The following command is intended for the user's IRIDIS6 login shell; the Bash \`tee\` writes only one review log under \`$HOME\`. No git pull, CDS retrieval or forcing/model writes.

~~~bash
(
  set -euo pipefail

  BASE="$HOME/ameriflux_batch04_stage20"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts"
  STAGE20_COMMIT="0ebb29514c032d05b3f205cec42e67a7e60424f3"
  DEPENDENCY_COMMIT="9be06860ee3e9f14e08fb078d22d0090b49d58d4"

  mkdir -p "$BASE"
  SCRIPT="$BASE/20_audit_original_BIF_temperature_instrument_metadata.py"
  curl -fLsS --retry 3 \
    "$RAW/$STAGE20_COMMIT/$REL/stage20/20_audit_original_BIF_temperature_instrument_metadata.py" \
    -o "$SCRIPT"

  curl -fLsS --retry 3 \
    "$RAW/$DEPENDENCY_COMMIT/$REL/stage12/12_repair_non_syv_science_holds.py" \
    -o "$BASE/12_repair_non_syv_science_holds.py"

  python3 -B -m py_compile "$SCRIPT"
  python3 -B -m py_compile "$BASE/12_repair_non_syv_science_holds.py"
  python3 -B "$SCRIPT" --self-test
  python3 -B "$SCRIPT" --audit \
    2>&1 | tee "$BASE/stage20_original_BIF_temperature_instrument_readonly.log"
)
~~~

## What it checks, and what it cannot establish

- SHA256-checks the **three original native full-length FLUXMET sources** (US-SP1, US-SRG, US-Seg), the **original BIF** for each site, and the original BIF site latitude, longitude and UTC offset.
- Verifies exact Stage12 \`148/156\` source-repair state and all **eight** original unresolved temperature-science events before reading new metadata. It does not change earlier Stage14/15 research branches.
- Inventories original BIF \`VARIABLE\`, \`DATAVALUE\` and \`GROUP_ID\` fields: candidate air-temperature/TA/T_AIR groups plus associated instrument, sensor, measurement-height, date, manufacturer/model and metadata fields, when present.
- Prints bounded source metadata excerpts, always labelled **POSSIBLE / CANDIDATE metadata**. Missing or unlinked BIF records must be reported as **INSUFFICIENT EVIDENCE**, not used to infer nonexistent instruments, a false original QC0 measurement or validated raw sensor replacement.
- This script cannot query unpublished site operator records or reconstruct raw instrument readings that were never deposited in the original release. Such gaps require targeted site-PI inquiry or an independent raw-data source.

**Scientific next action:** after the IRIDIS6 output, decide whether the original BIF contains time-linked instrument provenance adequate for a site-specific review, or whether a site-specific data-holder inquiry is required. Retain all **8 original temperature science HOLDs**, US-Syv **606** deferred science HOLDs plus **10** skipped ERA endpoints, and prevent production Post-v5/DATM/CIME/spinup authorisation.

**Return the complete Stage20 stdout** from \`$HOME/ameriflux_batch04_stage20/stage20_original_BIF_temperature_instrument_readonly.log\` to allow evidence-based progression and GitHub status update. No Stage20 PASS or sensor identification is claimed without that output.

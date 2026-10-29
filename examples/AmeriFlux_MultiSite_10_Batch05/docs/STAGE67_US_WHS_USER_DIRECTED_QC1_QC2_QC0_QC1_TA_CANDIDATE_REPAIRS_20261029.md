# AmeriFlux Batch05 — Stage67 US-Whs operator-directed source TA temperature interpolation

## Manual methodology selection, 29 October 2026

The investigator supplied actual Stage66 full-US-Whs source audit:

```text
STAGE66 SUCCESS | ORIGINAL ALL-YEAR US-Whs TA_F jump inventory, no source/model modifications
STAGE66 SOURCE_RANGE 200701010000 202512312330 TOTAL_HH 333120 GAPS 0
STAGE66 QC_COUNTS {"0": 296559, "1": 1609, "2": 34952, "OTHER": 0}
STAGE66 SPIKE_COUNTS {"10": 13, "3": 4511, "5": 282, "8": 34}
STAGE66 JUMP_GE5_QC_TRANSITIONS {"0->0": 219, "0->1": 26, "1->0": 23, "1->1": 5, "1->2": 4, "2->1": 5}
```

**User-selected precise science policy**: investigate and repair only source-native 30-minute original `|ΔTA_F| ≥ 5°C` transitions `QC1→QC2` (4 jump edges) by interpolation from surrounding **QC1** donor values; and `QC0→QC1` (26 edges) by interpolation between two **QC0 measured** donor values. Preserve all other transitions and observations unchanged. This is **30 trigger boundaries**, not necessarily 30 replacement half-hours; each trigger may start an extended block. The other 252 >=5°C transition edges are deliberately excluded.

**Critical provenance distinction**: QC=0 observation-based/source tower measurements, QC=1 MDS fill and QC=2 processed-source ERA fill are lineage codes, not arbitrary "good/bad" flags. Do not rewrite source QC2 as 1, or source QC1 as 0, after numerical interpolation. A *versioned source-T-preserving candidate only* is generated, and original source values/QC remain accessible. This repairs candidate temperature only; VPD and moisture are untouched and their thermodynamic consistency remains a separate future review gate.

## Bounded operator-selected interpolation

For each flagged edge, isolate its following **maximal contiguous native source-QC target run**, and require actual site-native **30-minute consecutive timestamps** and **two immediate bracketing native QC donors** of the specified class:
- `QC1→QC2`: preceding original QC1 TA_F and next original QC1 TA_F bracketing only QC2 points, for linear temporal interpolation.
- `QC0→QC1`: preceding original QC0-measured TA_F and next original QC0-measured TA_F bracketing only QC1 points, for linear interpolation.

The script cannot infer a trustworthy numerical replacement if there are long gaps or changes to other QC classes. It reports **HOLD** for missing donor anchor, missing TA source, clock gap, >12 half-hour targets (>6 hours), numerically implausible anchor, or interpolation that would create a new ≥5°C per-30min step. These conservative gates are explicit *source-science numerical preflight rules*, not a scientific claim that the resulting temperature is actually observed.

**Known 2012-05-25 QC1→QC2 examples:**
- 05:30 QC1 TA_F=31.635°C → six QC2 HH from 06:00 through 08:30 → 09:00 QC1 TA_F=33.085°C. Interpolation generates a smooth intermediate QC2-labelled *candidate*, distinct from original ERA-filled values. The QC1 +8.051°C jump at 05:00→05:30 remains unmodified because `QC1→QC1` was explicitly excluded.
- 09:00 QC1 33.085°C → single QC2 09:30 → 10:00 QC1 32.765°C, numerical candidate 32.925°C. The original QC at 09:30 stays 2.

## Immutable GitHub scripts

- [Stage67 candidate builder](../scripts/stage67/67_US_Whs_QC1_to_QC2_QC0_to_QC1_TA_repair_candidates.py), commit `f76c0a8ef07124a8b69b9b94fc34aa8c2aadf81f`, blob `fa209d5e2483f48769d8e24e0725bb23a6cf621a`.
- [Stage67 IRIDIS6 SHA-pinned launcher](../scripts/stage67/run_stage67_US_Whs_targeted_TA_candidates_iridis6.sh), commit `aa3e29520e73954611f317b26ad55939dea0bd7d`, blob `736ce04ec0a547d36ef4f437c3b04bde939a73d3`.

```bash
curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/aa3e29520e73954611f317b26ad55939dea0bd7d/examples/AmeriFlux_MultiSite_10_Batch05/scripts/stage67/run_stage67_US_Whs_targeted_TA_candidates_iridis6.sh" -o "$HOME/run_stage67_Whs.sh" && test "$(git hash-object "$HOME/run_stage67_Whs.sh")" = "736ce04ec0a547d36ef4f437c3b04bde939a73d3" && bash "$HOME/run_stage67_Whs.sh"
```

Reads operator-verified Stage66 at
`/home/ly3n24/ameriflux_batch05_stage66_Whs/all_TA_jumps_20261029T033601Z_2119759`
and original pinned SHA `0e25b768c60114aba5bc7600c1d08e4d629e4d147e32c208b7e7f8cca12d3767` FLUXMET ZIP.

Produces:
- `stage67_ALL30_TARGETED_QC_TRANSITIONS_AND_DECISIONS.csv` with exact 30-source-edge keys, target run spans and classifications;
- `stage67_USER_SELECTED_TA_INTERPOLATION_CANDIDATE_ONLY.csv` with original TA/QC and individually versioned candidate TA for valid bounded runs, as well as original unchanged VPD and VPD QC;
- `stage67_UNREPAIRABLE_QC_BRACKET_HOLDS.csv` with explicit reason and unchanged source scope;
- `stage67_manifest.json` immutable source hashes, selected rules, and count reconciliation.

**Stage67 GitHub code/launcher Git SHA verified; on-cluster run not yet reported.** No original source changes, no existing 204-user-approved RH/VPD overlay changes, no VPD recalculation, no DATM/CIME or Slurm submission. Before any model-forcing action, explicitly review relevant humidity/VPD physical consistency and the new candidate values. This is a bounded science candidate workflow, not an automatic assertion that the whole US-Whs site is now scientifically finished.

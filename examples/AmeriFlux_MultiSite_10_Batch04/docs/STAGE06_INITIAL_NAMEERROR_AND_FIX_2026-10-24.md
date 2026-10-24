# Batch04 Stage06 initial read-only execution fault and fix

**Date:** 2026-10-24. User-provided exact IRIDIS6 output:

```text
=== SYNTAX CHECK ===
=== SELF TEST ===
STAGE06 SELF-TEST PASS: source timestamps, saturation physics, direct pair checks
=== VERIFY ALL STAGE05 REPAIRS ===
STAGE06 SELF-TEST PASS: source timestamps, saturation physics, direct pair checks
Traceback (most recent call last):
  File ".../06_audit_batch04_qcv5_candidate_effects.py", line 347, in main
    source=read_source_context(meta,context_needed(patches,holds))
  File ".../06_audit_batch04_qcv5_candidate_effects.py", line 150, in read_source_context
    x["TIMESTAMP_START"] for x in patches + holds if x["site"] == site
NameError: name 'patches' is not defined
```

**Diagnosis:** the Stage06 script's `read_source_context()` reached a variable scope bug: `patches` and `holds` were defined by `main()` but not passed into the reader. Therefore this is a Python analysis script defect, **not a Stage05 dataset defect**, and was not caught by its original limited mathematical self-test. The user command was set to `set -euo pipefail`, so the failure at `--check` halted the shell group **before `--run`**. No Stage06 report materialization or original data mutation is shown.

**Fix committed to the default GitHub branch:**
- Commit `af4d3fadaf3a61a6f869f8767407b4e5b546898f`: pure `required_target_keys(patches,holds)` helper; reader now explicitly accepts `required_keys`; main passes this mapping; test exercises required vs neighbouring-context keys without any file writes.
- Commit `ae7765e3096479b5cb157928e6dc88ab88e69268`: align Stage06 numeric missing-value handling with Stage05 `-6999/-9999` conventions.

Current repaired source: [Stage06 audit script](../scripts/stage06/06_audit_batch04_qcv5_candidate_effects.py).

**Execution status:** the new GitHub source has been committed but no user log confirming successful rerun is available yet. Re-download fixed source before invoking `--self-test`, `--check` and optionally `--run`. A completed self-test alone does not verify the 5,336 sparse patch values; the independent full `--check` must pass.

Stage05 separate candidate version remains:
`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage05_candidates/candidate_20261024T103113Z`.
Any future Stage06 scientific result remains subject to the 754 unresolved Stage05 HOLDs and candidate VPD/RH physical/jump review.

# JapanFlux Stage05AW — ACTUAL original 45/45 unified evidence reconcile PASS; next Stage05AX original source QC0/QC1 neighbors (2026-11-03)

## Operator-executed actual Stage05AW result

```text
STAGE05AW SELF-TEST PASS | exact original 45 QC2 variable fields, 35 site-native times, 22 strong+23 context, no repair values/writes
STAGE05AW 45 ORIGINAL JPF SELECTED F=ERA QC2 VS INDEPENDENT HOURLY ERA5L SOURCE EVIDENCE RECONCILED PASS | NO REPAIR
ORIGINAL_SOURCE_FIELD_COVERAGE 45 /45 DISTINCT_SITE_NATIVE_HALF_HOURS 35
EVIDENCE_TIERS 22 PRIOR_STRONG_CONTEXT + 5 SOURCE_JST_CONTEXT_ONLY + 18 OPERATOR_JST_CONTEXT_ONLY
ORIGINAL_SOURCE_SITES {'JP-Fjy': 6, 'JP-Khw': 11, 'JP-Yms': 10, 'JP-Tef': 4, 'JP-Tmd': 14} VARIABLES {'PA': 27, 'TA': 6, 'LW_IN': 12}
INDEPENDENT_REFERENCE_OUTSIDE_ALL_45 True
UNIFIED_45_SOURCE_HOLD_TABLE /home/ly3n24/japanflux_stage05aw/run_20261103T061649Z/stage05aw_45_original_JPF_F_ERA_QC2_source_vs_ERA5L_independent_context_ALL_HOLD.tsv
REPAIR_READINESS_SUMMARY /home/ly3n24/japanflux_stage05aw/run_20261103T061649Z/stage05aw_45_original_JPF_QC2_35_source_native_times_REPAIR_READINESS_NOT_APPROVED.json
NEXT_ORIGINAL_QC0_QC1_NEIGHBOR_REVIEW_ONLY; ALL_45_SOURCE_FIELDS_HOLD; NO FORCING/MODEL/SLURM
```

The operator ran the original [Stage05AW unified 45-field source ledger](../scripts/stage05/05aw_merge_45_original_QC2_independent_context_REPAIR_READINESS_HOLD_NO_WRITES.py) to combine actual Stage05AL 27, AT 2, AU 8, AV 8 independently ERA5-Land contextualized selected-F=embedded-ERA original QC2 fields with strict exact source site/native halfhour/variable mapping. All 45 are outside independently retrieved nearby gridded model hourly reference envelopes. **This does not certify replacements, exact tower halfhour values or any original source clock conversion.**

Original-source evidence classes: 22 previously `STRONG_CONTEXT` at source-verified JST sites, 5 newer Yms context-only at verified JST source, 18 Tef/Tmd context-only using operator-chosen `JST_UTC_PLUS9_DIAGNOSTIC_ONLY` (original 75-line README SHA `17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5` says local solar time). The original `F_QC=2` class is a release-specific ERA-derived selected-field flag, not true measured tower values. **All 45 science HOLD, 0 approved replacement values**.

## Stage05AX first REAL JP-Tmd attempt: source-number type error, corrected code committed

On 2026-11-03 the operator ran the first SHA-pinned Stage05AX `--site JP-Tmd`. The real `py_compile` and `--self-test` passed. During **read-only original source QC2 source-row reconciliation**, Python raised:

```text
TypeError: must be real number, not str
  File "stage05ax.py", line 231, in _inner_scan
    close(f,events[key]["original_source_F_QC2"])
  File "stage05ax.py", line 83, in close
    math.isclose(a,b,abs_tol=atol,rel_tol=1e-10)
```

**Root cause:** source `F` parsed as a float, but Stage05AW TSV loaded via `csv.DictReader` retained the same original source number as a string. This is a Python code typing error, NOT original JP-Tmd provenance corruption and NOT a failed meteorological science test. Source ZIP is only read; no original ZIP/forcing/model, no external CDS or Slurm modifications occurred.

The corrected Stage05AX source `close` now runs **both** operands through the already existing `numeric()` source parser, refuses nonfinite/missing values, and compares source floats to original ledger numeric strings safely. Added self-test regression for mixed `float`/`str`, source value `0.0`, and missing/-9999 values.

**Additional preventative source-provenance correction:** instead of using an unverified full literal SHA for the 85-line JP-Fjy/Khw/Yms original README releases, Stage05AX now **requires `--stage05k-dir`**, reads each original `JP-<site>_exact_metadata.json` from the earlier verified Stage05K sources, requires its original `README.txt` SHA256 and source metadata status, and cross-compares with SHA256 computed by re-reading the actual nested original JPF source ZIP. Checks that the original 85-line JST-source README states local standard time (without DST), and retains the independently verified, exact 75-line Tef/Tmd solar README original SHA `17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5`. The genuine computed README SHA is stored in each site report, with `original_readme_sha256_matches_prior_Stage05K: true`. This improves source integrity without guessing a digest or altering timebase science status.

**Code fix commit:** `476cc0ade51c95e14ed3c6b84826e3129316ec2e`, script Git blob SHA `7cc202ff9a15fd4f78bba84d33cf65faeb4b3e07`. A corrected *real* JP-Tmd source run has **not yet been observed**. No result of Stage05AX site audit can be claimed until successful real execution. Stage05AW 45/45 independently contextualized science result remains PASS and all original 45 variable fields remain HOLD. Use corrected pinned Stage05AX and `--stage05k-dir "$HOME/japanflux_stage05k"` on the retry.

## Next Stage05AX (script COMMITTED; corrected real IRIDIS run PENDING)

[Stage05AX 5-source JPF original halfhour QC0 vs QC1 gapfill neighbor / contiguous QC2 episode forensic read-only](../scripts/stage05/05ax_45_original_JPF_QC0_QC1_neighbor_and_QC2_run_READONLY.py)

Run each of five original JPF source releases separately (bounded 512 MiB nested ZIP buffer) to avoid building 5 large full HH archives in memory. Source outer layout is the actual original `/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<site>/forcing/packages/<package>.zip` with a nested `<package>.zip` containing exact original `JPF_<site>_FLUXNET_FLUXMET_HH_<year range>_v1.3_r1.csv` and SHA-pinned README. No extraction or modification of source ZIP; original FLUXMET HH CSV read once per site in a stream, with CRC validated at EOF.

For each exact Stage05AW flagged variable record, preserve original site/native halfhour/F value/same-release ERA/F_QC=2, read original **±24 h** on the source-native timestamp axis, and report:
- Nearest left/right **QC0 measured** same-variable F and timestamps within source window, if present.
- Nearest left/right **QC0 or QC1** same-variable F and timestamps; QC1 = already gap-filled, **not original measured**, so weaker.
- Original selected `F`, `_ERA`, optional raw-measurement `TA`/`PA`/`LW_IN`, `_F_MDS`, `_F_MDS_QC` columns as actually available; absence recorded as absent. Do not assume original measured raw sensor columns are present.
- **Full contiguous run length** of QC2 source records per variable (could extend far beyond the ±24h context window), to avoid false short-gap interpolations.
- A conservative **feasibility screen** only: `SHORT_QC0_BRACKETED_SHADOW_CANDIDATE_REVIEW_ONLY`, `MIXED_QC0_QC1_BRACKETED_REVIEW_ONLY_QC1_IS_GAPFILL`, or `LONG_OR_UNBRACKETED_QC2_SOURCE_EPISODE_HOLD_EXTERNAL_CONTEXT_NEEDED`. These are temporal anchor screens, **not approved repair values**.

Source frame must be unchanged even for the original Tef/Tmd local-solar vs operator-JST timebase discrepancy. The Stage05AX script uses the original native timestamps and does not align neighbors against hypothetical UTC: the within-source QC sequence is valid independently of external clock provenance.

Actual Stage05AW science input paths:
```text
/home/ly3n24/japanflux_stage05aw/run_20261103T061649Z/stage05aw_45_original_JPF_F_ERA_QC2_source_vs_ERA5L_independent_context_ALL_HOLD.tsv
/home/ly3n24/japanflux_stage05aw/run_20261103T061649Z/stage05aw_45_original_JPF_QC2_35_source_native_times_REPAIR_READINESS_NOT_APPROVED.json
```

The user's original `examples/JapanFlux_MultiSite_11/sites.tsv` SHA-1 Git blob `344ce4d822f3a0393da7b7e2ef5ece6d6204104f` locks 11 release selections, including exactly the five original JPF QC2 source sites.

After real five site-level passes, optional `--aggregate --site-results-root` verifies **45 source fields, 35 distinct site/native halfhours, site and variable populations**, and produces a unified derived neighbor feasibility table. No CDS calls, no forcing/model/Slurm/AD400 work, no original source modifications and no automatic repair. User previously stated PFT configuration is already complete and is outside scope.

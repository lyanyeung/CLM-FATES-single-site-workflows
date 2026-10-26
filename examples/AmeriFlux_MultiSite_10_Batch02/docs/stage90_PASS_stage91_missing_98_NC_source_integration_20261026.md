# Batch02 Stage90 operator PASS → Stage91 missing-five-site source integration

26 October 2026. Actual user Stage90 output `SYNTAX PASS`, `SELF-TEST PASS`, 6 original primary source SHA verified, `STAGE90 AUDIT PASS`; no input or model writes. Source report `reports/stage90_Ha1_VPD_Ho1_Dec_source_context_20261026T011202Z_ca90b24c`.

## Confirmed state, without premature model approval

- Stage87 successfully built exactly **117 technical yearly NOLEAP NetCDF** for BZS 15, CMW 21, Ha1 35 (hourly), Ho2 27, Ho3 19. **Not science-approved, not active DATM**.
- Other five site year counts **98**: EML 16 (2008–2023), GLE 16 (2005–2020), Ho1 28 (1996–2023), ICh 19 (2007–2025), ICt 19 (2007–2025). All ten sum to **215** desired technical yearly files. Missing 98 source-complete and independently checked files **cannot be claimed built**.
- 24 historical Stage07 original QC0 edits include BZS 1 TA, CMW 1 VPD + 1 TA, Ha1 2 VPD, Ho2 7 VPD + 12 LW_IN. Original neighbor/source recheck supports candidate corrections, but exact science approval is not implied by being numerically valid.
- Ha1 original 2003-05-29 07:00/08:00 tower T 12.4/13.4 C and VPD 14.404/15.379 hPa, physically just beyond water saturation pressure (~14.389/15.362). Approximate original derived RH -0.10/-0.11%; candidate interpolation VPD 10.461/8.638 hPa is a reasonable *numerical correction candidate*, still track original QC0 changes with explicit provenance.
- Ho1 original 2000-04-19 09:30 through 04-20 11:00 has 52 non-QC0 source T, max difference against ERA 4.52 C, both ends connected to original QC0 T. Preserve original gapfill/QC flag.
- Ho1 original 2000-12-27 09:00 through 12-31 23:30 has **222** non-QC0 T: one QC1 source `TA_F=-15.4`, source `TA_ERA=3.444` on 27 Dec 09:00; the next 221 QC2 source T equal original `TA_ERA`, starting 09:30 at `3.346` C. Boundary jumps +18.746 C in 30 minutes; no evidence that either independently measured real environment was that warm/cold. First later original QC0 T is **2007-12-31 23:30**, so the intervening quality-source segment must not be mislabeled observed tower T. This specific boundary and broader non-QC0 use require explicit provenance policy/physical source review; avoid blind smoothing or automatically changing original QC0. Stage85 previously approved source-original QC0 T 17,294, humidity remaps 1,068, 32 retained VPD unchanged.
- Stage64 9,389 independent numerical RH source candidates and Stage74 15,199 independent CDS shadows are **not** automatically approved or disjoint from Stage85. Do not count them as a finished ten-site forcing file or as mutually additive events.
- Production gates remain: full ten-site selected source CSV/manifest; Post-v5 numeric/extremes QC; site clock offset and native interval centering; ZBOT; surface/PFT/footprint, CIME DATM/CDEPS and smoke test. Slurm spinup must not start from preview templates.

## Stage91 worklist (not model forcing builder)

[Source](../scripts/stage91/91_missing_five_site_forcing_integration_worklist.py) pinned commit `bc11e17db4ed1b8e0a927c32305938490b0b4d9d`, Git blob `0a6ec7563265497e18b2d19810e3f871ec239271`. This hashes Stage64/74 numerical-source manifests and exact csv, Stage85 manual 2000 CSV, Stage87 117 technical manifest and Stage90 report; joins distinct site/native-time correction/shadow scopes into a **98 site-year** build plan, preventing double counting. It creates only isolated source integration worklist reports. It **does not build the 98 NetCDF files**, activate DATM, repair the Ho1 18.746 C source transition, or approve older shadows.

### Copy to IRIDIS6

```bash
(
 set -euo pipefail
 conda activate clm_fates_env
 REL="examples/AmeriFlux_MultiSite_10_Batch02"
 COMMIT="bc11e17db4ed1b8e0a927c32305938490b0b4d9d"
 BLOB="0a6ec7563265497e18b2d19810e3f871ec239271"
 TMP="$(mktemp /tmp/batch02_stage91_XXXXXX.py)"
 trap 'rm -f "$TMP"' EXIT
 curl -fLsS --retry 3 \
   "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/$COMMIT/$REL/scripts/stage91/91_missing_five_site_forcing_integration_worklist.py" -o "$TMP"
 test "$(git hash-object "$TMP")" = "$BLOB"
 python3 -B -c 'import ast,sys; ast.parse(open(sys.argv[1],encoding="utf8").read()); print("SYNTAX PASS")' "$TMP"
 python3 -B "$TMP" --self-test
 python3 -B "$TMP" --check
 python3 -B "$TMP" --audit 2>&1 | tee "$HOME/Batch02_Stage91_source_worklist.log"
)
```

Expected: `STAGE91 SELF-TEST PASS`, `STAGE91 CHECK PASS`, `STAGE91 WORKLIST PASS | 98 missing NC source years...`. If a SHA, row schema or original count conflicts, stop; do not select by latest path or silently relax constraints. After worklist success, the actual next engineering stage must combine source-preserving annual meteorological candidates with Stage85 manual 2000 Ho1 override by identical original native timestamps, resolve the genuinely hard holds under a source-QC policy, rerun ten-site Post-v5, build all 98 year NC and verify CIME stream mapping. No production run from preliminary NetCDF.

## Stage91 source-schema hotfix (2026-10-26)

Operator reported `ValueError: Empty site in Stage85` immediately after Stage64/74/85 source SHA passed. Stage85's 1,068 approved humidity edit CSV is intentionally **US-Ho1-only** and has no `site` field; Stage91's generic multi-site indexing had incorrectly required it. Fixed source commit `bc11e17db4ed1b8e0a927c32305938490b0b4d9d` blob `0a6ec7563265497e18b2d19810e3f871ec239271` uses the pinned Stage85 *manifest* to supply the exact `US-Ho1` source identity, and rejects conflicting explicit sites. It also verifies all 1,068 Stage85 rows have original QC0 and are humidity edits, with original temperature unchanged. Additional isolated self-tests validate Stage85 missing-site acceptance and multi-site missing-site rejection. This does not change original data or previously generated NetCDF. Source is committed, actual repaired IRIDIS execution pending.

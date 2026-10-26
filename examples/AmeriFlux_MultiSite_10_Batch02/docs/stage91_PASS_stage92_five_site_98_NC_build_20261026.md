# Batch02 Stage91 operator PASS → Stage92 actual missing-five-site forcing and NC previews

Date: 26 October 2026. Actual Stage91 IRIDIS6 operator `WORKLIST PASS`; 98 missing technical annual NC, five original Stage07 humidity-blocked site scopes, historical independent humidity evidence verified.

## Actual Stage91 summary

Five sites are original FLUXNET released met input candidates **without complete QC-v5 forcing**: EML 16y, GLE 16y, Ho1 28y, ICh 19y, ICt 19y. The already existing Stage87 BZS,CMW,Ha1,Ho2,Ho3 **117** annual files are technical previews, source-pinned and not activated. Stage91 original source category counts: Stage64 9,389, Stage74 15,199 numerical shadow + 1,675 original-T science HOLD, Stage85 exactly 1,068 humidity modified/source QC0 2000 Ho1; Stage74/85 overlap 563, Stage64/74 overlap zero. **Do not sum the 563 twice; original time/source identities must be reconciled.**

## Stage92 real forcing engineering rather than a worklist

- [Stage92 driver](../scripts/stage92/92_build_remaining_five_candidate_forcing_and_nc.py) calls [source-pinned adapted original Stage07 QC-v5 engine](../scripts/stage92/qcv5_stage92_integrate_external_RH_sources.py) for actual complete multiyear Stage02 five-site CSV forcing candidates.
- SOURCE SHA checks all original five-site native FLUXNET/ERA companions from preserved Stage07 manifest, all Stage64/74/85 candidate receipts, and Stage91 worklist. Engine reuses original Stage07 value-range checks, short-gap interp and source-replacement ledger; Stage92 adds exact external RH/CDS source candidates at **original/current T and PA** only when T/P align (if not, reject and HOLD).
- Scope: independent Stage64 9,389 and Stage74 16,874 original hard source rows including 1,675 original temperature-science HOLD **as explicitly unapproved TECHNICAL-PREVIEW humidity candidates**, never as validated tower measurements or release consent. 15,199 previously numeric + 1,675 original-T held are distinguishable in all candidate provenance.
- Preserve the Stage85 operator decision: **original 17,294 measured-QC0 Ho1 2000 temperatures in 17,568 native leap-year HH**. On NOLEAP forced year (skip 48 Feb29 measured QC0), **17,246** approved measured-QC0 rows remain and original **274** non-QC0 April/December gapfilled/source rows retain explicit unapproved status. Restore exact original measured-QC0 T even if original QC-v5 earlier engine would have modified some. Exact Stage85 1,068 changed humidity times are keyed from source and not double-overlaid by Stage74. The Ho1 Dec27 QC1-to-QC2 18.746C source transition is **not** silently fixed or accepted.
- For each source that reaches physically numeric forcing and independent original→event audit, creates whole-site CSV in isolated Stage92 root then uses original Stage87 SHA-pinned NetCDF module to build exactly site-year technical-preview NC plus **unactivated** stream text template. If still unresolved source humidity remains, that entire site fails with an explicit operator error and is not declared complete.
- Stage09 Post-v5, model PFT/landunits, sensor height ZBOT, historical site local time/UTC/interval centering, CIME DATM/CDEPS and smoke test remain separate gates. NO production jobs launched.

## One paste on IRIDIS6

Three pinned code inputs: Stage92 driver and Stage92 engine from commit `9b0e3b2f956205f37065b4066f58aa65f80efef4`, Stage87 builder from commit `7e4c3cd653289872d09f7a6a71e75fa35a258c2b`. Verify Git blob SHA for each before execution.

```bash
(
 set -euo pipefail
 REL="examples/AmeriFlux_MultiSite_10_Batch02/scripts"
 STAGE92="9b0e3b2f956205f37065b4066f58aa65f80efef4"
 STAGE87="7e4c3cd653289872d09f7a6a71e75fa35a258c2b"
 BLOB92="4de71a168eecf06e990f32c61919c36cd8243838"
 BLOB92ENGINE="e0c938d1115650db1ffaa4450947b549a514d1f3"
 BLOB87="4f62ba03f52b41b98d7b6db3e89af2bf10bee8a1"
 WORK="$(mktemp -d "$HOME/Batch02_stage92_XXXXXXXX")"
 trap 'rm -rf "$WORK"' EXIT
 BASE="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
 curl -fLsS --retry 3 "$BASE/$STAGE92/$REL/stage92/92_build_remaining_five_candidate_forcing_and_nc.py" -o "$WORK/92_build_remaining_five_candidate_forcing_and_nc.py"
 curl -fLsS --retry 3 "$BASE/$STAGE92/$REL/stage92/qcv5_stage92_integrate_external_RH_sources.py" -o "$WORK/qcv5_stage92_integrate_external_RH_sources.py"
 curl -fLsS --retry 3 "$BASE/$STAGE87/$REL/stage87/87_build_five_verified_Stage07_DATM_noleap_technical_preview.py" -o "$WORK/87_build_five_verified_Stage07_DATM_noleap_technical_preview.py"
 test "$(git hash-object "$WORK/92_build_remaining_five_candidate_forcing_and_nc.py")" = "$BLOB92"
 test "$(git hash-object "$WORK/qcv5_stage92_integrate_external_RH_sources.py")" = "$BLOB92ENGINE"
 test "$(git hash-object "$WORK/87_build_five_verified_Stage07_DATM_noleap_technical_preview.py")" = "$BLOB87"
 python3 -B -c 'import ast,sys;[ast.parse(open(p,encoding="utf8").read()) for p in sys.argv[1:]];print("ALL 3 SYNTAX PASS")' "$WORK"/*.py
 python3 -B "$WORK/92_build_remaining_five_candidate_forcing_and_nc.py" --self-test
 python3 -B "$WORK/92_build_remaining_five_candidate_forcing_and_nc.py" --build --netcdf-module "$WORK/87_build_five_verified_Stage07_DATM_noleap_technical_preview.py" 2>&1 | tee "$HOME/Batch02_Stage92_five_site_build.log"
)
```

Expected if full numeric completion: `STAGE92 FIVE SITE CANDIDATE PASS | five original-source audited forcing CSV; NC preview years 98`. Otherwise `STAGE92 FIVE SITE PARTIAL/FAIL | numeric sites x/5; annual NC y/98; INCOMPLETE marker retained`. If any site fails, inspect only the exact printed site/error and `site_build_summary.json`, not all thousands of prior hard source records. Source/active forcing and model submissions are never touched.

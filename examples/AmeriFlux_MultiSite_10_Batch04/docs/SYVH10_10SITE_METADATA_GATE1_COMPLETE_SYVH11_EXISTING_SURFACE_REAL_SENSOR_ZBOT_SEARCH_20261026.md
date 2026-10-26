# Batch04 SYVH10 actual operator Gate-1 PASS — 10 site source/BIF metadata, surface missing at one path, unresolved sensor height/ZBOT and CIME

**2026-10-26 actual IRIDIS6 operator stdout.** Read-only SYVH10 completed 10/10 station BIF lat/lon and native UTC offsets, following the **existing original USER-APPROVED US-Seg BIF GROUP_ID 1495** exact coordinate/elevation/date source. The source-verified final SYVH9 research ten-site selected seven-met NOLEAP Gate-0 remains **10/10 PASS** with only **3 documented input-precision VPD oversaturations** (US-Rpf 2, US-Syv 1). No native/original/candidate/model file changed. Gate-1 did **not** authorize Post-v5, DATM, CIME, Slurm or CLM-FATES spinup.

Operator read-only output:
- `SYVH10 SOURCE PROVENANCE AND POSTV5 DATM METADATA GATE1 AUDIT COMPLETE`
- `GATE1 10_SITE_MET_NUMERIC True ZBOT_VERIFIED False TIMECENTER_VERIFIED False ACTIVE_CASE_MAPPING_VERIFIED False SCIENCE_RELEASE False`
- Original report `/home/ly3n24/ameriflux_batch04_manual_review/Batch04_SYVH10_Postv5_10site_DATM_metadata_20261026T131846Z_6102179a.json` SHA256 `e788d41c52329cdffc9e3932b2e6eed411ad9502a10069fb11e7326fc4ae531d`.

## Actual site metadata from operator output

| Site | BIF latitude | BIF longitude | Native UTC offset | Years | Reported height candidates (NOT ZBOT) |
|---|---:|---:|---:|---|---|
| US-Rpf | 65.1198 | -147.4290 | -9 | 2008–2024 | 0 |
| US-SP1 | 29.7381 | -82.2188 | -5 | 2000–2020 | `HEIGHTC 24.2 m` (2008) |
| US-SRG | 31.7894 | -110.8277 | -7 | 2008–2025 | `HEIGHTC 0.5 m` |
| US-SRM | 31.8214 | -110.8661 | -7 | 2004–2025 | `HEIGHTC 2.5 m` |
| US-Seg | **34.3623** | **-106.7020** | -7 | 2007–2025 | 0; **prior user-approved Stage02 original BIF group 1495** |
| US-Ses | 34.3349 | -106.7442 | -7 | 2007–2025 | 0 |
| US-Slt | 39.9138 | -74.5960 | -5 | 2005–2022 | `HEIGHTC 9.52 m` |
| US-Syv | 46.2420 | -89.3477 | -6 | 2001–2025 | `HEIGHTC 27.5 m` |
| US-Ton | 38.4309 | -120.9660 | -8 | 2001–2025 | multiple historical `HEIGHTC` values, differing source groups/dates |
| US-Uaf | 64.8663 | -147.8555 | -9 | 2003–2025 | 0 |

**Important:** `HEIGHTC` is vegetation/canopy height, not `TA_F` or `WS_F` observation height. In the SYVH10 script's first version `HEIGHTC_DATE`, `HEIGHTC_STATISTIC_NUMBER` and method strings were overcounted as "height candidates"; even a valid `HEIGHTC` is NOT an acceptable met forcing `ZBOT`. The more scientifically relevant original BIF `VAR_INFO_HEIGHT` must be grouped with exact `VAR_INFO_VARNAME` (TA and wind) and relevant `VAR_INFO_DATE`, distinguishing periods and instruments. Existing [six-site precedent](../../FLUXNET_MultiSite_6/scripts/06_check_surface_zbot_make_datm.py) and [time-varying height precedent](../../FLUXNET_MultiSite_6/scripts/07_make_six_site_datm_timevarying_zbot.py) demonstrate this same principle, including caution about TA/WS mismatch and not extrapolating past a timestamp unless independently justified.

## Actual surface/domain technical findings

For **all ten sites**, the SYVH10 script reported `SURFACE_MISSING_OR_MULTIPLE`, with zero known domain candidates at `/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/<site>/subset_data/surfdata*.nc` (nonrecursive candidate path). This **does not prove surface or domain are globally missing**; they may be nested elsewhere, staged under generated subset paths or referenced by existing case `CaseDocs/lnd_in` files. It would be scientifically unsafe to invent new surface/PFT parameters or choose a non-site-specific generic domain automatically.

## Next source-preserving action — SYVH11, published but not executed on IRIDIS6

New [`stage_syvh11_locate_site_surfaces_BIF_ZBOT_CIME_readonly.py`](../scripts/manual_review/stage_syvh11_locate_site_surfaces_BIF_ZBOT_CIME_readonly.py), pinned GitHub commit **`ddbc515e295f70897a4b911e78178836749b2ac6`**, begins at exact SHA-verified final SYVH9 ten-site research manifest and original Stage05 three-site + Stage08 seven-site provenance.

It audits every original BIF `VARIABLE_GROUP + GROUP_ID` row linking `VAR_INFO_VARNAME / VAR_INFO_HEIGHT / VAR_INFO_DATE`, reports real **TA and wind observation height** evidence separately from `HEIGHTC`, with no ZBOT invented or authorized. It performs a **bounded, site-specific scan** of existing surface/domain NetCDF candidates in original site directories and conventional subset/forcing subdirectories, logging each candidate SHA and point-location difference from the already verified original tower coordinate; also scans only one directory level of expected CTSM case roots for exact site case names and case config file evidence (`lnd_in`, `atm_in`, `env_run.xml`, stream settings), not broad recursive searches of large scratch. Strictly no source/input/met/case/model writes; optional tiny HOME report JSON/TSV only.

Run:

```bash
conda activate clm_fates_env
(
  set -euo pipefail
  BASE="$HOME/ameriflux_batch04_manual_review"
  RAW="https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows"
  COMMIT="ddbc515e295f70897a4b911e78178836749b2ac6"
  REL="examples/AmeriFlux_MultiSite_10_Batch04/scripts/manual_review"
  FINAL="/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/manual_Batch04_SYVH9_12_low_LW_5sites_independent_ERA5Land_research_not_approved/candidate_20261026T121123Z_a8b8146f"
  mkdir -p "$BASE"
  SCRIPT="$BASE/stage_syvh11_locate_site_surfaces_BIF_ZBOT_CIME_readonly.py"
  curl -fLsS --retry 3 "$RAW/$COMMIT/$REL/stage_syvh11_locate_site_surfaces_BIF_ZBOT_CIME_readonly.py" -o "$SCRIPT"
  python3 -B -m py_compile "$SCRIPT"
  python3 -u -B "$SCRIPT" --candidate-dir "$FINAL" --report 2>&1 | tee "$BASE/Batch04_SYVH11_surface_domain_BIF_ZBOT_CIME_inventory.log"
)
```

**Expected:** `SYVH11 SELF-TEST PASS`, `SYVH11 SOURCE PIN PASS final manifest ...`, ten `SYVH11 SITE <site> BIF_TA_HEIGHTS ... SURFACE_DOMAIN_FILES ... CASE_CANDIDATES ...` reports, and `SYVH11 METADATA INVENTORY DONE. NO ZBOT/SURFACE/DOMAIN/STREAM HAS BEEN APPROVED.`. Depending on the actual source data, `BIF_TA_HEIGHTS` may be empty/ambiguous and this is an evidence gap, not a script error. The operator should supply the exact output before further choosing height, generating surface or creating CIME/DATM source files.

**No new manual science choice is required to perform this bounded inventory.** Production model-run release is separate and remains BLOCKED, even though all 10 complete met sources pass seven-field/NOLEAP Gate-0.

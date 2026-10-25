# Batch04 — operator-verified manual three-temperature research candidate assessment

**Operator execution:** IRIDIS6 on 2026-10-25, `clm_fates_env` Python. **Status: `--assess` PASS; `--trial` NOT RUN IN THIS LOG.** Original Stage14/15/FLUXNET sources unchanged.

## Verbatim operator receipt

```text
MANUAL TRIAL SELF-TEST PASS: 3 HH isolated, QC2 ERA-derived provenance, no original overwrite
MANUAL PROPOSAL US-SP1 200010091800 ORIGINAL_T -6.9 ORIGINAL_QC0 TRIAL_T 14.370813 TRIAL_QC2 TRIAL_VPD 10.194556 METHOD EXACT_RECEIPT_VERIFIED_ERA5LAND_T2M_INTERPOLATED_TO_NATIVE_UTC
MANUAL PROPOSAL US-SP1 200010091830 ORIGINAL_T -7.1 ORIGINAL_QC0 TRIAL_T 13.776224 TRIAL_QC2 TRIAL_VPD 9.445459 METHOD EXACT_RECEIPT_VERIFIED_ERA5LAND_T2M_INTERPOLATED_TO_NATIVE_UTC
MANUAL PROPOSAL US-SRG 201903191200 ORIGINAL_T 0.718 ORIGINAL_QC0 TRIAL_T 20.1365 TRIAL_QC2 TRIAL_VPD 17.060332 METHOD MANUAL_INTERPOLATION_BETWEEN_TWO_QC2_ERA_SUBSTITUTED_FLANKS
MANUAL SCIENCE: ORIGINAL 8/8 TEMPERATURE HOLDS STILL UNRESOLVED; US-Syv 606+10 DEFERRED
MANUAL ASSESS ONLY: 0 WRITES, 0 RELEASES
```

| Site | Native local-standard HH | Original TA_F °C | Original TA_F_QC | Proposed TA_F °C | Proposed VPD_F hPa | Research QA label | Original-replacement origin |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| US-SP1 | 2000-10-09 18:00 | −6.900 | 0 | **14.370813** | **10.194556** | **trial QC2** | Exact existing CDS SHA-receipted ERA5-Land 2-m temperature, interpolated in UTC to the original HH clock |
| US-SP1 | 2000-10-09 18:30 | −7.100 | 0 | **13.776224** | **9.445459** | **trial QC2** | Same source/clock |
| US-SRG | 2019-03-19 12:00 | 0.718 | 0 | **20.136500** | **17.060332** | **trial QC2** | (11:30 source `TA_F=19.668°C/QC2` + 12:30 `TA_F=20.605°C/QC2`)/2, explicitly ERA-derived, not independent tower thermometer interpolation |

The script's newly calculated VPD values use the **retained Stage14 RH** at the altered temperature, and check physical saturation closure. The printed 6-decimal temperatures/VPD values are **rounded**; when `--trial` runs, more precise floats are written into **new** research CSVs and the per-event provenance ledger.

The preceding initial execution in conda `(base)` failed to import `numpy`. The operator then switched to the validated `clm_fates_env` (`/home/ly3n24/.conda/envs/clm_fates_env/bin/python3`) and confirmed `NUMPY/NETCDF4 PASS`; later `--assess` ran to completion. **No reason to pip-install or change Python environments.**

## Scientific scope and next command

The original US-SP1 2000 Stage15 research alternative instead interpolated from tower neighbors to **13.1816667°C** and **15.3633333°C**, with trial QC1. **That is a DIFFERENT scientific sensitivity scenario** and must not be overwritten with this ERA5-Land-based trial. The US-SRG manual candidate is also not independent measured tower truth because its flanks are already QC2 ERA-derived values. Both updated-site trial temperatures are **experimental ERA-origin substitutions** and should retain source provenance in their separate ledger.

**Only after the operator accepts these precise three numbers**, the next action is to execute the pinned [`build_manual_T_replacement_trial_only.py`](../scripts/manual_review/build_manual_T_replacement_trial_only.py) with `--trial`, using exactly the existing `clm_fates_env` and downloaded sibling Stage10 helper:

```bash
conda activate clm_fates_env
BASE="$HOME/ameriflux_batch04_manual_review"
python3 -u -B "$BASE/build_manual_T_replacement_trial_only.py" --trial \
  2>&1 | tee "$BASE/manual_three_T_changes_trial.log"
```

This is a **write to a new, uniquely named scratch research candidate directory only**. Expected receipts: two new full site research CSVs (US-SP1 and US-SRG), 10-site *research* manifest, per-event manual provenance, signed SHA receipt and a `NOT_APPROVED_NOT_FOR_DATM_CIME_SLURM_SPINUP` marker. Do **not** claim any trial artifact exists before actual operator `--trial` success output. No original FLUXMET file, Stage14 candidate, Stage15 scenario, other eight selected input files, source-side scientific QC, DATM, CIME or spinup will be intentionally changed.

**Release gate:** Stage14's original **8** tower-temperature source science HOLDs remain; `US-Syv` **606** old science HOLDs plus **10** skipped ERA edge-endpoints stay deferred. **No Post-v5, DATM, CIME, Slurm/model/spinup release** from this candidate.

[Extended original TA windows (7/7 verified, including four 18:00 US-SP1 jumps)](MANUAL_EXTENDED_T_OPERATOR_VERIFIED_2026-10-25.md).

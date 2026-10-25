# AmeriFlux Batch04 Stage12 first application — 143/156 resolved (IRIDIS6 VERIFIED)

**Source:** operator-provided IRIDIS6 stdout, 2026-10-25. Stage12 Python syntax and self-test PASS; five selected site latest source CSVs checked; 5 original BIF coordinates and fixed standard UTC offsets accepted.

| Site | BIF latitude | BIF longitude | UTC_OFFSET | Selected target HH timestamps |
|---|---:|---:|---:|---:|
| US-SP1 | 29.7381 | -82.2188 | -5 | 148 |
| US-Ton | 38.4309 | -120.966 | -8 | 1 |
| US-Seg | 34.3623 | -106.702 | -7 | 4 |
| US-SRG | 31.7894 | -110.8277 | -7 | 1 |
| US-Uaf | 64.8663 | -147.8555 | -9 | 2 |
| **Total unique** | | | | **156** |

The original **155 non-US-Syv HOLD entries**, plus 2 separate Stage07 US-SP1 direct-ERA skip entries, result in **156 distinct native half-hour timestamps**, not 157, because one timestamp overlaps an earlier hold.

## Execution result

```text
STAGE12 SELF-TEST PASS
STAGE12 TARGETS inherited=155, original skipped-SP1-edge=2, unique 156
STAGE12 CDS REQUIRED 8 site-years
STAGE12 NEW/RECOVERED CDS SITE-YEARS 3
STAGE12 RESULT 143 of 156 resolved 13 not resolved
NO ORIGINAL OR STAGE05-11 DATA, DATM, CIME OR SLURM WRITES
```

The execution generated actual updated complete site-derived FLUXMET HH file(s), a full ten-site latest manifest `stage12_repaired_source_candidates.tsv`, and a per-timestamp `stage12_science_decisions.tsv`. The operator's output does not state per-site repaired counts or updated CSV SHA256; retrieve them from the Stage12 receipt rather than guessing.

**New derived directory:**
```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch04/qcv5_stage12_non_syv_repaired/candidate_20261025T055139Z_9bc58872
```

## Acquired/reused CDS inputs in this invocation

- **US-SP1 2008:** 100 requested HH targets; a valid existing `.download.partial` recovered with SHA256 `58239b2baa73832d7248da0f0e730e00f42e075d8b7c9a61b585eb6d0ebc09a9`.
- **US-SP1 2007:** 44 targets; CDS request successfully completed; grid response SHA256 `de7ea5f7754562e93d542c6d62629986b4f1c693c576d64320b0a0946a0042ba`.
- **US-SP1 2000:** 2 targets; CDS request successfully completed; grid response SHA256 `12354219c7fbe62ea2011a3046e0dbaee64b37ae6cae004fc110ad5794d5e4b4`.

## 5 absent site-years: exactly 7 corresponding required grid target timestamps

| Site-year | Grid-required HH targets |
|---|---:|
| US-Seg 2018 | 2 |
| US-Uaf 2004 | 2 |
| US-SRG 2019 | 1 |
| US-Seg 2014 | 1 |
| US-Seg 2016 | 1 |
| **Total** | **7** |

The remaining **13** science targets comprise **7** corresponding to the above missing grid site-years and **6** not automatically resolved despite other grid/source context. The six require inspection of the exact Stage12 `stage12_science_decisions.tsv` statuses to identify physical causes. Do not promise all 13 will resolve after the downloads.

## Next operator command (same pinned Stage12 code; no source overwrite)

```bash
set -o pipefail
BASE="$HOME/ameriflux_batch04_stage12"
python3 -B "$BASE/12_repair_non_syv_science_holds.py" --run --max-downloads 5 \
  2>&1 | tee "$BASE/stage12_complete_five_years.log"
```

The Stage12 code reuses the previously receipted three SP1 datasets, downloads the five missing site-years at most, and recomputes a new Stage12 version **from the pinned Stage11 baseline**. This replaces neither the earlier Stage12 version nor any original Stage05–11 source. On success inspect `stage12_science_decisions.tsv` for any still-unresolved timestamps and capture the produced ten-site selection/SHAs.

**US-Syv 606 original HOLDs and 10 Stage07 missed edge targets remain deferred.** No Post-v5/DATM/CIME or spinup permission is implied by Stage12 derived candidates.

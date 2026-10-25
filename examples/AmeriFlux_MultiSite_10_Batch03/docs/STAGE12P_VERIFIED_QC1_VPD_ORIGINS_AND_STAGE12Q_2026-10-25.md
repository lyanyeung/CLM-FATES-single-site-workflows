# Batch03 Stage12p VERIFIED — 32 QC1 edge differences classified; Stage12q upstream VPD provenance

**Operator log: 2026-10-25 09:19 UTC.** The exact pinned Stage12p Git blob passed source SHA and Python syntax verification, `--self-test`, `--check`, and `--run`. Isolated SHA-receipted IRIDIS6 report:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/stage12p_NR1_Me6_QC1_VPD_neighbor_origin_and_jump_sensitivity_20261025T091906Z_d349135a/`

**Original exact 38 source-native Stage12g VPD jump science holds / 76 adjacent *sides* remain unchanged.** Among 76: 71 original FLUXMET `VPD_F_QC=1` sides and 5 `QC=0` sides. All five QC0 sides numerically match Stage12e. Among QC1 sides, exactly **39 raw `VPD_F` match Stage12e**; the 32 other sides are **24 both-finite-but-different** (US-Me6 22, US-NR1 2) and **8 raw-only-finite** (all US-Me6). There are zero Stage12e-only finite or both-absent sides in this specific 76-side sample.

| Original edge origin class | Sides | Candidate-vs-raw >4hPa | Candidate-vs-Stage12e >4hPa | Candidate-vs-final Stage12g >4hPa |
| --- | ---: | ---: | ---: | ---: |
| Me6 original QC0 both-finite match | 5 | 0 | 0 | 0 |
| Me6 QC1 both-finite differ | 22 | 21 | 4 | 4 |
| Me6 QC1 both-finite match | 35 | 34 | 34 | 34 |
| Me6 QC1 raw-only finite | 8 | 8 | 0 (reference unavailable) | 0 (6 references absent) |
| NR1 QC1 both-finite differ | 2 | 2 | 0 | 0 |
| NR1 QC1 both-finite match | 4 | 4 | 4 | 4 |

**Do not interpret a false >4hPa comparison where the reference is missing as a passed physical check.** These are reference sides, not independent native held times; 3 source-neighbor timestamps are reused, and some Stage12g final reference slots are masked by rejected candidates. A hypothetical new candidate matching a prior research-shadow VPD does NOT grant science or forcing approval. The 38 jump held native timestamps, 48 temperature discrepancy holds, original 233 protected physics holds, site tower QC0 temperature, pressure, clock, and Post-v5/DATM/spinup HOLD are immutable.

### Why Stage12q, rather than changing 4hPa

Direct inspection of pinned [Stage12c](../scripts/stage12/12c_six_site_full_native_shadow_with_held_gaps.py), [Stage12d](../scripts/stage12/12d_native_companion_RH_bulk_gap_rescue.py), [Stage12e](../scripts/stage12/12e_six_site_independent_ERA5Land_gap_rescue.py) and [Stage12g](../scripts/stage12/12g_apply_new_year_ERA5Land_RH_shadow.py) source shows Stage12e is a successor to Stage12d, not the source of every existing Stage12e VPD value. Stage12c builds an original-FLUXMET plus matched-companion ERA baseline and imports Stage12b grid-RH candidate patches; Stage12d fills additional humidity gaps from companion ERA RH; Stage12e fills later gaps using yearly ERA5-Land RH; Stage12g handles still-missing verified-year candidates. Each stage's signed *actual row values and provenance ledgers* must be compared before asserting which stage introduced the 24 different VPD values or why eight raw-finite values remain missing.

[Stage12q exact 76-side C/D/E/G value lineage audit](../scripts/stage12/12q_NR1_Me6_76_edge_stage12c_d_e_g_VPD_lineage_READONLY.py) is the next science-only step. It reads Stage12p's SHA-sealed 76 edges, verifies Stage12c/d/e/g signed report receipts and the two-site snapshot CSV SHA, joins on original exact native timestamps, tests the Stage12e and Stage12g values against the Stage12p edge ledger, and attributes retained Stage12e numbers to signed Stage12b/C, 12d or 12e value changes using original per-stage patch ledgers. It must fail closed on unknown source lineage or missing source artifacts. `--self-test` synthetic only, `--check` read only, `--run` writes only a new isolated SHA-receipted report, never an approved forcing source. **Not yet verified on IRIDIS6.**
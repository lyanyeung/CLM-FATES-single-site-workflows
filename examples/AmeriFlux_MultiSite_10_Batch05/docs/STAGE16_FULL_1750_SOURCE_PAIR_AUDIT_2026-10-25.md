# AmeriFlux Batch05 — Stage16 original tower/MDS/ERA source-pair comparison, actual IRIDIS6 output

## Execution status — completed, read only

Operator log on 2026-10-25 reports `SOURCE VERIFIED`, Python syntax check and self-test PASS, plus

```text
STAGE16 SUMMARY sites=10/10 events=1750 measured=119 MDS=965 ERA=666 approved=0 reports=/iridisfs/home/ly3n24/ameriflux_batch05_stage16/source_pairs_20261025T225516Z_1291407
NEW REVIEW CSV/JSON ONLY; NO ORIGINAL SOURCES/STAGE10/STAGE15/FORCING/MODEL/SLURM CHANGES
```

The same physical folder was echoed as `/home/ly3n24/ameriflux_batch05_stage16/source_pairs_20261025T225516Z_1291407`. Stage16 outputs `stage16_all_1750_source_pair_review.csv` and `stage16_summary.json` are stored on IRIDIS6, not uploaded to GitHub. No forcing, run cases, source time labels or Slurm jobs were altered.

## All 1750 native low derived-RH events

Selected VPD source status: measured QC0=119, good MDS QC1=965, ERA/downscaled QC2=666, total 1,750. Of those 1,559 are water-formula negative RH and 191 are RH in [0%, 1%). Original RH is missing in 1,605 events.

| Original/alternative meteorology diagnostic on the SAME 1750 flagged timestamps | Formula physical | Formula nonphysical |
|---|---:|---:|
| Native MDS `TA_MDS + VPD_MDS` | 700 | 1,050 |
| Native processed ERA `TA_ERA + VPD_ERA` | 1,695 | 55 |
| Direct mix `TA_F + VPD_ERA` | 1,102 | 648 |
| Preserve ERA implied vapor pressure `e_ERA=es(T_ERA)-VPD_ERA`, pair with `TA_F` | 1,580 | 115 (among the 1695 valid ERA self pairs) |

**These diagnostics overlap the same 1,750 records** and are not independent counts. In the last line, 55 ERA-self-invalid records cannot form a physical ERA-implied vapor pressure, so the valid/invalid shadow denominator is 1,695, not 1,750.

Two additional discordance counts: `|TA_F-TA_ERA|>5°C` for **437/1750**; `|VPD_F-VPD_ERA|>5 hPa` for **629/1750**. The counterpart ERA is part of the preprocessed FLUXNET/AMF source package and **not an independent freshly downloaded ERA5-Land analysis**.

## Site-level results

| Site | Low-RH | Selected VPD QC0 | QC1 | QC2 | `TA_F-TA_ERA` magnitude >5°C |
|---|---:|---:|---:|---:|---:|
| US-UiD | 0 | 0 | 0 | 0 | 0 |
| US-UMB | 23 | 0 | 23 | 0 | 0 |
| US-UMd | 15 | 0 | 15 | 0 | 6 |
| US-Var | 62 | 0 | 62 | 0 | 4 |
| US-Vcm | 509 | 93 | 320 | 96 | 124 |
| US-Vcp | 629 | 0 | 172 | 457 | 211 |
| US-WCr | 88 | 26 | 60 | 2 | 5 |
| US-Whs | 1 | 0 | 1 | 0 | 1 |
| US-Wjs | 401 | 0 | 290 | 111 | 76 |
| US-Wkg | 22 | 0 | 22 | 0 | 10 |
| **TOTAL** | **1,750** | **119** | **965** | **666** | **437** |

US-Vcp + US-Vcm + US-Wjs account for **1539/1750=87.94%** of all low-RH records. The operator's primary source-physics priority flag distribution from Stage16 is: ERA_SELF_NONPHYSICAL 55, ERA_IMPLIED_E_INCOMPATIBLE_WITH_TOWER_T 115, ERA_SELECTED_EXTREME_LOW 609, MDS_SOURCE_EXTREME_LOW 852, MEASURED_EXTREME_LOW 119; these five reason flags sum to 1,750 but are not the Stage15 hierarchical source-QC reason categories.

## Scientific interpretation: not a replacement recommendation

The Stage16 paired-source results show why swapping `VPD_F` to the supplied processed `VPD_ERA` is **not** a uniform solution:
- ERA's own paired temperature/VPD is mathematically coherent in 1695 cases, but directly pairing `VPD_ERA` to selected tower `TA_F` is mathematically inconsistent in 648.
- Conserving `e_ERA` and using `TA_F` reduces invalid pairings to 115 of 1695, but this hypothetical transformation does not establish local atmospheric realism or an authorized humidity repair.
- `VPD_F_QC=2` already represents ERA-downscaled processing provenance, so switching to the same source cannot independently verify it.
- Good MDS flags denote provider processing/QC, not physical approval: 1050 MDS pairs violate this particular water-RH formula, despite 700 feasible pairs.
- Original metadata on local clock, UTC offset, site coordinates/elevation, raw sensor variables and processing method must be verified before an independent reference such as reanalyzed native ERA5-Land or local independent stations can be used scientifically.
- The 27 measured QC0/0 near-zero formula-negative cases retain native RH≈0, small equation-dependent differences and unresolved source processing convention. Do not auto overwrite them.

## Next recommended work

Stage17 should **group the 1750 source-timestamp cases into native contiguous half-hour episodes** and produce a prioritized per-episode manifest rather than running more math screens over all 3.5M records. Include site, start/end (unaltered native local printed time), number of half-hours, source QC0/1/2 mix, ERA-self and vapor-pressure shadow failures, tower–ERA >5°C, and a metadata gate for any future independent met reference. The manifest is an evidence request, **not** a substitute forcing. Stage17 code and its actual execution status are tracked in the Batch05 README.

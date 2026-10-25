# AmeriFlux Batch05 — Stage11: 1,750 humidity review ledgers verified

**Real IRIDIS6 run, 2026-10-25:** pinned original Stage11 script passed SHA, syntax, self-test, and `STAGE11 SUMMARY sites=10/10 events=1750 negative=1559 nonnegative_below1=191 files_valid=10`. All 10 CSV reports under `/iridisfs/home/ly3n24/ameriflux_batch05_stage10/review_20261025T180413Z_682688` and `audit_summary.json` match. **Read-only. No forcing or report changes.**

## Stage11 actual results

| Site | All low-RH cases | Unapproved interpolation physically feasible | Lacks both QC0/0 anchors within 3h | Bracketed interpolation nonphysical | ERA/tower-T physical holds |
|---|---:|---:|---:|---:|---:|
| US-UiD | 0 | 0 | 0 | 0 | 0 |
| US-UMB | 23 | 7 | 16 | 0 | 0 |
| US-UMd | 15 | 0 | 15 | 0 | 0 |
| US-Var | 62 | 29 | 33 | 0 | 31 |
| US-Vcm | 509 | 31 | 474 | 4 | 54 |
| US-Vcp | 629 | 35 | 594 | 0 | 6 |
| US-WCr | 88 | 5 | 83 | 0 | 9 |
| US-Whs | 1 | 0 | 1 | 0 | 0 |
| US-Wjs | 401 | 121 | 280 | 0 | 69 |
| US-Wkg | 22 | 1 | 14 | 7 | 1 |
| **Total** | **1,750** | **229** | **1,510** | **11** | **170** |

The three interpolation statuses sum to 1,750. ERA holds **overlap** these groups and are not additional unique records. The original Stage10 QA counts also matched `MDS_FEASIBLE=700`, `MDS_NONPHYSICAL=1050`, `ERA_HYPOTHETICAL_ERA_VAPOUR_PAIR_FEASIBLE=1580`, original RH missing 1,605.

`TA_F_QC/VPD_F_QC` breakdown within 1,750: `0/0=119`, `0/1=961`, `0/2=479`, `1/1=4`, `1/2=128`, `2/2=59`. No field is approved for correction by these reports.

## Important exception: 27 apparently negative **measured** TA/VPD cases

All 27 have `TA_F_QC=VPD_F_QC=0`: **US-WCr 26**, **US-Vcm 1**. The Stage11 source examples show original US-WCr `RH=0%` with derived RH approximately `-0.1%` for the continuous 2025-08-25 period. US-Vcm on 2025-10-13 17:00 has `TA_F=11.686°C`, `VPD_F=13.731 hPa`, original RH `0.08066284%`, derived water RH `-0.022119%`. Differences this small could arise from rounding or native saturation vapor pressure choices and **do not alone establish faulty sensors**. Do not auto-replace these `QC0/0` measurements with ERA or interpolation.

## Scientific next step

The [Stage12 original-data temporal context review exporter](../scripts/stage12/12_export_priority_low_RH_source_context_readonly.py) collects original native TA, VPD, RH, consolidated and MDS QC, MDS TA/VPD and ERA TA/VPD across unchanged printed timestamps from -3h to +3h around four **overlapping** categories of priority events: 229 *unapproved* bracketed interpolation candidates; 11 bracketed interpolation failures; 27 QC0/0 measured negative cases; 170 ERA humidity-pair holds. The operator must examine source-context before deciding **whether** any repair is justified. This Stage12 script creates new report CSV/JSON only and refuses to edit original source/Stage10 reports/forcing. Its execution is pending.

No modified forcing, clock shifts, model cases or Slurm jobs are authorized.

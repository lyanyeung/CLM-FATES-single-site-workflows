# AmeriFlux Batch05 — Stage17 executed: 522 native-HH episodes, human-review gate

**Actual IRIDIS6 operator execution, 2026-10-25 23:06 UTC.** Pinned GitHub Stage17 source verified; syntax, self-test and original 1,750-HH/10-site inputs passed. Produced **new review-only** evidence manifests, without changing original tower data, previous reports, forcing, model cases or Slurm.

```text
STAGE17 AGGREGATE {"episodes": 522, "events": 1750, "priority_tiers": {"P1_MEASURED_OR_ERA_INVALID": 39, "P2_MIX_OR_LONG_EPISODE": 89, "P3_CONTEXT_AND_INDEPENDENT_REFERENCE": 394}}
STAGE17 SUMMARY sites=10/10 original_HH=1750 episodes=522 approved=0 reports=/iridisfs/home/ly3n24/ameriflux_batch05_stage17/episode_manifest_20261025T230607Z_1291407
ONLY NEW EVIDENCE REQUEST CSV/JSON; NO ORIGINAL/OTHER_REPORTS/FORCING/MODEL/SLURM WRITES
```

The `/home/ly3n24/...` variant of the directory was also printed by the operator. Files: `stage17_episodes_evidence_requests.csv`, `stage17_site_metadata_gates.csv`, `stage17_summary.json`. Source files stay on IRIDIS6.

## Distribution

| Tower | Source low-RH HH | Native contiguous abnormal episodes | P1 episodes |
|---|---:|---:|---:|
| US-UiD | 0 | 0 | 0 |
| US-UMB | 23 | 9 | 0 |
| US-UMd | 15 | 6 | 0 |
| US-Var | 62 | 37 | 0 |
| US-Vcm | 509 | 109 | **37** |
| US-Vcp | 629 | 172 | **1** |
| US-WCr | 88 | 25 | **1** |
| US-Whs | 1 | 1 | 0 |
| US-Wjs | 401 | 153 | 0 |
| US-Wkg | 22 | 10 | 0 |
| **TOTAL** | **1,750** | **522** | **39** |

Priority episodes: P1 = 39 (7.5% of 522), P2 = 89 (17.0%), P3 = 394 (75.5%). The priority-tier definitions reflect the Stage17 algorithm, not science-approved corrections: P1 includes any original `VPD_F_QC=0` source observation *or* an internally nonphysical ERA pair; P2 includes ERA e/tower-T incompatibility or episodes >=12 contiguous original half-hours; other episodes are P3. P2 and P3 are **not automatically safe to repair**.

## Most important human-review P1 episodes, native local-standard printed timestamps

| Episode | Native start — end | HH | Source evidence | Human decision question |
|---|---|---:|---|---|
| US-WCr_E0025 | 2025-08-25 13:00 — 2025-08-26 01:30 | 26 | 26 source measured QC0 and near-zero original RH | Verify original RH-zero floor, native VPD formula, instrument source, source-level QC before treating ~-0.1pp formula residual as a sensor failure |
| US-Vcm_E0004 | 2007-12-15 21:00 — 2007-12-16 06:00 | 19 | ERA selected QC2: 19 internally nonphysical source pairs | Verify original ERA downscaling, temperature/humidity unit/phase and original station/local time before alternate reference |
| US-Vcm_E0001 | 2007-01-17 04:00 — 08:30 | 10 | 10 internally nonphysical ERA source pairs | Same provenance check, particularly for winter temperature |
| US-Vcm_E0007 | 2008-02-06 03:30 — 08:00 | 10 | 10 internally nonphysical ERA source pairs | Same winter provenance check |
| US-Vcm_E0106 | 2025-10-13 15:30 — 17:00 | 4 | Original measured QC0, including source Magnus-screen RH=-0.022% at 17:00 | Check original RH≈0.0807%, formula sensitivity: Buck≈0.039%; no automatic measured-value overwrite |
| US-Vcp_E0116 | 2011-01-01 07:00 — 08:00 | 3 | ERA selected QC2: 3 internally nonphysical pairs | Verify early-January original ERA variable pair |

Many additional US-Vcm P1 events have original QC0 observations with 0% < implied RH <1%, for which genuine local air humidity, the original instrument and algorithm should be reviewed. Low RH alone is not source sensor proof. Date/times are native printed labels; do not invent UTC conversions.

## Decision as of Stage17

**The user asked whether human review is necessary and, only if none is needed, to modify the forcing. There are genuinely unresolved human-review tasks. No batch replacement, auto clipping or unconditional ERA/MDS substitution is scientifically authorized.** All 522 episodes and 1,750 records remain `HOLD_NOT_APPROVED`. The 1,368 anomalies not among the earlier Stage12 priority list now have episode-level review status but do not thereby gain detailed original-context validation.

What can be done without manually examining 1,750 rows: select the **39 P1 episodes**, produce compact source-context files for those only, request source BADM/processor provenance and original independent sensor/ERA5-Land corroboration. A strict review decision requires for each episode a verified original tower time scale and sensor status, an independently defensible replacement, preservation of source provenance and physical consistency, and explicit QA sign-off.

The Stage17 report enumerates all P1 rows already. On IRIDIS6, extract a copy without source mutation:
```bash
python3 - <<'PY'
import csv
from pathlib import Path
src=Path.home()/"ameriflux_batch05_stage17/episode_manifest_20261025T230607Z_1291407/stage17_episodes_evidence_requests.csv"
with src.open(newline="", encoding="utf-8") as f:
    rows=list(csv.DictReader(f))
p1=[x for x in rows if x["priority_tier"]=="P1_MEASURED_OR_ERA_INVALID"]
assert len(rows)==522 and len(p1)==39
print("P1 EPISODES 39 OF 522")
for x in p1:
    print(x["episode_id"],x["native_start"],x["native_end"],
          "HH="+x["half_hours"],"QC0="+x["qc0_measured_HH"],
          "ERA_self_nonphysical="+x["ERA_internal_nonphysical_HH"])
PY
```

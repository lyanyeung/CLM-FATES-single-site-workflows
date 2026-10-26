# Batch04 — operator manual SCIENCE decision: retain original US-SP1 2008 temperature, preserve existing Stage14 humidity treatment

**Date:** 2026-10-26 (the operator's decision follows the supplied source-verified Jan/Feb 2008 temperature panels and native half-hour series).

## Direct user decision, scope and action

**USER DIRECTION (explicit):** `我认为这里都应该使用TA_F，人工决定是这样的。下面继续吧，还有没有要人工决定的站点。`

This answers the human-review request about **US-SP1 2008-01-15 through 2008-01-17 and 2008-02-02 through 2008-02-04**, including exact Stage13 focal QC0 temperatures **2008-01-16 08:00 (−8.211°C), 08:30 (−4.365°C) and 2008-02-03 08:00 (−3.613°C)**.

**Binding operational choice for Batch04 research candidates:**
- **KEEP `TA_F` from the original tower** throughout those 2008 cold episodes. **No point or interval reanalysis temperature replacement**, no ERA bias adjust, no QC0→QC2 relabel of original TA.
- **Retain existing Stage14 independent ERA5-Land-based humidity/VPD physical-closure candidates** for the three explicit Stage13 impossible original TA/VPD pairs; Stage14 did not change tower temperature, and has separate complete-source SHA receipts.
- This user instruction does **NOT** rescind separate operator choices already applied to **US-SP1 2000-10-09 18:00/18:30** (ERA5-Land two-HH research trial) and **US-SP1 2007-10-15–18 + 22–23** (six-day 137-HH daily local QC0 bias-adjusted `TA_ERA` research trial, parent SHA `357a0c89892365e41e1b932663953fcff33487a2cbf6171ba3b9347b7482a9b0`).
- **US-Seg 2016-12-27 18:00**: based on existing contiguous native wintertime cooling, recommend **KEEP original `TA_F=0.015°C/QC0` provisionally**; the already-built Stage14 US-Seg VPD closure **2.63121106028 hPa** remains available. Explicit user direction above refers to the **US-SP1 2008** plots, not a new global approval for US-Seg.
- **This is a science ledger / input-selection decision only**. No need to re-run Stage14, repair 137 October 2007 points, overwrite original source, or alter published SHA-pinned experimental candidates. The eight source-era original HOLD ledger events remain as archival provenance; each separately adjudicated research treatment should be recorded without lying that original FLUXNET QC was corrected. Any Post-v5/DATM/spinup release remains a separate gate.

## Remaining Batch04 human-review priorities (after Stage12/14 + operator decisions)

All ten sites and known source HOLD counts come from Stage11 and later Stage12/Stage14 source checks:

| Site | Current state / what is known | Additional manual T decisions |
| --- | --- | --- |
| US-SP1 | Stage14 VPD physics / Oct 2007 six-day research trial / Jan–Feb 2008 user explicitly retain original TA | **NO**, 2008 human decision recorded |
| US-SRG | One Mar 2019 original-source temperature substituted by user-selected separate ERA-origin midpoint candidate, full CSV independently validated | **NO** for this original T event |
| US-Seg | Stage14 humidity-only candidate at 2016-12-27 18:00; sustained native overnight cooling; retain TA provisionally | **NO immediate extra repair**, formally retain science provenance |
| US-Rpf, US-Ses, US-Slt, US-SRM, US-Ton, US-Uaf | Earlier Stage07–12 repaired or scientifically screened known non-Syv targets (non-Syv Stage12 **148/156 repaired**, remaining **8** original-T conflict events all in SP1/SRG/Seg) | **No other named original T-science HOLDs in verified 8-event remainder**; final Post-v5 QA still required |
| **US-Syv** | **606 Stage05 original inherited science HOLD entries**, plus **10 Stage07 original paired ERA-boundary skips**, possible overlap; deliberately not included in Stage12 science repair | **YES, this is the outstanding untriaged SITE**; classify grouped episodes before requesting human intervention |

**Do not infer 606+10=616 unique HH**: union by native TIMESTAMP_START required; several legacy holds/ERA edge skips may refer to the same original half-hour.

## Next focused step

Run one read-only, source-pinned **US-Syv 606 + 10** study; group the hold reasons by half-hour and contiguous events, print original and current Stage07 derived TA/VPD/RH/QCs and paired source `TA_ERA` / `VPD_ERA` only for meaningful example cases, plus physical admissibility. Only ask the operator to decide genuinely ambiguous cases after grouping. Straight physical invalidity can follow already user-approved source-limited temperature-preserving VPD/Humidity repair rules when its physics and provenance supports a valid replacement; avoid indiscriminate source overwrites.

No model/Post-v5/DATM/CIME/Slurm/spinup operations or change of user decision.

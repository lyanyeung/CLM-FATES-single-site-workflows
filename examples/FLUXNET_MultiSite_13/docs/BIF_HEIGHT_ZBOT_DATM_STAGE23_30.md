# BIF height policy, exceptional stations, and 271 annual DATM files

**Date:** 18 October 2026. **Status:** scientifically provisional. This describes actual Stage 29b + Stage 30 data preparation, not independent evidence that every station's meteorological height has been historically constant.

## 1. Source and meaning of ZBOT

The model DATM contains seven meteorological fields — `TBOT`, `QBOT`, `PSRF`, `FSDS`, `FLDS`, `WIND`, `PRECTmms` — and `ZBOT` (met reference height). The rule for **11 BIF-supported stations** is to map the documented `TA_F` **air-temperature sensor height**, *not* the EC flux measurement height, tower top, mean canopy height, or the `WS_F` anemometer height, to `ZBOT`.

Stage 23/24 audited source BIF station files, duplicate/dated records and TA/WS heights. Stage 29b preserves original BIF effective datetimes and applies the latest known TA height at or before each 30-minute model forcing instant (piecewise constant). For events not exactly on a 00/30 minute boundary, the new height is applied at the next appropriate forcing instant; **source event dates are not rounded**. Stage 29b also records and flags historical times before the first available BIF TA epoch: the earliest known TA height may be *extrapolated backward* only under the explicitly selected provisional assumption.

The existence of a static single BIF height **does not prove** there were no unrecorded historical sensor moves. Wind data were **not** vertically adjusted to compensate for any TA/WS height separation. A large separation does not itself show numerically wrong forcing, but creates a physically relevant representativeness/surface-layer question.

## 2. All sites, height policy and annual DATM counts

| Site | MET years | Annual files | Height mode and known first/reference height | Evidence and caveat |
|---|---|---:|---|---|
| DE-Lnf | 2002–2024 | 23 | **44.0 m STATIC** | Published *TA measurement* height, not BIF; entire-period constancy assumed |
| DE-Obe | 2008–2025 | 18 | **30 m STATIC** | BIF TA; all 52,560 early half-hour records use extrapolated earliest documented height |
| ES-Agu | 2006–2024 | 19 | **2.7 m STATIC** | BIF TA |
| ES-LJu | 2004–2024 | 21 | **2.5 m STATIC** | BIF TA; 5,762 early half-hours use earliest known TA height |
| IT-Col | 1996–2014 | 19 | **32.0 m STATIC PROXY** | Paper reports *measurement height (MH)*, **not confirmed TA sensor height** |
| DE-Gri | 2004–2025 | 22 | **2.0 m STATIC** | BIF TA |
| DE-RuR | 2011–2025 | 15 | **DYNAMIC**, first 2.58 m | Multiple dated BIF TA epochs |
| FI-Hyy | 1997–2025 | 29 | **DYNAMIC**, first 33.6 m | Multiple BIF TA epochs; 122,640 half-hours have TA/WS height difference >3 m |
| FI-Let | 2010–2025 | 16 | **DYNAMIC**, first 25.7 m | Multiple BIF TA epochs; one early extrapolated record |
| FR-Pue | 2000–2025 | 26 | **DYNAMIC**, first 11.5 m | Multiple BIF TA epochs |
| GF-Guy | 2004–2025 | 22 | **57 m STATIC** | BIF TA |
| IT-MBo | 2003–2025 | 23 | **DYNAMIC**, first 3.48 m | Multiple dated BIF TA epochs |
| IT-Tor | 2008–2025 | 18 | **1.8 m STATIC** | BIF TA |
| **Total** | | **271** | **5 BIF dynamic + 6 BIF static + 2 literature static** | All scientifically provisional |

Early-extrapolation counts are taken from the recorded audit checkpoint; use Stage29b's **site/year audit CSV** as the authoritative event ledger, especially if source BIF releases change.

## 3. DE-Lnf: 44 m with explicit published TA evidence

**Jürgensen, J., Muhr, J. & Knohl, A. (2021).** *Variations of the Oxidative Ratio across Ecosystem Components and Seasons in a Managed Temperate Beech Forest (Leinefelde, Germany).* **Forests**, 12(12), 1693. [https://doi.org/10.3390/f12121693](https://doi.org/10.3390/f12121693).

The article's methods report **air temperature at 44 m above ground** measured using a **Vaisala HMP45A** temperature/humidity sensor. This is direct documentary evidence for TA observation height; it is **not** simply an assumption that the EC tower and TA sensor share a level. **Limit:** using 44.0 m *statically from 2002 through 2024* assumes no undocumented historical movement, which that paper alone does not prove. Stage 30 writes this as a provenance-tagged **STATIC** candidate rather than fabricating dated BIF epochs.

## 4. IT-Col: 32 m is only a measurement-height proxy

**Keenan, T. et al. (2009).** *Improved understanding of drought controls on seasonal variation in Mediterranean forest canopy CO₂ and water fluxes through combined in situ measurements and ecosystem modelling.* **Biogeosciences**, 6, 1423–1444. [https://doi.org/10.5194/bg-6-1423-2009](https://doi.org/10.5194/bg-6-1423-2009).

Table 1 lists **Collelongo MH = 32 m** for a measurement period including **1998–1999**. It does **not** identify 32 m as the **air-temperature sensor installation height**. The Stage 30 decision uses **32.0 m static throughout 1996–2014 only as a provisional modelling proxy**, not as an actual BIF observation. Papers and stations may report tower heights, EC levels and TA levels differently. Site correspondence/instrument logs or an IT-Col ZBOT sensitivity analysis remain necessary before making a verified TA-height claim.

## 5. Stage 29b → Stage 30: exact output provenance

- **Stage 29b:** BIF-derived ZBOT only for 11 sites, created **229 yearly full-DATM NetCDF** plus **229 yearly ZBOT-only NetCDF**. DE-Lnf and IT-Col were initially **blocked** from being silently assigned EC or wind height.
- **Stage 30:** produced **23 + 19 = 42** further yearly DATM/ZBOT files. Its preflight independently checked Stage 28 13-site MET/BIF provenance, the earlier 229 annual DATM and 229 ZBOT SHA256 values. Report: 42 newly created, **271 consolidated**; earlier 229 unchanged and SHA256-verified.
- Each full annual DATM has **17,520 time records**, 30-minute spacing and `noleap` convention. It stores `TBOT`, `QBOT`, `PSRF`, `FSDS`, `FLDS`, `WIND`, `PRECTmms`, `ZBOT`. Outputs are **PROVISIONAL**.
- **Do not infer DATM paths from names**. Stage29b and Stage30 may store annual files in separate experiment directories and use `_PROVISIONAL.nc`. Use the consolidated Stage30 SHA256 manifest, which contains precise per-file paths.

Stage 30 report root:

`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET_13_ZBOT_DATM_STAGE30_20261018_055940_1008203/reports`

Consolidated inventory:

`04_consolidated_13site_271_DATM_SHA256_manifest.csv`

The original source ZIP/CSV/BIF, processed forcing, height-only/full-DATM NetCDF and per-record evidence remain on IRIDIS. Only code, documented assumptions and safe aggregate summaries belong on public GitHub.

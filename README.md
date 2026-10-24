# CLM-FATES single-site workflows


## Stage82 — DATM case integration preflight (read-only)

After the operator-confirmed successful Stage81 **213 annual NC / 10-site** technical build, next run the [Stage82 read-only case-integration and NetCDF integrity check](examples/AmeriFlux_MultiSite_10/scripts/stage82/README.md). It SHA-verifies the Stage80/81 source receipts and annual files, validates sample NOLEAP NetCDF, and optionally inventories an actual existing CIME case (`--reference-case`) without changing it. Further tasks: verify DATM/CDEPS stream format, model domain, native station timestamp centering, and site-specific ZBOT sensor height (notably CA-Cbo/CA-Man) before an isolated 1–5-day smoke test. **Do not submit production spin-up or activate Stage81 placeholder stream templates yet.**

## Stage81 FINISHED on IRIDIS6 — 213 annual DATM NetCDF + 10 unactivated stream templates (24 October 2026)

**User-provided actual completed Stage81 output (not independently inspected from GitHub):** Stage81 `--self-test`, `--check` and `--build` all succeeded using the immutable Stage80 selection (18 original RH<1% native-ERA5 joint replacements, 1,091 original RH1–5% rows preserved). The script reports **10/10 sites; 213/213 yearly 30-minute NOLEAP NetCDF files** passing its annual readback check, and **10/10 DATM stream TEMPLATE files generated, NOT ACTIVATED**. Output and per-file SHA source-provenance manifest: `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports/stage81_DATM_technical_20261024T162235Z/` (`manifest.json`).

Annual files per station: BR-Ma2 **18** (1999–2016); CA-Ca3 **24** (2001–2024); CA-Cbo **29** (1996–2024); CA-LP1 **18** (2007–2024); CA-Man **15** (1994–2008); CA-TP1, CA-TP3 and CA-TP4 **22 each** (2002–2023); US-Aud **23** (2002–2024); US-Bar **20** (2004–2023). The metadata source is the existing point-surface grid coordinates, and all `ZBOT` are **UNRESOLVED**. The NetCDF science/case activation gate still requires validated sensor heights (particularly unresolved CA-Cbo and CA-Man), local timestamp and interval-centering policy, the actual point-domain and correct CIME DATM/CDEPS stream syntax, and a smoke test. **Do not call this an activated or scientifically released DATM**; no existing CSV, CIME case, DATM stream, or Slurm task was changed.

See [Stage81 build documentation](examples/AmeriFlux_MultiSite_10/scripts/stage81/README.md) and its SHA-pinned inputs. Stage80 RH repair and Stage81 file generation are now complete; proceed to case-specific coupling/provenance checks, not another ERA5 data-repair loop.

## Stage80 completed — 10-site forcing final; Stage81 DATM generation (24 October 2026)

**Verified on IRIDIS6 by operator log:** Stage80 self-test, full read-only ten-site audit, and full candidate generation **all PASS**. Output: `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports/stage80_RH_lt1_final_20261024T123353Z/`. **Only 18 original RH<1% records** replaced with native ERA5 jointly recomputed T/D2m/P; **1,091 original RH1–5%** and every other Stage75 value retained. Selected four new full forcing candidates (CA-Ca3 7; CA-Cbo 2; CA-Man 1; US-Bar 8) plus six unchanged originals. Stage80 flags **17 operator-accepted RH/T half-hour edge warnings** and preserves prior Stage74 CA-Man independent 18-row amendment. Selected ten-site checksum manifest: `10_site_selected_forcing_sources.tsv`. **RH repair now complete**.

[**Stage81 DATM technical NetCDF generator**](examples/AmeriFlux_MultiSite_10/scripts/stage81/README.md) converts this exact checksum-pinned 10-site selection to annual 30-min NOLEAP CLM1PT-style NetCDF, with `SHUM` from Stage80 `QBOT`, measured-model-grid site coordinates from existing point surfaces and 10 unactivated DATM legacy XML stream templates. It does not fabricate ZBOT or change temporal support. Scientific model activation remains held for CA-Cbo/CA-Man sensor height, actual case domain/streams setup and interval centering. No active DATM or Slurm job automatically changed.

## ACTIVE Batch01 operator rule — only original RH <1% replaced (24 October 2026)

**LATEST USER DECISION, superseding Stages77–79's broader low-RH replacement and edge-review instructions.** For the ten Stage75 Batch01 selected forcings: replace **only the 18 ORIGINAL half-hour records with RH<1%**, always using the already-computed same-source **native ERA5 T2m + 2m dewpoint + surface pressure** joint meteorological state (`TBOT`, `TA_USE`, `QBOT`, `PSRF`, `VPD_USE`). Counts: **CA-Ca3 7, CA-Cbo 2, CA-Man 1, US-Bar 8**. Keep **every other row unchanged**, including **all 1,091 original RH 1–5% records** (CA-Ca3 34; CA-Cbo 26; CA-Man 120; CA-TP4 6; US-Aud 874; US-Bar 31), and preserve the Stage75 CA-Man prior Stage74 approved edits as baseline. The older **all-1,109 RH<5% Stage77 trials are historical alternatives, NOT the current selected forcing version**.

[**Stage80 final operator scope and 10-site selected version workflow**](examples/AmeriFlux_MultiSite_10/scripts/stage80/README.md) builds **four complete SHA-pinned candidate forcing CSVs (18 ERA5 replacements only)** and a ten-site manifest (four new candidates + six unchanged Stage75 paths), with exact every-row diff verification, full NOLEAP/physics checks and a change ledger. The 89 Stage78 new/worsened RH/T edges and Stage79 source-switch findings relate to the **superseded 1,109-row trial**; they do not block implementing the user's narrower replacement decision. Any substantial boundary steps caused by the **18 retained ERA5 corrections** are logged as **explicitly operator-accepted risk**, not automatically repaired by changing neighbors. ERA5 LST/UTC/half-hour averaging remains a documented source-provenance caveat; no existing active CIME/DATM case or Slurm job is modified.


### Stage79 transition-specific native ERA5 diagnosis (24 October 2026)

**Observed Stage78 89-edge classification from IRIDIS6:** CA-Ca3 13, CA-Cbo 18, CA-Man 42, CA-TP4 5, US-Aud 0, US-Bar 11. Site-specific examples reveal *new* half-hour RH steps of **84.37 pp (CA-Man), 69.85 pp (US-Bar), 67.02 pp (CA-Cbo), 56.29 pp (CA-TP4) and 44.91 pp (CA-Ca3)** where the previous source had much smaller steps. These are actual before/after boundary risks, not just Stage77's 179 provisional old-neighbor flags. **Do not mark production MET ready solely based on thermodynamic closure or elimination of RH<1**.

[Stage79](examples/AmeriFlux_MultiSite_10/scripts/stage79/README.md) independently compares the **actual native ERA5 T/D2/P RH on BOTH sides** of all 89 edges with the unmodified tower neighbors, plus exact-time FLUXMET QC columns when present. It forms an evidence-based source-switch vs ERA-internal-step classification, preserves all **1,109 operator-directed ERA substitutions as SHA-pinned trial candidates**, and generates only new audit reports. Missing independent local-standard-time/UTC and 30-minute interval verification remains an explicit model-production HOLD. Never auto-overwrite unflagged QC0 observations or blend incompatible moisture data merely to force smoothness.

### Stage78 actual trial edge audit completed (24 October 2026)

**User-confirmed Stage78 execution:** exact SHA-pinned Stage77 native ERA5 trial candidates **6/6**, with **1,109/1,109 recomputed RH<5% half-hours** (six changed sites) and 4 unchanged site inputs, have been included in the *10-site candidate manifest*. Full old-to-old vs new-to-new consecutive half-hour edge comparison succeeded. Reports are in `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports/stage78_1109_operator_versioned_selected_boundary_20261024T115621557398Z/`.

| Site | Recomputed RH<5% rows | affected 30-min edges | old RH edge ≥25 pp | new RH edge ≥25 pp | edges flagged for targeted review |
|---|---:|---:|---:|---:|---:|
| CA-Ca3 | 41 | 50 | 0 | 13 | 13 |
| CA-Cbo | 28 | 51 | 22 | 20 | 18 |
| CA-Man | 121 | 190 | 81 | 44 | 42 |
| CA-TP4 | 6 | 10 | 3 | 5 | 5 |
| US-Aud | 874 | 1,031 | 3 | 1 | **0** |
| US-Bar | 39 | 56 | 3 | 11 | 11 |
| **Total** | **1,109** | **1,388** | **112** | **94** | **89** |

**Interpretation:** The 179 flagged by Stage77 used new RH compared with *old-neighbor* values and are not 179 confirmed newly introduced discontinuities. Stage78 finds **89 affected half-hour edges for targeted source/clock/discontinuity review**; these are *edges, not necessarily 89 separate affected records or mandatory re-edits*. Some groups overall improve even where individual boundaries worsen. CA-Ca3 and US-Bar merit first review because the number of RH≥25 pp edges rose; US-Aud creates **0 new/worsened large RH or >10°C T edges** despite 874 native ERA substitutions. Final RH<1%=0 in all six native trials; 65 original-targeted US-Aud rows remain RH1–5% based on ERA5; this is a genuine co-sourced ERA result, not an incomplete replacement.

**Decision:** all 1,109 replacements are **scientifically chosen by the operator** and **physically validated in independent trial files**, but **no active DATM/CIME/Slurm input has been changed**. Before production activation, inspect actual worsened edge groups (especially 13 CA-Ca3, 11 US-Bar, 5 CA-TP4) and independently confirm site LST↔UTC / interval-centering. Preserve original checksums, Stage77 replacement ledgers, and Stage78 warnings. [Stage78 workflow](examples/AmeriFlux_MultiSite_10/scripts/stage78/README.md).

### Stage77 IRIDIS6 execution — actual trial complete (24 October 2026)

**Verified user-provided run log:** all 45 native CDS ERA5 source requests were completed; `--check` passed for all **1,109** RH<5% events across six Batch01 sites, and the **corrected Stage77 `--trial` finished**: CA-Ca3 41, CA-Cbo 28, CA-Man 121, CA-TP4 6, US-Aud 874, US-Bar 39. Each entire forcing CSV passed Stage58 structural/thermodynamic checks; only the five coupled fields at selected timestamps were edited; the original inputs and model cases were not modified. The six full **TRIAL_NOT_PRODUCTION** candidate files and per-timestamp ledgers are on IRIDIS6 at `/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10/reports/stage77_1109_RH_lt5_fixed_20261024T114333Z/`.

**RH<1 fell from 18 to 0 across these six trials**, and 65 ERA5-replaced US-Aud records still have RH<5% (valid dry reanalysis conditions, not an unsuccessful replacement). Stage77 printed **179 rows with at least one RH boundary-step magnitude >=25 percentage points compared against the neighboring ORIGINAL rows**: CA-Ca3 35, CA-Cbo 16, CA-Man 96, CA-TP4 5, US-Aud 1, US-Bar 26. **These 179 are screening warnings, NOT 179 demonstrated NEW discontinuities**. For automatic, **full-file original-to-original versus final-to-final 30-minute edge comparison**, SHA-pinned selection of the six corrected forcing candidates together with the four unchanged stations, and a focused *new/worsened-only* scientific review queue, run [Stage78](examples/AmeriFlux_MultiSite_10/scripts/stage78/README.md). This finalizes **candidate** selection by manifest; it does **not** overwrite DATM/CIME/production input paths. If two adjacent RH<5 observations were both changed, Stage77's original-neighbor boundary screen may overstate discontinuities of the combined trial. Review the actual before/after *entire-file adjacent 30-minute edges* rather than counting these as 179 independent errors. The user's explicit all-<5% joint-recompute instruction remains in force; prior RH1–5 acceptance is superseded. Model/production use still requires provenance and clock/time-centering confidence and documented review of worsened boundary edges.

## CURRENT OPERATOR-OVERRIDE: all RH <5% to native ERA5 (24 October 2026)

**This is the latest instruction and takes precedence over earlier RH handling decisions elsewhere in this README.** For **AmeriFlux Batch01**, the operator explicitly directs that **EVERY original half-hour with RH <5% be recomputed from the same native ERA5 source's 2 m air temperature, 2 m dewpoint and surface pressure**, replacing **all five coupled forcing fields together**: `TBOT`, `TA_USE`, `QBOT`, `PSRF` and `VPD_USE`. No temperature-only or original-QBOT shortcuts. Scope from checksum-pinned Stage75 candidate forcings: **1,109 records** = 18 RH<1% (including the previously accepted CA-Man case) + 1,091 RH 1–5%: CA-Ca3 **41**, CA-Cbo **28**, CA-Man **121**, CA-TP4 **6**, US-Aud **874**, US-Bar **39**. Older Stage76 acceptance of 1–5% unchanged and older CA-Man accepted RH<1% are **SUPERSEDED for the respective low-RH timestamps**; the separate CA-Man Stage74 18/17 temperature-QC decision remains the input baseline.

**Implementation:** [Stage77 native ERA5 all-RH<5 source-coupled pipeline](examples/AmeriFlux_MultiSite_10/scripts/stage77/README.md) and [code](examples/AmeriFlux_MultiSite_10/scripts/stage77/77_native_ERA5_all_RH_below5.py), with site/year CDS downloads, same-source thermodynamics, row-exact 1,109-target verification, six new trial forcings, 10+/15-year physical/full-file audit, manifests and human-readable decision ledgers. Historic Stage76 and Stage74 reports are kept unchanged as reproducibility records and **must not override this new operator choice**. Native ERA5 must be **actually downloaded** before claiming recomputation; any proposed LST→UTC site offsets require independent metadata verification and must remain flagged PROVISIONAL. No original forcing overwrite, active CIME/DATM case edit, or Slurm submission is authorized by creating a trial.


## Mandatory meteorological source consistency (all ICOS, AmeriFlux and OzFlux workflows)

**NON-NEGOTIABLE SCIENCE RULE — jointly correct temperature and atmospheric moisture from a compatible, timestamp-aligned source.** When a QC1/gap-filled air-temperature value is replaced with ERA5, ERA5-Land, FLUXNET ERA5_HH or another product, **do not keep an unrelated tower/original `QBOT` (specific humidity), RH, dew-point or VPD as if it were measured at the new temperature**. This can produce spurious RH/VPD or supersaturation, even when the temperature trace becomes smooth. This rule applies to all current and future preparation, QC, gap-filling, cold-start, spin-up and historical simulation scripts.

1. **Prefer an internally consistent source bundle at the same physical location, timestamp and temporal support.** For ERA5-Land, jointly retrieve `2m_temperature`, `2m_dewpoint_temperature` and `surface_pressure` from the *same ERA5-Land version/grid cell*, then derive vapor pressure, `QBOT`, RH and VPD with one documented set of saturation conventions. For FLUXNET ERA5_HH, a provisional alternative is its **co-timed** `TA_ERA + VPD_ERA` pair; derive `e = e_s(TA_ERA) - VPD_ERA` and other moisture variables only after confirming VPD units, source processing, time-zone/averaging convention, and the validity of `0 < e <= e_s(T)` (or an explicitly reviewed supersaturation case). To derive `QBOT`, the pressure source and its units must also be **documented and compatible**; prefer co-sourced pressure. If compatible pressure is absent, **HOLD the QBOT-dependent coupled repair**, rather than silently combine products.
2. **Do not conflate data products or sources.** FLUXNET ERA5_HH `TA_ERA` may be processed/bias-corrected and is **not automatically raw ERA5 or ERA5-Land**. `TA_ERA + original forcing QBOT`, `ERA5-Land TA + tower RH`, or unrelated `T / dewpoint / pressure` are not approved meteorological corrections. A mixed-source *counterfactual sensitivity* is allowed only if explicitly labelled **SHADOW / NOT PRODUCTION**, its exact mixed provenance is recorded, and **no resulting records are scientifically approved or automatically propagated**.
3. **Check timestamps and conversions before calculating humidity.** Verify UTC/local time, daylight-saving interpretation, interval start/end/centre, clock offset, missing values, sensor/source processing and reanalysis sampling. ERA5-Land is hourly; when generating half-hour forcing, interpolate the **coherent T/moisture thermodynamic state** consistently (e.g., temperature and vapor pressure with documented pressure handling), recompute derived RH/VPD/QBOT, and check both QC0–QC1 boundaries. Do not independently interpolate RH, T and VPD into incompatible states.
4. **Require explicit thermodynamic closure and physical/scientific review.** In consistent units, `e_s(T)`, actual vapor pressure `e`, `RH=100*e/e_s(T)`, `VPD=e_s(T)-e`, and `q=0.622*e/(p-0.378*e)` (with `p` and `e` in the same pressure units) must agree numerically; if dew point is available, derive `e` from it and check consistency. Document water-vs-ice saturation convention and subfreezing behaviour. Check neighboring QC0 records, RH/dew-point/VPD time continuity, source QC, independent station/tower evidence and all downstream fields. **An acceptable RH range or fewer >10°C steps is NOT sufficient for approval**.
5. **Fail closed and preserve provenance.** On missing co-source moisture/pressure, unverified clock, unit ambiguity, thermodynamic closure failure, or unverifiable sensor identity, mark **HOLD**, retain original records and do not substitute an improvised humidity value. Use pinned input hashes, per-timestamp change ledgers and full-file comparisons; modify only evidence-supported QC1 points in *new, clearly named shadow files*. Preserve QC0 observations, original forcing and original downloads. **Never create production forcing, edit active CIME cases or submit Slurm runs without independent scientific review and explicit approval.**

**CA-Man Batch01 example (24 October 2026):** Stage72 deliberately tested a *mixed-source* `TA_ERA + original QBOT` **sensitivity only**. Of 35 isolated QC1 temperature candidates, 20 met its basic physical gate but showed large RH/VPD changes; 15 failed the gate (some implied RH >100%); **zero edits are approved for production**. Its shadow must **not** be reused as a coupled meteorological correction. Next review must use a coherent same-source T–moisture–pressure combination, and keep the separate 2007-03-10 anchor case on HOLD. See [Stage72 scientific limitations](examples/AmeriFlux_MultiSite_10/scripts/stage72/README.md).

### Verified Stage74 outcome and Batch01-wide MET follow-up (24 October 2026)

**IRIDIS6 Stage74 operator trial successfully completed:** **18/262,800** CA-Man half-hour forcing records underwent a coherent same-source ERA5_HH `TA_ERA/VPD_ERA/PA_ERA` temperature, humidity and pressure replacement in an **isolated, non-production** file. All **17** events flagged for RH/VPD/pressure boundary risk and the **2007-03-10** anchor were retained bit-for-bit. Full Stage58 numerical/NOLEAP audit: **PASS_REVIEW_ONLY**; `>10°C/30min` temperature-step flags **185→152**, `RH<1%` flags **1→1**. Original forcing unmodified and no model/Slurm jobs submitted. The exact user-verified Stage74 report is `reports/stage74_CA-Man_operator_18_same_source_trial_20261024T084149888301Z/` (IRIDIS6, not tracked as raw data in Git).

**Still outstanding before declaring Batch01 MET ready:** **17 RH<1% events** at CA-Ca3 (7), CA-Cbo (2) and US-Bar (8); the separately documented CA-Man one-event RH risk; temperature-review classes originally **96 P1** and **184 P2** groups across ten sites (some CA-Man P1 already operator-reviewed); and source/QC/time alignment, site-specific science decisions for other stations. Across the currently reviewed ten-site forcing candidates, >10°C/30min **step flags are expected to total 389 rather than the original 422** (this is a bookkeeping expectation to verify, not a claim that 389 physical sensor errors remain).

Use [Stage75 — complete ten-site MET release-risk audit](examples/AmeriFlux_MultiSite_10/scripts/stage75/README.md) and its [read-only audit script](examples/AmeriFlux_MultiSite_10/scripts/stage75/75_batch01_MET_release_risk_audit.py) to verify per-site meteorological bounds, low RH, original P1/P2 review queues and the exact CA-Man Stage74 trial. Even if the numerical audit passes, **it is not production approval**. The specific user decision to accept the CA-Man residual temperature jumps rather than damage moisture consistency remains documented above.

### Extreme and very-low RH follow-up: Stage76 (24 October 2026)

Batch01 Stage75 numerically scanned all ten sites and found **17 still-unresolved RH<1% half-hours** (CA-Ca3: 7, CA-Cbo: 2, US-Bar: 8) plus **1,091 RH 1–5% half-hours** (CA-Ca3: 34; CA-Cbo: 26; CA-Man: 120; CA-TP4: 6; US-Aud: 874; US-Bar: 31). These are **candidate quality flags, not automatic errors**. Stage76 is a read-only/native-ERA5-assisted scientific review: calculate each extreme RH event using a **matched actual ERA5 2m air temperature, 2m dewpoint and surface pressure** when CDS native data and site UTC offsets are available; separately report provisional **FLUXNET TA_ERA + VPD_ERA + PA_ERA *inferred* dewpoint** if native dewpoint is not yet available. Never mislabel an inferred dewpoint as a native ERA5 dewpoint; never mix ERA temperature with old tower QBOT. Group all RH1–5 records into contiguous episodes, inspect temperature/VPD/tower QC and neighbouring half-hours, and obtain an explicit human decision before any forcing change. **The one existing CA-Man RH<1% operator-accepted risk is not part of the unresolved 17.**

See [Stage76 code, CDS native-ERA5 retrieval and human-review instructions](examples/AmeriFlux_MultiSite_10/scripts/stage76/README.md). Until its source/clock and station-level evidence is reviewed, **0 further humidity replacements are approved**.

### Human-review precedent: accept a remaining temperature jump rather than introduce implausible humidity

**Operator's explicit CA-Man Batch01 decision, 24 October 2026 (Stages71–74):** First screen **36** isolated QC1 air-temperature jump events bracketed by QC0. One event (**2007-03-10 11:30**) remains a separate QC0-anchor HOLD. Of the other **35**, an alternative matched-row `FLUXNET ERA5_HH` bundle (`TA_ERA`, `VPD_ERA`, `PA_ERA`) passed basic physical/thermodynamic checks for **35/35**, but comparing the jointly computed RH, VPD and pressure against neighboring QC0 records produced two distinct groups:

- **18/35 with `NO_LARGE_BOUNDARY_SHIFT_DETECTED`:** operator chooses a **scoped same-source joint T/Q/P/VPD substitution** (update `TBOT`, `TA_USE`, `QBOT`, `PSRF`, `VPD_USE` coherently) in a **new, provenance-pinned trial forcing file**. No clock/source verification or formal production sign-off is implied by a basic physical pass or this selection.
- **17/35 with `REVIEW_LARGE_BOUNDARY_SHIFT`:** **retain the ORIGINAL complete meteorological forcing row**, **do not replace only its temperature**, and **accept the remaining >10°C/30-min temperature jump as a documented, operator-reviewed unresolved risk**. **Do not smooth or overwrite neighboring QC0 observations** merely to remove the anomaly. Retention **does not prove original RH/QBOT correct**; it reflects the operator's preference not to introduce a potentially larger moisture artifact.
- **1/36 QC0-anchor ambiguity (2007-03-10):** preserve the original row and keep it independently on HOLD.

**Reusable decision principle:** When a potential air-temperature repair is not supported by a *jointly coherent, time-matched moisture/pressure state* that also passes the established RH/VPD/pressure boundary review, **do not force temperature continuity at the expense of moisture credibility**. A documented temperature discontinuity may be retained. This 18/17 threshold partition is **specific to CA-Man and the Stage73 screening settings** (large RH step ≥25 percentage points, large VPD step ≥10 hPa, or ERA-to-original pressure discrepancy ≥2000 Pa); **do not apply the same numerical counts or thresholds blindly to other stations**. Use original observations, site climate, water/ice saturation convention and scientific context.

**Reproducible record:** [Stage73 same-source audit](examples/AmeriFlux_MultiSite_10/scripts/stage73/README.md) and [Stage74 operator-decision, 18-replacement trial](examples/AmeriFlux_MultiSite_10/scripts/stage74/README.md). Stage74 has `--self-test`, `--check` (read-only) and `--trial` (creates a separate candidate only), with **exact 18 changed timestamps, 17 unchanged flagged cases and one unchanged anchor**, SHA manifests and a full 15-year scan. The Stage72 `ERA T + original QBOT` shadow remains **sensitivity-only and must not be used as an approved repair**. All active CIME/Slurm cases and original source/forcing files stay untouched.


<!-- MULTIBATCH_SPINUP1000_STATUS_START -->
## ICOS sites — four multi-site spin-up campaigns (IRIDIS6 status, 20 October 2026)

**Latest user-supplied IRIDIS6 checkpoint/Slurm snapshot** for batches 8, 11, and 13; for batch 6, no equivalent new snapshot was supplied in this update. All progress numbers represent **archived elapsed model years**, not forcing years or the current timestep within a running five-year job. Slurm statuses are a dated snapshot. Reaching a target does not demonstrate ecological convergence.

| Campaign | Latest confirmed archival / current Slurm status | Next action |
| --- | --- | --- |
| [ICOS Batch 6](examples/FLUXNET_MultiSite_6/) | Previous observation: five cases RU-Fyo, DE-Tha, DK-Sor, NL-Loo, IL-Yat reached 1000 years and were continued toward 3000; DE-Hai was recovered from a verified 810-year checkpoint and its Slurm run was accepted. **No new batch-6 status is included in the operator's current snapshot.** | Run a fresh batch-6 audit before claiming newer progress |
| [ICOS Batch 8](examples/FLUXNET_MultiSite_8/) | **0/8 current targets met.** Seven 1000-year cases: **2 RUNNING / 5 PENDING**, archived 635–655 years; FR-Hes **360/500**, IDLE. **2,620 target model-years remain** across all eight cases. | Monitor seven submitted chains; FR-Hes archiving requires separate investigation |
| [ICOS Batch 11](examples/FLUXNET_MultiSite_11/) | **9/11 completed 1000 archived years**; IT-Noe **5/1000**, IDLE; CH-Aws **NO_ARCHIVE**, IDLE, elapsed years unverified | Inspect IT-Noe and CH-Aws separately; do not mistake stored RESUBMIT for queued jobs |
| [ICOS Batch 13](examples/FLUXNET_MultiSite_13/) | **0/13 completed 1000 archived years**, **2 RUNNING / 11 PENDING**; archived model years total **6,360/13,000**, with **6,640 remaining** | Continue monitoring existing S30SHARED cases; do not resubmit active chains |

**Evidence:** operator-provided read-only `check_four_spinups.py` report dated 20 October 2026; batch-specific exact checkpoint, RESUBMIT and Slurm job IDs are recorded in each linked README. A `PENDING` job may be queued for priority or dependency reasons, and `RUNNING` only proves job activity at the snapshot, not that the next segment is complete. `NO_ARCHIVE` does not establish zero simulated years.

### Read-only monitoring and protected Research Filestore archival

- **[Preferred live four-batch monitor](maintenance/check_four_spinups.py)** ([instructions](maintenance/README.md)): 38 sites, one active CIME case per site, separate model/archive status, checkpoint/resubmit details, and provenance-checked CH-Aws RH42A v8 inherited restart baseline. On IRIDIS6: `git fetch origin main && git show origin/main:maintenance/check_four_spinups.py | python3 -` (no local merge required).
- [Secondary Filestore-oriented four-batch history audit](scripts/research_filestore/audit_four_batches_live.py) uses legacy case naming; **not** the preferred live RH42A monitor.
- [Selective 8-/13-site transfer and SHA-256 verification](scripts/research_filestore/archive_completed_8_13.py): only run after verifying completed, idle cases.
- [Established 11-site transfer tool](scripts/research_filestore/archive_eleven_site_1000yr.py), [Filestore guidance](docs/research_filestore/README.md), [11-site operational record](docs/research_filestore/FLUXNET_MultiSite_11.md).

**Research Filestore destination:** `/research/xclimatetbm/ly3n24/CLM_FATES/Spinup_Archives/<BATCH>/<SITE>/<CASE>/`. Confirm copy/checksum receipts before considering Scratch cleanup; do not delete active restart or original CIME cases.
<!-- MULTIBATCH_SPINUP1000_STATUS_END -->

**[ICOS sites — multi-site experiments](examples/ICOS_sites/)** collects the four existing European FLUXNET/ICOS batches (6, 8, 11 and 13). Dataset provenance remains site-specific. **AmeriFlux sites** are maintained separately, starting with [US-Ha1](examples/AmeriFlux_US-Ha1/). Existing workflow paths remain unchanged to avoid breaking IRIDIS6 jobs.

**[24 October 2026: ICOS 38-site observed-PFT percentage and simulated-PFT comparison](examples/ICOS_sites/ICOS_PFT/)** — [complete 38-site master comparison CSV](examples/ICOS_sites/ICOS_PFT/MASTER_38_SITE_OBSERVED_VS_FATES_PFT_20261024.csv), [source-based observed PFT percent report](examples/ICOS_sites/ICOS_PFT/38_SITE_OBSERVED_PFT_PERCENT_REPORT_20261024.md) and [FATES model PFT screening](examples/ICOS_sites/ICOS_PFT/comparison_20261024/FOUR_BATCH_EC_PFT_VS_FATES_REPORT_20261024.md). These compare field species evidence (28 stations with some numeric leads, 10 qualitative only) with 34 GitHub-published model final VegC distributions. Field percentages are not automatically FATES land-area fractions.

**[AmeriFlux sites](examples/AmeriFlux_sites/)** includes [Batch 01 (10 sites)](examples/AmeriFlux_MultiSite_10/) and **[Batch 02 (10 sites)](examples/AmeriFlux_MultiSite_10_Batch02/)**. Batch02 publishes Stages00–10, its exact release manifest and operating instructions. The operator's 22 October 2026 Stage07 result is **5 numerically verified candidates / 5 humidity-blocked sites (4,904 unresolved records)**; Stage08 same-release-RH sensitivity and the mandatory Post-v5 numeric/science gates are ready for execution; no DATM or model jobs have been created for Batch02. See the [experiment index](examples/README.md) and the Batch02 README for current scope.

Reproducible single-site CTSM/CLM-FATES workflows used on University of Southampton IRIDIS6.

The repository is organized by observing network / case study:

- `examples/ICOS_ES-LJu/` — ES-LJu ICOS/FLUXNET single-site CLM-FATES workflow.
- `examples/OzFlux_AU-How/` — Howard Springs OzFlux single-site CLM-FATES workflow.
- `examples/AmeriFlux_US-Ha1/` — Harvard Forest EMS Tower, 1991–2025 hourly AmeriFlux/FLUXNET forcing with automated physical QC and CLM-FATES workflow.

This repository intentionally does **not** contain raw flux-tower packages, annual DATM NetCDFs, CTSM surface files, or model history files. Those are large and/or subject to source-data terms. The scripts reconstruct the workflow from the original downloaded data.

Current software context for the ES-LJu example:

- CTSM: `ctsm5.4.056`
- FATES: `sci.1.92.7_api.46.0.0`
- CIME: `cime6.5.5`
- compset: `I1PtClm60FatesRsGs`
- grid: `CLM_USRDAT`
- compiler / MPI: Intel / OpenMPI
- calendar: `NO_LEAP`

- `examples/AmeriFlux_US-Ha1/` — Harvard Forest EMS Tower, 1991–2025, hourly AmeriFlux/FLUXNET forcing with automated physical QC and CTSM/FATES workflow.

- `examples/FLUXNET_MultiSite_6/` — Six-site FLUXNET input preparation, surface extraction, meteorological QC v1–v5, and documented outstanding issues.

## CLM-FATES Spin-up Failure Diagnostics

[**Failed-site diagnostics and incident tracking**](diagnostics/spinup_failures/) gathers read-only investigations for interrupted or scientifically suspect spin-ups. Start with the [IT-Noe negative-RH failure investigation](diagnostics/spinup_failures/IT-Noe/README.md) and its [independent ICOS ERA5 source-audit script](diagnostics/spinup_failures/IT-Noe/it_noe_era_source_audit.py). The original 11-site, CH-Aws, and FR-Hes experiment records remain unchanged. **Diagnostic flags do not imply approved meteorological correction or successful restart.**

## IRIDIS6 MPI / Slurm CPU affinity

**Read [IRIDIS6 MPI, Slurm CPU affinity and OpenMPI troubleshooting](IRIDIS6_MPI_CPU_AFFINITY.md)** before launching multiple single-core CLM-FATES cases on shared IRIDIS6 nodes. It documents a reproduced mismatch between a one-core Slurm allocation and OpenMPI's actual binding, both MPI test launchers, the tested `srun --mpi=pmix` fix, and the difference between CPU allocation, affinity, walltime, and real model progress. Runnable diagnostics are in [`diagnostics/iridis6/`](diagnostics/iridis6/).

**Eight-site experiment:** [`examples/FLUXNET_MultiSite_8/`](examples/FLUXNET_MultiSite_8/) now includes the checkpoint-safe `srun` recovery script, test evidence, and detailed operating instructions. This supersedes the October 13 `mpirun` shared-node resumption method; do not repeat the original eight-site creation/submission script against active cases.

- `examples/FLUXNET_MultiSite_11/` — Eleven-site FLUXNET/ICOS/EUF source-aware meteorological QC; ERA5-Land winter humidity, pressure/longwave trial corrections, and scientific-review ledgers.

## DK-Sor CO2 sensitivity experiment

[**DK-Sor: Fixed vs NOAA Historical CO2 (1996–2024)**](examples/FLUXNET_MultiSite_6/experiments/DK-Sor_CO2_sensitivity/)

This experiment investigates how time-varying atmospheric CO2
influences CLM-FATES simulations of GPP and NEE at DK-Sor.

Two historical simulations are designed to use the same
1000-year spin-up restart and meteorological forcing:

- **Fixed CO2:** 361.93 ppm throughout 1996–2024.
- **Dynamic CO2:** NOAA globally averaged monthly atmospheric CO2
  covering the historical observation period.

The objective is to evaluate whether historical CO2 forcing
changes simulated carbon fluxes, seasonal dynamics, interannual
variability and agreement with eddy-covariance observations.

The experiment includes:

- Scientific hypotheses and experimental configuration.
- Read-only IRIDIS6 monitoring scripts.
- GPP and NEE comparison and visualization scripts.
- Documentation of reproducibility and scientific limitations.

**Status:** NOAA historical simulation underway.
The full fixed-CO2 historical control and 29-year comparison
are not yet completed.

## Southampton Research Filestore: six-site 1000-year history archival

See the repository-wide [Research Filestore management guide](docs/research_filestore/README.md), [six-site archival case study](docs/research_filestore/FLUXNET_MultiSite_6.md), and independent [read-only archive audit script](scripts/research_filestore/audit_six_site_archive.py): five published 1000-year spin-up cases with carbon-pool and GPP/NEE figures, a separate DE-Hai backup-only case, the 2026-10-18 Scratch file-count quota incident, safe archival paths, and read-only verification code. Successful migration and Scratch deletion must be confirmed from live checksum manifests; this repository does not contain raw NetCDF or restart files.

## CIME Git cleanup and Scratch inode maintenance

[**CIME case Git maintenance guide and reusable scripts**](maintenance/cime_git_cleanup/) — safe audit, sequential `git gc --no-prune` packing, stale `gc.pid` inspection, IRIDIS6 Slurm execution, and the October 2026 five-site 1000-year case study. **Do not delete per-case `.git` directories** or remove a Git lock without checking its recorded host and PID. The maintenance process does not alter CLM-FATES restart or history files and does not replace scientific convergence or continuation checks.

## Eleven-site 1000-year spin-up results (20 October 2026)

[Nine of eleven FLUXNET sites have completed their 1000-model-year simulations](examples/FLUXNET_MultiSite_11/README.md): BE-Bra, FR-Fon, GL-ZaH, AT-Neu, FI-Sod, CH-Cha, CH-Fru, CH-Lae and CZ-Stn. IT-Noe and CH-Aws remain incomplete. **Execution completion does not establish spin-up convergence.** The [11-site Research Filestore archive guide](docs/research_filestore/FLUXNET_MultiSite_11.md) and [non-destructive transfer/checksum script](scripts/research_filestore/archive_eleven_site_1000yr.py) describe transferring model output to Southampton Research Filestore. Archive migration must be verified live; no transfer or Scratch deletion is claimed by this GitHub update.

# Batch01 MET and BIF code archive audit (2026-10-24)

This is a source-controlled **coverage and provenance inventory**, not science approval.
Audit basis: repository main branch full recursive tree; operator-shared Stage54,
Stage55, Stage56, Stage57B logs. GitHub cannot independently read IRIDIS6 data.

## Present in repository
- Stage00-25: original upload, source extraction, BIF geolocation, surfaces,
  source anomaly audits, original QCv5, US-Bar scoped recovery and science audits.
- Shared AmeriFlux_sites scripts Stage28-32: BASE height inventory,
  sensor/date/ZBOT candidate analysis. Stage34-36: vegetation/PFT review.
- Stage33: surface/FATES preflight.
- Stage38: read-only pre-spinup gate.
- Stage57B: US-Bar combined humidity, temperature and BASE/FLUXMET audit.
- Stage54, Stage55, Stage56: **reconstructed** from the conversation's executed
  code and observed outputs on 2026-10-24. These are new archives, NOT certified
  byte-for-byte copies of the original interactive console scripts. Stage54
  intentionally refuses to overwrite the existing Stage54 candidate. Stage56
  is READ ONLY and only *verifies* an existing accepted-risk ledger.

## Still missing or incomplete
- Stage39-53 originals: NO verified executable copies were found in main
  at audit time. This includes the Stage51 seven-record scoped humidity repair,
  Stage52 three-event diagnostic, and Stage53 CA-Man BASE cross-check.
  Existing Stage51 inputs/ledgers on IRIDIS6 are **not** evidence that their
  source-generation scripts have been archived to GitHub.
- Original Stage56 writer that created the CA-Man accepted-risk JSON:
  NOT archived as executable writer; the GitHub Stage56 reconstruction reads
  and checks the already-created ledger without writing or overwriting it.
- Full run logs, historical data versions, all per-site source hashes and
  formal sign-off decisions: not held in this repository inventory.

## Operator-confirmed IRIDIS6 checkpoints (not GitHub replicated data)
- Stage51 CA-Man candidate SHA256:
  c87c8d44381e29f17bf3ccee074afb27ff526b4dd5b92b951e0a990ba4a5ee3e
- Stage54 CA-Man candidate SHA256:
  fac0bc4a82050a087e462c3af1b05ec16e1f3f803a66bde7bf87c0b3a39d3705
- Stage55: 262800 rows; only 1999-05-09 13:00 and 2005-05-09 14:00
  updated, columns QBOT and VPD_USE; physical closure and NO_LEAP PASS.
- Stage56: 2007-07-03 20:00 CA-Man RH approx 0.3673% accepted as a
  documented risk; no change to that forcing row.
- Stage56 screen: 17 non-exempt RH<1% values across CA-Ca3 (7),
  CA-Cbo (2) and US-Bar (8), and 422 temperature-jump flags across ten sites.
- Stage57B US-Bar: 350400 rows, 8 RH<1%, 106 >10 C/30-min TA jumps,
  18 reversing jump pairs. BASE RH_PI_F often contradicts sub-1% computed
  humidity; exact timestamp matching still requires interval/clock validation.
  Also, some huge TA spikes track BASE TA sensors, so do not repair automatically.

## Remaining gates
1. Recover and review the **actual** Stage51/52/53 source scripts from HPC
   history, saved files or complete conversation source before archiving.
2. Preserve immutable Stage51/54/56 manifests/receipts with hashes and provenance.
3. Review scientific QC0 changes, humidity events and TA spikes.
4. Resolve BIF sensor-height effective dates and DATM ZBOT.
5. Audit surfaces/PFT, then independent smoke tests; no production spinup
   is authorized solely by numerical PASS.

Safety: no forcing, DATM, CIME, PFT, surface or Slurm changes made by this
GitHub documentation update.

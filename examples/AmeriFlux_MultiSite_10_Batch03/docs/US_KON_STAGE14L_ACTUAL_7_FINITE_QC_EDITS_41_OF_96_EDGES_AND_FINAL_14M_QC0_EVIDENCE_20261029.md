# US-Kon — Stage14L **actual** 2026-10-29 04:57Z results; finite QC1/QC2 reanalysis revisions not promoted

The user actually executed the pinned GitHub Stage14L original-Grade-aware research sensitivity (commit `773252e67a54b60c2a92d621bfd77cd01635508f`). Syntax and self-test PASS. Its output is a **new independent research-only file**, not a replacement of Stage12AY or the Stage14K primary candidate:

```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/US_Kon_14L_QC1_QC2_NEIGHBOR_ERA_RH_RESEARCH_ONLY_20261029T045738Z_fe3252d0
```

Stage14L actual signed prior Stage14K SHA256 `050007998ea63c911c63eab42b23902be31f57135935b5a7135d45541d964acb`, original source manifest SHA256 `a68e021f234b8efd9a0ad533dd3a8085193ce51a8234aa1e6e09335cb5d7ddca`.

## Actual comparison (do NOT conflate denominators)

| Diagnostic | Actual |
|---|---:|
| Native model source | 280,320 30-min NOLEAP |
| Stage14K already-filled routine VPD/QBOT slots, unchanged | 68 |
| Protected true source missing special HOLDs, unchanged | 9 |
| Newly changed *finite original QC1/QC2* neighbours in isolated Stage14L | **7** |
| Original 68-seed contact joins checked in Stage14L | **96** |
| Those seed joins with any warning, Stage14K baseline | **46** |
| Same **96** joins with a warning after Stage14L | **41** |
| Enlarged source-contact joins **after adding 7 new neighbour slots** | 103 |
| Enlarged source-contact joins with warning | **44** |
| Finite-source water/QBOT closure, prior native QC0 preserved | PASS |
| Production science/DATM/AD400 approved | NO |

The earlier Stage14K **62 flagged of 112 original 35-episode joins** includes 9 still-missing hard-HOLD episode edges. That is **not the same audit set** as Stage14L's 96 original routine-contact joins. A reduction from **46 to 41 over the same 96** is meaningful but small; it cannot be described as reducing Stage14K's 62 to 41 on the same population. In fact 44 of 103 expanded interface checks still warn, and the new seven neighbour modifications have no independently measured verification.

Actual rejection counts, across iterative candidate expansion attempts rather than distinct hours: **32** original tower/ERA T mismatches >5°C; **29** no two-sided edge improvement; **3** actual VPD QC0/invalid protected; **14** no meaningful source change; **2** previously modified/source mismatch protected; **1** other missing or special HOLD adjacent. None of the original source, 68 already rebuilt, 9 protected hours, other meteorology or model case changed.

Severe remaining actual 30min native joins:
- `201208040900→201208040930`, original QC1→QC1, abs ΔVPD **23.529666 hPa**, RH **32.827753 pp**, QBOT **0.004651 kg/kg**; `201208040930→201208041000` after adjacent revision still VPD **9.849934 hPa**.
- `201509061730→201509061800`, original QC2→QC2, abs ΔVPD **16.779835 hPa**, RH **42.970466 pp**, QBOT **0.006122 kg/kg**; `201509061930→201509062000` **11.004314 hPa**, RH **44.725632 pp**, QBOT **0.007168 kg/kg**.
- `201506101400→201506101430`, QC2→QC2 VPD **15.703989 hPa**, RH **28.451341 pp**, QBOT **0.004825 kg/kg**.
- `201109281630→201109281700`, QC2→QC2 VPD **12.082047 hPa**, RH **37.041425 pp**, QBOT **0.005436 kg/kg**.

## Scientific final decision at this stage

**Continue to use Stage14K as the primary numerically reconstructed but incomplete scientific input (68 new VPD/QBOT + 9 protected NaN).** Preserve Stage14L separately as a finite-neighbour QC1/QC2 reanalysis **sensitivity**, NOT an approved replacement. Seven new finite-source edits reduce only five previously flagged joins, and there is no clear independent sensor QA corroboration. **Do not force the 44 remaining interface warnings to zero by uncontrolled source smoothing.**

The next and last consolidated data-quality action is one **read-only original source observation QC0 provenance package** for **all nine original protected missing source-HOLD halfhours** and **44 actually still flagged expanded source edges**. Inspect native `TA_F_QC=0` and `VPD_F_QC=0` simultaneous measured pairs, proximity ±2/6/24h, true original selected/model/FLUXMET ERA values and source time, including whether a candidate is derived from QC2/ERA. If there is no independent measurement, leave source science OPEN; do not invent temperature or RH truth.

[Stage14M: original both-QC0 tower measured original source evidence, nine protected HOLDs and 44 remaining flagged interfaces](../scripts/stage14/14m_US_Kon_QC0_evidence_for_9HOLD_and_44_edges_READONLY.py). **Not actually run on IRIDIS6 as of this handoff**. The new code must verify actual Stage14K and Stage14L output receipts and exact originals. It prints nine native original source QC0 context and severe remaining >10hPa edges; writes only a new original-source QA report with SHA receipts. No source writes, no production Post-v5/DATM/AD400 or Slurm jobs.

Pinned source Git commit `77b6f36cfd450344a53d55cd2c27239213dd47e9`, blob `1e3058537e0591b0dc4fa4cbf15a8ed3399376f2`.

```bash
(
 set -euo pipefail
 F="$HOME/US_Kon_last_QC0_provenance.py"
 curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/77b6f36cfd450344a53d55cd2c27239213dd47e9/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage14/14m_US_Kon_QC0_evidence_for_9HOLD_and_44_edges_READONLY.py" -o "$F"
 test "$(git hash-object "$F")" = "1e3058537e0591b0dc4fa4cbf15a8ed3399376f2"
 python3 -B -c 'import pathlib,sys; f=pathlib.Path(sys.argv[1]); compile(f.read_text(),str(f),"exec"); print("SYNTAX PASS")' "$F"
 python3 -B "$F" --run 2>&1 | tee "$HOME/US_Kon_last_QC0_provenance.log"
)
```


## 2026-10-29 06:19 UTC — Stage14M false year guard fail, corrected

**Actual operator execution of original commit 77b6f36... Stage14M:**
```
SYNTAX PASS
US-Kon STAGE14M QC0 ORIGINAL EVIDENCE SELF-TEST PASS
US-Kon STAGE14M STOP READONLY: original site year/clock changed
```
It failed at Python line 68–70 **before** source QC0 evidence classification because the script incorrectly hardcoded manifest `first_year=2005,last_year=2020`. Earlier Stage14J/L did NOT require those years; 280,320 native selected NOLEAP half-hours alone do **not** establish original release bounds. Neither Stage14K nor Stage14L source inputs changed; no reports/model jobs executed from the failed run.

**Correction on GitHub commit `35ce6de07407477646a29cc21f119961d16dfa8f`**, Git blob `bb25b2aafc8ad73c665ee6d1c84b048e167e0013`: use the real SHA-verified original site manifest `first_year/last_year` as metadata and print them; assert only original native interval = 30min, an exactly contiguous 16-year `280320` selected time tape with all leap days omitted, and actual published original FLUXMET + companion-ERA timestamps and SHA. Do NOT conflate original release bounds with selected forcing years. Correct source has been inspected for balanced quotes/brackets but still needs actual HPC run.

The user can rerun ONLY Stage14M with this pinned command:
```bash
(
 set -euo pipefail
 F="$HOME/US_Kon_last_QC0_provenance.py"
 curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/35ce6de07407477646a29cc21f119961d16dfa8f/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage14/14m_US_Kon_QC0_evidence_for_9HOLD_and_44_edges_READONLY.py" -o "$F"
 test "$(git hash-object "$F")" = "bb25b2aafc8ad73c665ee6d1c84b048e167e0013"
 python3 -B -c 'import pathlib,sys; f=pathlib.Path(sys.argv[1]); compile(f.read_text(),str(f),"exec"); print("SYNTAX PASS")' "$F"
 python3 -B "$F" --run 2>&1 | tee "$HOME/US_Kon_last_QC0_provenance.log"
)
```

Stage14M remains **read-only except creation of its separate SHA-receipted report** and cannot authorize production DATM/AD400. Exact nine protected scientific holds and 44 actual expanded QC warning edges are unchanged.


## 2026-10-29 06:19+ UTC — second actual Stage14M early-stop, FSDS CSV precision comparison

Operator reran corrected Stage14M `35ce6de...`: source year metadata and selected source grid successfully confirmed:

```
SYNTAX PASS
US-Kon STAGE14M QC0 ORIGINAL EVIDENCE SELF-TEST PASS
US-Kon ORIGINAL MANIFEST YEARS: 2004 2019 native_minutes 30
US-Kon SELECTED SIGNED NOLEAP YEARS: 2004 2019 HH 280320
US-Kon STAGE14M FAIL CLOSED: non-humidity original source changed FSDS
```

This is a **second premature audit failure** before actual QC0 inference; the earlier false claim that original source might be 2005–2020 has been directly disproven: both original metadata and selected complete 16-year NOLEAP tape are **2004–2019**.

Reason the original guard is too strict: Stage14L verified `new["FSDS"].equals(parent["FSDS"])` (and all other nonhumidity fields) **in memory before writing** its independent SHA-signed CSV. But Stage14M compares **two independently serialized and parsed floating-point CSVs** with `Series.equals()`, which is strict on dtype and binary floating equality. A last-bit difference from pandas CSV float parsing/17-digit output can trigger a **false scientific alteration**. The exact numerical discrepancy cannot be claimed until the added diagnostic runs.

**Third corrected original-source auditor** pinned at Git commit `0906444ffdbd6749043f943a33e8e0ac60837e47`, blob `9909fddf2a80ed0290b726bfadc120b988ed57fa`. Before any original tower QC0 source interpretation, it:
- checks strict equality of NaN, +infinity, −infinity masks for every nonhumidity numeric field (`TBOT,PSRF,FSDS,FLDS,WIND,PRECTmms,TA_USE`);
- prints per-field max absolute readback difference and number of differences > **1e-10 in original field units**;
- allows *only* parser/CSV-level tiny absolute differences <=1e-10, stops on any larger difference; `time` equality remains exact;
- independently preserves strict source provenance: both Stage14K and Stage14L SHA receipts, exactly 7 actual humidity-source differences in signed ledger, exactly 9 preserved `VPD_USE/QBOT` native NaNs, original FLUXMET and paired ERA SHA, 280320 consecutive 2004–2019 source NOLEAP timestamps.

The revised script has NOT been run on IRIDIS6 as of this note, and the first two actual attempts did not write source or QC reports. If the new per-field output shows any meaningful difference above tolerance, STOP and inspect before changing historical forcing. Stage14M does not modify scientific inputs, cases or Slurm jobs.

```bash
(
 set -euo pipefail
 F="$HOME/US_Kon_last_QC0_provenance.py"
 curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/0906444ffdbd6749043f943a33e8e0ac60837e47/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage14/14m_US_Kon_QC0_evidence_for_9HOLD_and_44_edges_READONLY.py" -o "$F"
 test "$(git hash-object "$F")" = "9909fddf2a80ed0290b726bfadc120b988ed57fa"
 python3 -B -c 'import pathlib,sys; p=pathlib.Path(sys.argv[1]); compile(p.read_text(),str(p),"exec"); print("SYNTAX PASS")' "$F"
 python3 -B "$F" --run 2>&1 | tee "$HOME/US_Kon_last_QC0_provenance.log"
)
```

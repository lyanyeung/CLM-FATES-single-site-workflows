# US-Kon — actual Stage14N 2026-10-29 06:36 UTC; final scientific hold decision

**Status: STOP further routine automatic source modifications.** The operator actually executed the SHA-pinned [Stage14N three original paired-QC0-bracketed RH candidates](../scripts/stage14/14n_US_Kon_three_nearby_QC0_RH_candidates_ONEPASS.py). Self-test and all input/parent SHA checks passed. **Zero of three** original VPD-QC1/T-QC0 humidity missing half-hours passed BOTH immediate 30-minute source water/VPD/QBOT consistency gates. The actual write was only a **separate versioned research trial**; no historical source, parent Stage14K, alternate Stage14L, model case, DATM or Slurm was touched. The new independent trial retains **all nine hard-source VPD/QBOT NaNs**. Actual source:

```
/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/science_trials/US_Kon_14N_3_NEARBY_QC0_RH_RESEARCH_ONLY_20261029T063612Z_13452774
```

## Three exact original paired-QC0 neighbour experiments — all blocked

| Original held native HH | Measured QC0 RH interpolated | Paired ERA RH | Source QA and blocker |
|---|---:|---:|---|
| 2011-10-23 07:30 | 67.0345% | 72.8491% | Original source T QC0/VPD QC1. Both contacts fail, left/right ΔVPD 4.432/7.611 hPa; ΔRH 44.266/50.254 pp, ΔQBOT >.003 both |
| 2012-02-25 10:30 | 52.8069% | 48.8668% | Left contact PASS; right ΔVPD 5.296 hPa, ΔRH 27.117 pp |
| 2012-08-05 09:00 | 38.3399% | 60.7748% | Left contact PASS; right ΔVPD **15.121 hPa**; paired ERA RH differs from QC0-derived candidate by −22.435 pp |

All original nine missing science slots `201102220830`, `201102220900`, `201102220930`, `201105261100`, `201109291830`, `201110150730`, `201110230730`, `201202251030`, `201208050900` are preserved **missing**, not silently ERA-filled. In particular the three 2011-02-22 original T-variable inconsistent records have nearby two-sided original QC0 paired anchors but cannot be treated as reliable T/RH interpolation; 2011-05/09/10 other three missing events have too-distant original RH QC0 anchors.

The Stage14M evidence report documented original both-QC0 source 184,026 sitewide but only 6/9 special holds with close ±6h observed anchors, and 11 severe original QC1/QC2/ERA >10 hPa native 30min jumps. Stage14N does not resolve these; it directly shows that even near-source observed water RH cannot be inserted without violating neighbouring selected derived humidity. Negative evidence is a useful scientific finding, not a reason to multiply unvalidated patches.

## Main site decision (2026-10-29)

1. **Stage14K is the preferred least-edited incomplete *research* version:** 280,320 native NOLEAP HH, original 77 humidity missing reduced to **9 protected** by 68 source-paired ERA-RH low-confidence reconstructions. It is **NOT model-ready**; previous Stage14K source join audits had 62 flagged of 112 original episode contacts.
2. **Stage14L remains an independent sensitivity**, only 7 extra original finite QC1/QC2 neighbour edits (on same 96 routine contact interfaces warning count **46→41**, still 44 warnings over expanded 103 interfaces), not independent QC0 truth.
3. **Stage14N does not add any gap fill:** accepted=0/3, missing remains nine. Both endpoints and the entire original 68, source T, PSRF and source QC0 protected. No DATM/AD400, Post-v5, CIME or Slurm permission.
4. **Science triage is complete *at available-data level*, not source-forcing approved.** Stop additional threshold-chasing or blind interpolation. Further progress requires genuinely additional independent measured RH/instrument QA/source maintenance evidence; or the user must explicitly request a separately labelled low-confidence all-gap model *sensitivity*, not an observationally validated forcing. No ETA can be inferred from the current repository.

## Ten-site Batch03 context at 2026-10-29

**7/10 already have zero-NaN research meteorological shadows, but not any full Post-v5/DATM/AD400 approval**: US-MMS (Stage14C), US-MOz (Stage14I), US-Mpj (Stage14D), US-MtB (Claude MtB04), US-NC2 (Stage11Q/14E), US-Me6 (Claude CL03, 45 HH filled), US-NR1 (Claude CL03, native 1999–2025, 191 HH filled; 1998 excluded under the user's decision). The outstanding numerical/scientific sites are **US-Kon (nine retained special source missing), US-NR3 (238 native selected humidity HH remain, Claude Stage08 evidence and alternatives; no approved replacement forcing), US-Me2 (the four clock-linked humidity event records still require source decisions and an equivalent complete selected model input; documented UTC-8 solved).**

More context:
- [Claude US-Me6 & US-NR1 source reconstruction handback](US_ME6_NR1_CLAUDE_HANDBACK_20261029.md).
- [Claude US-MtB original-source alternative research handback](US_MTB_CLAUDE_HANDBACK_20261029.md).
- [US-NR3 Claude Stage07/Stage08 exact 238 science options and source-year risks](US_NR3_CLAUDE_STAGE07_EVENT_DECISION_REPORT_20261029.md).
- [US-Me2 original source BADM documented clock evidence](US_ME2_CLOCK_EVIDENCE_20261026.md).

**Important:** 'numerically complete research' is a **different gate** from independent QC0 observation support, approved source certainty, actual DATM ice saturation acceptance, surface/PFT/ZBOT clocks, model spin-up safety. None of the work above automatically submits a model job.

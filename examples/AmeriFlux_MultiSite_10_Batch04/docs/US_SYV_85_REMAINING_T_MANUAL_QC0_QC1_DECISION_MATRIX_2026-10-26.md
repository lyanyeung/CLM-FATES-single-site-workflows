# US-Syv — 85 remaining T-vs-ERA holds fully audited, scientific operator-decision matrix

**2026-10-26 actual operator result.** [Read-only source-flank auditor](../scripts/manual_review/review_remaining_US_Syv_85_temperature_holds_30_runs_before_after.py) successfully passed original/Stage07/final 106-HH Syv SHA, original paired FLUXNET ERA and Stage05 HOLD lineage. **85 source HALF-HOURS / 30 contiguous historical HOLD runs / 298 unique half-hour timestamps across ±2h context**. Original source **TA_F_QC 0: 24 HH; TA_F_QC 1: 61 HH**. 106 previously manually ERA-substituted Syv native HH unchanged, previous 9 other site's selected sources unchanged; no repairs from this read-only step.

**Reference:** source `TA_ERA` is the *processed original FLUXNET paired ERA-derived* data, not an independently fetched ERA5-Land data set. QC0 denotes the original observed-source consolidated product, QC1 denotes MDS gap fill, QC2 ERA-origin fill. `TA_F_MDS` is not necessarily independent tower evidence, particularly where `TA_F_MDS=TA_F` and MDS QC1. A large grid mismatch alone does not establish sensor failure; a hard isolated 20–40°C fall and recovery during same season plus bad vapour physics is much stronger.

## Verified remaining event counts and triage

**12 original source-QC0 HOLD runs, 24 HH:**
- **Strong suspect source-QC0 temperature artifacts: 20 HH across 10 runs:** 2003-05-08 11:30–14:00 (6) **and 15:00–15:30 (2)**; 2003-05-30 07:30–08:30 (3) **and 09:30–10:30 (3)**; 2001-08-14 10:30 (1) and 14:30 (1); 2003-05-06 14:00 (1) and 15:30 (1); 2003-05-10 18:00 (1); 2003-06-03 15:30 (1).
- **Ambiguous source-QC0 temperature: 4 HH across 2 runs, recommend retain TA pending independent sensor meteorology:** 2001-10-02 14:30–15:00 (2) and 2007-03-29 19:00–19:30 (2). The native source has lower T than paired grid but some local persistence in after-flanks; these are not same abrupt isolated pathological examples.

**18 original source-QC1 MDS-filled HOLD runs, 61 HH:** *probable gap-fill provenance/continuity artefacts*, often occurring directly after QC2 ERA-filled reference and staying nearly constant at much colder T. **Recommendation: candidate same-native packaged ERA temperature substitution only for operator-approved trustworthy interval bounds**, with QC2 and physically consistent VPD/RH, not blind original-source modification. The old HOLD intervals are often NOT the true full outlier interval; source immediate after-flanks continue at QC1. Therefore do not treat *61 flagged HH only* as automatically exact full replacement scope until proper boundaries defined.

### QC0 exact before/source/after examples (all °C)

| Native interval | Original before TA / processed ERA | Anomaly source TA / paired ERA | After TA / processed ERA | Assessment |
| --- | --- | --- | --- | --- |
| 2003-May08 11:30–14:00 +15:00–15:30 (8 source HOLD HH) | May08 11:00 **10.933/15.632** | 12:00 **−2.924/17.182**, 15:30 **−0.402/16.934** | 16:00 **12.870/16.626** | Strong artifact, interrupted by 14:30 **12.984/17.346** source QC0, so **do not silently overwrite this 14:30 time** |
| 2003-May30 07:30–08:30 +09:30–10:30 (6 source HOLD HH) | May30 07:00 **−3.661/12.110** already bad | 08:00 **−20.181/11.115**; 10:00 **−30.297/11.213** | 11:00 **−17.956/11.869** still bad; 12:30 **−1.501/12.338** still bad | **Source anomaly exceeds original 6 flagged HH**. Evaluate actual beginning and return from original full-day T/ERA before selecting an authorised span |
| 2001-Aug14 10:30 (1) | 10:00 **20.479/20.479** QC2 | **0.000/20.472** QC0 | 11:00 **20.464/20.464** QC2 | Obvious isolated return-to-reference failure |
| 2001-Aug14 14:30 (1) | 14:00 **22.074/22.074** QC2 | **12.118/22.140** QC0 | 15:00 **22.206/22.206** QC2 | Obvious isolated failure |
| 2003-May06 14:00 +15:30 (2) | 13:30 **8.370/12.542** QC0 | 14:00 **−7.378/12.577**, 15:30 **1.779/12.683** | 16:00 **13.685/12.716** QC0 | Two isolated pathological dips, not blanket afternoon replacement |
| 2003-May10 18:00 (1) | 17:30 **11.607/13.325** | **−7.779/12.209** | 18:30 **8.631/12.088** | Isolated implausible dip |
| 2003-Jun03 15:30 (1) | 15:00 **17.047/19.327** | **−9.442/19.344** | 16:00 **17.707/19.360** | Isolated implausible dip |
| 2001-Oct02 14:30–15:00 (2) | 14:00 **14.094/19.131** | 14:30 **11.259/19.285**, 15:00 **11.319/19.440** | 15:30 **11.154/19.082**, 16:00 **10.658/18.723** | **HOLD decision / likely retain T**; no isolated -20°C shock |
| 2007-Mar29 19:00–19:30 (2) | 18:30 **9.400/10.064** | 19:00 **3.908/12.664**, 19:30 **2.290/11.552** | 20:00 **1.316/10.439**, 20:30 **0.647/9.906** | **HOLD decision / likely retain T**; sustained cooling, original QC0 |

### QC1 complete 18 old HOLD episodes (61 HH), reference starting native values

| Source HOLD interval | HH | Previous 30-min source TA / ERA | Start of HOLD source TA / ERA | First following 30-min source TA / ERA | Important |
| --- | ---: | --- | --- | --- | --- |
| 2002-May22 19:30→May23 00:30 | 11 | 18.119/18.119 QC2 | **−0.475/18.080** QC1 | May23 01:00 **1.633/16.031** QC1 | Bad fill continues beyond HOLD; a separate May23 02:00 flagged time exists |
| 2001-Nov01 20:00–23:30 | 8 | 1.515/12.360 QC1 | 1.523/12.343 QC1 | Nov02 00:00 **1.594/9.421** QC1 | Preceding QC1 plateau also bad; do not simply fix 8 HH |
| 2002-May21 19:30–21:30 | 5 | 14.058/14.058 QC2 | **−0.395/13.904** QC1 | 22:00 **−0.395/8.263** QC1 | Flat-filled value continues |
| 2004-Sep26 18:00–20:00 | 5 | 18.471/18.471 QC2 | **6.473/18.211** QC1 | 20:30 **6.420/16.233** QC1 | Plateau beyond HOLD |
| 2007-May10 19:30–21:30 | 5 | 23.432/23.432 QC2 | **3.507/22.862** QC1 | 22:00 **5.118/16.579** QC1 | 2007 May paired multi-day artifact |
| 2008-Apr04 18:30–20:30 | 5 | 4.808/4.808 QC2 | **−6.084/5.019** QC1 | 21:00 **−6.793/4.713** QC1 | 2008 Apr clock-locked repeated episode |
| 2007-May09 20:00–21:30 | 4 | 18.775/18.775 QC2 | **5.357/18.883** QC1 | 22:00 **4.553/14.954** QC1 | Same two-night family |
| 2008-Apr03 18:30–20:00 | 4 | 5.787/5.787 QC2 | **−7.530/5.786** QC1 | 20:30 **−7.548/4.739** QC1 | Third repeated night |
| 2008-Apr02 18:30–19:30 | 3 | 3.426/3.426 QC2 | **−7.474/3.338** QC1 | 20:00 **−7.574/2.591** QC1 | Again continues after source HOLD |
| 2007-Feb07 17:30–18:00 | 2 | −13.939/−13.939 QC2 | **−22.797/−14.271** QC1 | 18:30 **−22.925/−14.970** QC1 | Older Feb07 plateau closely related to approved Feb08–12 events; expand only with exact provenance |
| 2008-Mar29 18:30–19:00 | 2 | 3.912/3.912 QC2 | **−6.685/3.493** QC1 | 19:30 **−6.728/2.510** QC1 | Starts same 18:30 clock pattern |
| 2002-Mar16 18:00 | 1 | −0.456/−0.456 QC2 | **−7.837/0.192** QC1 | 18:30 **−7.812/0.236** QC1 | Continued gap-fill issue |
| 2002-Mar18 19:00 | 1 | −4.924/3.632 QC1 | **−4.906/4.396** QC1 | 19:30 **−4.884/3.439** QC1 | Earlier segment already very different |
| 2002-May23 02:00 | 1 | 1.805/16.122 QC1 | **1.969/16.214** QC1 | 02:30 **2.129/15.762** QC1 | Same May22→May23 continuous issue |
| 2005-Nov11 16:30 | 1 | 10.701/10.701 QC2 | **1.403/9.442** QC1 | 17:00 **1.339/8.184** QC1 | Fill-start discontinuity |
| 2007-Nov12 16:30 | 1 | 7.889/7.889 QC2 | **−2.658/6.732** QC1 | 17:00 **−2.676/5.575** QC1 | Fill-start discontinuity |
| 2008-Feb23 17:30 | 1 | −2.239/−2.239 QC2 | **−11.893/−2.757** QC1 | 18:00 **−11.836/−3.275** QC1 | Fill-start discontinuity |
| 2008-Feb24 17:30 | 1 | 1.478/1.478 QC2 | **−11.078/1.077** QC1 | 18:00 **−11.016/0.677** QC1 | Fill-start discontinuity |

**Plan for operator approval, not action already taken:** select a *new independent research temperature candidate* with (i) strong-anomaly source QC0 times and (ii) full source-demonstrated untrustworthy original QC1 MDS-fill episodes, using original packaged processed `TA_ERA` at same native time, trial T QC2. Preserve all old files and previously audited 106/137-HH interventions; require candidate VPD physical compatibility, exact window science authorisation, and complete SHA-diff audit. **Do not overwrite two ambiguous observed-QC0 source runs** or all original QC1 per se. The source HOLD ledger itself must remain immutable; separate "user decision" ledger tracks authorised alternatives.

**Remaining humidity QA:** before this next temperature decision, **500 HH** outside the user's 106 authorised Syv periods fail basic VPD saturation at source T, overlapping the **85 T-HOLD HH**; **18 HH** pass saturation but source original reasons require documented disposition. No automatic claim that the entire scientific grid/TA/Humidity site is model-ready. No Post-v5/DATM/CIME/Slurm/spinup release.

**Decision status:** 85-HH review and analysis completed in provided operator log, but the researcher has NOT yet approved these further 85-HH temperature replacements. Treat all notes above as recommendations only.

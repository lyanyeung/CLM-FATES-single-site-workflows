# US-MOz Stage14H — ACTUAL 2026-10-29 04:30 UTC original Jan09 QC report and one bounded Stage14I next experiment

The operator ran the Stage14H exact signed source read-only audit successfully on IRIDIS6, full 2005-01-03 through Jan10 original source/QC+selected-native 384 HH. Actual output:

\`/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03/reports/US_MOz_14H_Jan09_full_source_QC_onepass_20261029T043047Z_69844035\`

Actual SHA evidence: prior full Stage14G source receipt \`fda0ebdc6429cb105aa82eb1121987a6f6516cba8a2bebea36ae6b286cf7a370\`; original FLUXMET tower release \`6e823ef0aa59be7c47f4e244c72fea8d9f9e5cd6c8e49715f1931e1e25c832a9\`; original paired FLUXNET-ERA source \`77107f67fc28cb051ab44abfbdf5527f55c28510342bbaeb2610d32ee7b4de7c\`.

## Exact observed (QC/provenance) facts in actual operator output

- Native 2005-Jan09 exactly **48 half-hours**: original T **QC0=0**, **QC1=45**, **QC2=3**; original VPD QC0=0. No genuine measured Jan09 T+VPD QC0 pairs. All source QC2 observations are ERA-based, not independent tower measurements. Original paired tower T–companion ERA T reaches **−18.140°C**, max **+3.079°C**. **27** native source QC1 rows have T–ERA below −5°C, **0** are above +5°C. Original implied RHwater all physically >=0 and signed selected trial water/QBOT has **0** physical failures. Physically positive e does NOT establish source T correctness.
- From actual 8-Jan through 10-Jan selected half-hour T, **10 jumps >4°C**, VPD **0 jumps >4hPa**. Large Jan09 T edges include 07:30→08:00/08:00→08:30, 10:00→10:30 **+10.153°C**, 11:00→11:30 **−14.501°C**, 12:30→13:00 **+18.841°C**, 13:00→13:30 **−15.411°C**, 15:00→15:30 +8.475°C and 16:00→16:30 −4.274°C. The 10-count also includes existing **Jan08** QC1-only excursions and must not be falsely attributed solely to the Jan09 event.
- Original T+VPD source grading: **3 contiguous paired QC1 source runs** intersect Jan09:
  * 2005-01-06 13:00→2005-01-09 10:00: **139 HH**, T minus ERA [−11.382,+15.014]°C.
  * 2005-01-09 11:30→12:30: **3 HH**, T minus ERA [−18.140,−15.263]°C.
  * 2005-01-09 13:30→2005-01-10 09:00: **40 HH**, T minus ERA [−17.606,−0.035]°C.
  The first 139 HH includes the earlier **already user-approved Stage13L 40 source replacement** and also many temperature values with no large original discrepancy. **DO NOT blanket-replace 139 HH**.
- Native Jan09 **10:30, 11:00, 13:00** are original \`TA_F_QC=VPD_F_QC=2\` and equal the ERA-downscaled companion; **protect them** in new scenarios (not measured QC0). Original Jan10 **09:30** is \`TA_F_QC=VPD_F_QC=0\` (measured); **protect it as a real observational anchor**. Native QA confirmed true Jan05 19:30 QC1->QC1 bridge and Jan06 09:30 QC1->QC2, so there is no scientific excuse to redo the successful earlier source.
- Jan09 original 00:00–07:00 QC1 source differs from ERA by only ~1–3°C and source T changes smoothly; preserve these non-extreme records rather than blanket-replace all 45 QC1 rows simply because QC=1.

## Explicit manual choice: three new exact research-only QC1 regions (total 49 HH)

A single Stage14I run generates TWO independent, isolated, nonproduction source variants for exactly:

1. 2005-01-09 **07:30–10:00** (6 original QC1 HH; include 07:30/08:00/08:30 oscillation even if |T−ERA|<5 to avoid false threshold restriction);
2. 2005-01-09 **11:30–12:30** (3 original QC1 HH; original strong negative T−ERA);
3. 2005-01-09 **13:30–2005-01-10 09:00** (40 contiguous original QC1 HH; preserve the exact source regime through the real observed **09:30 QC0** transition rather than make an arbitrary threshold-driven early stop).

Variant A uses signed original native FLUXNET companion \`TA_ERA,VPD_ERA\`; Variant B uses **the already downloaded** CDS ERA5-Land native timestamp interpolation from \`t2m,d2m,sp\` at the published official BIF UTC−6. Both are ERA-linked hypotheses, neither is an independent true tower observation. Only QC1 source records may be changed. The 3 original QC2 rows and Jan10 real QC0, previous successfully executed Jan05/06 27 reanalysis+1 QC1 bridge+40 user-approved slots, original tower release, pressure, native clock and every other selected input are exactly preserved. Every native 30min candidate reconstructs QBOT from \`e=esw(T)-VPD\` and retained PSRF and must pass whole **315360** source model water VPD/QBOT/TBOT closure. Source provenance and both alternative candidate edge jumps are *reported*, not silently smoothed or automatically approved. **Jan08 >4°C source QC1 problems are documented, not auto-overwritten in this Jan09-only bounded task**.

[Stage14I one-run fully pinned 49 QC1 dual research scenarios](../scripts/stage14/14i_US_MOz_Jan09_49QC1_two_source_isolated_onepass.py) — source Git commit \`b0b14f8145cd091af3f241db08cc5854669af128\`, Git blob \`b995bddccf544961b8e5a489b0bd14632e7becc7\`. As of creation, this Stage14I script **has not yet been run on IRIDIS6**. Prior numerically complete Stage14G source exists and remains unapproved for Post-v5, DATM, AD400, Slurm. Stage14I writes only isolated research versions and ledger/edge reports, never overwrites any existing data.

Operator one-run instructions:
\`\`\`bash
(
 set -euo pipefail
 F="$HOME/US_MOz_Jan09_49QC1_onepass.py"
 curl -fLsS --retry 3 "https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/b0b14f8145cd091af3f241db08cc5854669af128/examples/AmeriFlux_MultiSite_10_Batch03/scripts/stage14/14i_US_MOz_Jan09_49QC1_two_source_isolated_onepass.py" -o "$F"
 test "$(git hash-object "$F")" = "b995bddccf544961b8e5a489b0bd14632e7becc7"
 python3 -B -c 'import pathlib,sys; f=pathlib.Path(sys.argv[1]); compile(f.read_text(),str(f),"exec"); print("SYNTAX PASS")' "$F"
 python3 -B "$F" --run 2>&1 | tee "$HOME/US_MOz_Jan09_49QC1_onepass.log"
)
\`\`\`

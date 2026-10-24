# AmeriFlux Batch02: Stage11–31 scientific audit and provenance
**Snapshot: 24 October 2026. All forcing repairs remain on scientific HOLD.** No DATM, CIME, or model run was approved. No data or NetCDF files are stored in GitHub.

## 1. Historical scripts recovered as exact Git blobs
Stage11–22 restored from the prior commit [880b3b62](https://github.com/lyanyeung/CLM-FATES-single-site-workflows/commit/880b3b62ad43f0bcdacc49b58a859abc7ac0dca3); these are the original scripts, not reconstructed substitutes.

- Stage11 and 11b: 4,884 unresolved cold-humidity rows, proposal and audit; all provisional.
- Stage12: humidity physical/source review.
- Stage13, 13b–13f: ERA5 dewpoint pilot, comparison, timezone and drought checks.
- Stage14: adjacent tower QC study.
- Stage15 and 16: verified five ERA5 one-year pilot and full-year comparison.
- Stage17 and 18: exact anomaly-year retrieval plan and previously downloaded ERA5 grid-year receipts. **Do not re-download unnecessarily.**
- Stage19: all 4,884 target timestamps independently examined with CDS ERA5 T, dewpoint and pressure.
- Stage20: water/ice saturation and RH-vs-dewpoint transfer.
- Stage21: 3,947 unapproved risk-screen candidates and 937 additional HOLD.
- Stage22: A/B/C risk tier; categories do **not** constitute approval.

## 2. Operator's original inline Stage23–30 audit findings
The original Stage23–30 code ran as inline Python in IRIDIS6 shells, not as files committed to GitHub. The new **read-only reproducibility scripts** under scripts/stage23–stage30 use a common implementation in scripts/diagnostics; they reproduce the scientific screens, but are not byte-for-byte copies of the original ephemeral commands. Until rerun, the following remain historical operator-reported evidence.

| Stage | Key result |
|---|---|
| 23 | 4,879/4,884 original final T/VPD pairs violate the 0.005-hPa-tolerant water-saturation condition; 4,884/4,884 FLUXNET ERA pairs violate it |
| 24 | Outside Stage19, 19,734 additional final violations and 10,268 additional embedded ERA violations; these sets overlap |
| 25 | 29,504 distinct outside-Stage19 flagged times = 19,236 FINAL_ONLY + 9,770 ERA_ONLY + 498 BOTH |
| 26 | Ho1: 15,446/15,459 mixed observed-TA/ERA-VPD failures have physically consistent companion ERA pairs; EML: 2,039 bad measured-TA/MDS-VPD pairs are also bad as MDS pairs |
| 27 | Ho1 median ERA-minus-tower T gap +14.062°C across mixed failures, with multiple multi-day winter episodes; EML MDS VPD QC=1 for all 2,039 records; one borderline 2010 QC0/QC0 exceedance ~0.0092 hPa |
| 28 | FLUXMET-embedded and standalone ERA T/VPD are equal for all 4,884 Stage08 unresolved timestamps; all companion ERA inferred RH values below −2% and equal to Stage08 diagnostics |
| 29 | Independently downloaded CDS ERA5 RH numeric valid 4,884/4,884; 431 dewpoint transferred VPD values negative at retained T (Ho1 425, GLE 6); 2,782 ice supersaturation cautions; still no observed humidity validation |
| 30 | Conditional QC0 measured-T comparison at held timestamps: 938 independent paired anchors across sites |

### Stage30 observed-temperature comparison (at selected Stage19 timestamps only)
| Site | QC0 anchors | FLUXNET-downscaled T MAE °C | CDS ERA5 T MAE °C | CDS closer | FLUXNET closer |
|---|---:|---:|---:|---:|---:|
| US-EML | 618 | 2.379 | 3.978 | 209 | 408 |
| US-GLE | 103 | 2.525 | 3.033 | 46 | 57 |
| US-Ho1 | 216 | 2.804 | 1.481 | 147 | 69 |
| US-ICh | 0 | — | — | 0 | 0 |
| US-ICt | 1 | 3.776 | 2.103 | 1 | 0 |

The comparison is **conditional on the held anomaly selection**, not full-year model performance. VPD positivity under a water-saturation constraint is necessary, not sufficient, evidence for a scientifically valid replacement. FLUXNET internal ERA and independent CDS ERA5 are different processing chains; ice-saturation and altitude uncertainty remain. US-Ho1 UTC offset is **provisional**. No RH floor clipping or QC0 alteration is authorised.

## 3. Stage31 next: source-aware sensitivity design gate
Read-only compare retained measured temperature (QC0), ERA-origin temperature (QC2), and other sources with CDS ERA5 RH transfer and dewpoint actual-vapour-pressure transfer, including ice and physical-caution flags. No forcing files are created and no spin-up should be submitted. Independent humidity/timing/altitude checks are still needed.

## 4. GitHub → IRIDIS6 reproducible execution
Download the common engine plus requested stage wrapper from the canonical main branch into a clean folder (no `git pull`, especially if the working tree has conflicts):

```bash
set -euo pipefail
RAW=https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/examples/AmeriFlux_MultiSite_10_Batch02
D="$HOME/Batch02_science_audits"
mkdir -p "$D/diagnostics" "$D/stage31"
curl -fLsS "$RAW/scripts/diagnostics/batch02_stage23_31_audits.py" -o "$D/diagnostics/batch02_stage23_31_audits.py"
curl -fLsS "$RAW/scripts/stage31/31_sensitivity_design_gate.py" -o "$D/stage31/31_sensitivity_design_gate.py"
PY=/home/ly3n24/.conda/envs/clm_fates_env/bin/python
"$PY" "$D/stage31/31_sensitivity_design_gate.py" --check
"$PY" "$D/stage31/31_sensitivity_design_gate.py" --audit
```

Both script modes are read-only; they verify source SHA256 and scientific HOLD before reporting. The `curl` steps write **only downloaded script copies** to home. No source CSV, forcing, NetCDF, DATM, case, or Slurm job is modified.

## 5. Existing candidate protection
The five Stage07 numeric-only candidates US-BZS, US-CMW, US-Ha1, US-Ho2, US-Ho3 remain preserved; they are not approved. The Stage08 incomplete marker, 4,884 HOLD rows and CDS source receipts remain protected. OSH-site eligibility and reference land cover/PFT, ZBOT, and flux-footprint representation are separate pre-model scientific reviews.

## Stage31 measured output and Stage32 continuation — 24 October 2026

IRIDIS6 operator ran the published Stage31 wrapper with `--check` and `--audit`, both successfully. All 4,884 Stage08 held timestamps were retained; source groups were QC0 measured temperature **938**, QC2 ERA-origin temperature **3,945**, and one other QC1. The RH-transfer variant passed its constructed numerical water-saturation screen for all 4,884, **which is not independent humidity validation**. Dewpoint actual-vapour-pressure transfer to retained site T produced **431 negative VPD values** (US-Ho1 425 in QC2 group, US-GLE 6: 4 QC0 and 2 QC2). ERA5 ice supersaturation cautions: **2,782** (EML 815, GLE 194, Ho1 29, ICh 141, ICt 1,603). All zero science approvals.

**Stage32** (`scripts/stage32/32_review_humidity_source_phase_risks.py`) checks the mathematical A/B/C alternatives **without creating a repaired forcing**: (A) transfer ERA5 water RH to retained site T; (B) transfer ERA5 dewpoint-derived vapour pressure to retained site T; and (C) use ERA5 T + ERA5 RH as a numerically paired *reference only*. It separates recorded source QC0/QC2, subzero water/ice physical constraints, phase warnings, temperature differences, and a hierarchical HOLD review priority. US-Ho1 clock remains an overriding hold. Stage32 is a new executable script: live IRIDIS output pending and should be reported separately from Stage31 operator evidence.

Download and run Stage32 on IRIDIS6 using a specific GitHub commit hash instead of `git pull` into an unresolved working tree:

```bash
set -euo pipefail
RAW=https://raw.githubusercontent.com/lyanyeung/CLM-FATES-single-site-workflows/main/examples/AmeriFlux_MultiSite_10_Batch02
DIR="$HOME/Batch02_science_audits/stage32"
mkdir -p "$DIR"
curl -fLsS "$RAW/scripts/stage32/32_review_humidity_source_phase_risks.py" -o "$DIR/32_review_humidity_source_phase_risks.py"
PY=/home/ly3n24/.conda/envs/clm_fates_env/bin/python
"$PY" "$DIR/32_review_humidity_source_phase_risks.py" --check
"$PY" "$DIR/32_review_humidity_source_phase_risks.py" --audit
```

The `curl` command writes only the local downloaded script copy to HOME; the script itself does not write output files or change original data, forcing, DATM, CIME, or jobs. Old Stage11–22 data retrievals must not be rerun without need.

## Stage32 completed and Stage33 next (24 October 2026)

Stage32 was executed successfully on IRIDIS6 (both --check and --audit). All 4,884 Stage19–21 source records matched their pinned SHA256 lineage and remain SCIENTIFIC HOLD, with 0 approved repairs.

**Stage32 summary:** 4,884 RH-transferred water-VPD numerical candidates are physically bounded by construction (not independently humidity-validated). Td-transfer water-negative VPD occurs 431 times: US-Ho1 425 (all source QC2 temperature), US-GLE 6 (4 QC0, 2 QC2). 2,782 grid-ERA5 ice-RH warnings were recorded. At the *retained site temperature*, RH-transfer ice saturation is exceeded 1,616 times (EML 540, GLE 171, Ho1 160, ICh 30, ICt 715); Td-transfer ice saturation is exceeded 529 times (EML 13, GLE 47, Ho1 469, ICh 0, ICt 0). Counts overlap and should not be summed as unique events.

**Mutually exclusive review routes:** P0_HO1_CLOCK_HOLD 917; P1_TD_WATER_SUPERSAT_HOLD 6; P2_ICE_PHASE_HOLD 2,773; P3_TEMPERATURE_REPRESENTATIVENESS_HOLD 818; P4_UNVALIDATED_HUMIDITY_HOLD 370. All are HOLD, including P4.

Strong Ho1 temperature inconsistency: 1999-02-13 01:00 retained TA -12.561 C, CDS ERA5 TA +9.2454 C, dewpoint +8.7993 C, hence Td-transfer water VPD -8.9817 hPa. Do not blindly substitute dewpoint or alter tower observations.

**Stage33** script: scripts/stage33/33_audit_US_Ho1_clock_alignment.py. It reuses the existing receipt- and SHA256-verified Stage15/18 NetCDF site-years, verifies Stage19 nominal local-UTC=-5 interpolation and the 425 negative water-VPD count, and tests offsets -7..-3h against all original tower QC0 observations in covered years, winter QC0, and the held QC0 subset. Offset sensitivity is NOT independent UTC/BADM certification, and full site grid orography remains unknown. Original US-Ho1 FULLSET 3-6 has no BIF. AmeriFlux official site https://ameriflux.lbl.gov/sites/siteinfo/US-Ho1 reports 45.2040 N, -68.7402 longitude and 60m elevation but does not alone establish the release UTC offset. No additional CDS download is needed. Stage33 live IRIDIS results are not yet verified.

Stage33 usage: download the single Python source to HOME from a pinned GitHub commit, then run --check followed by --audit. Both operations read only scientific/source data and never modify forcing, CIME, DATM or Slurm.

### Stage33 v2 receipt-path verification fix (24 October 2026)

First operator test: Python compilation passed, but `--check` stopped at the US-Ho1 1996 Stage15 `verified_receipt.json`: `Pinned verified receipt differs`. Root-cause in code: Stage19 stored receipt ledger keys using original `Path.home()` spelling without calling `resolve()`, while the initial Stage33 revision resolved the candidate receipt path **before** performing exact-string dictionary lookup. On systems with `/home/ly3n24` and `/iridisfs/home/ly3n24` aliases, an absent dictionary key was treated as a hash mismatch. This is an identified code-path bug; a true on-disk source mismatch has **not** been established by that traceback alone.

V2 `verify_ledger_file` locates ledger entries referring to the *same resolved file*, requires one unambiguous expected digest across matching aliases, computes and verifies the actual file SHA256, and still verifies the NetCDF against both Stage19 and its verified receipt. It never weakens hashes or silently skips missing files. After the fix, re-run `--check` and only then `--audit`. A future failure indicates a separate mismatch requiring diagnosis. Shells configured with interactive `set -e` may close on failed `python` commands; run inside an `if ...; then ...; else ...; fi` guard or `set +e` when troubleshooting. No forcing edits or scientific approvals.


## Stage33 VERIFIED and Stage34 next (24 October 2026)

Stage33 v2 successfully completed on IRIDIS6 with exit code 0: 16 ERA5 grid-year receipts/NetCDF hashes verified; the original US-Ho1 meteorological release pinned; 917 Stage19 anomalous timestamps reproduced; and Stage32's 425 negative dewpoint-transfer VPD events reproduced. There was no source change, download or job submission.

Local-minus-UTC sensitivity MAE for 106,336 observed QC0 temperature comparisons, from -7 to -3 hours, was 2.153, 1.708, **1.472 (nominal -5)**, 1.558, 1.889 degrees C respectively. Winter QC0 (n=35,409) MAE was 1.999, 1.641, **1.482**, 1.587, 1.850 degrees C. Selected held QC0 (n=216) MAE was 1.894, 1.566, **1.481**, 1.544, 1.634 degrees C. Negative Td-transfer VPD counts across same hypothetical offsets were **421, 425, 425, 427, 425** (out of 917). Therefore clock choice alone cannot explain or resolve the 425 conflicts.

Original QC0 temperatures are missing in the Stage19 years 1997, 1998, 2001-2005 and 2022, with only one source QC0 record in 2007. The dramatic gapfill source discrepancies are in years lacking direct temperature confirmation. Time offset -5 is the **best tested** temperature fit, but NOT officially certified without US-Ho1 BADM UTC_OFFSET. The FLUXNET2015/ONEFlux convention is local standard time (no daylight-saving changes); the authoritative offset should be checked from site metadata: https://fluxnet.org/data/fluxnet2015-dataset/ and https://ameriflux.lbl.gov/sites/siteinfo/US-Ho1 .

Stage34 script: scripts/stage34/34_audit_US_Ho1_QC2_temperature_provenance.py . This new READ-ONLY audit verifies Stage19-21 and original source SHA256/row identities, then compares 917 held US-Ho1 cases and the 425 QC2 negative-Td-transfer cases by year, including observed QC0 coverage and FLUXNET downscaled versus CDS ERA5 temperature divergence. It reproduces Stage30 selected QC0 MAEs before drawing a source-specific scientific interpretation. It does not infer or approve any correction, or modify forcing, NetCDF, CIME, DATM or Slurm. It still requires first IRIDIS6 execution to validate.

## Stage34 verified; Stage35 Howland neighbouring-tower QC0 evidence (24 October 2026)

Stage34 completed successfully on IRIDIS6: 917 Ho1 held records, 425 negative water VPD under CDS dewpoint transfer, ALL source QC2 temperature. Among 425, abs(CDS T minus FLUXNET QC2 T) exceeds 5C in 394, 10C in 281, 15C in 92, and 20C in 22. The median CDS-minus-FLUXNET temperature difference is +11.7672C. QC2 controls without negative dewpoint transfer (n=275) have a median difference of -0.1071C. Stage30 selected QC0 anchors reproduced (n=216, FLUXNET MAE 2.804C, CDS MAE 1.481C).

Year counts of negative dewpoint transfer: 1998 64, 1999 25, 2001 230, 2003 1, 2004 6, 2005 60, 2007 39. Original US-Ho1 within-year QC0 availability is zero in 1998, 2001, 2003, 2004, 2005, and 1 in 2007; hence objective validation of the QC2 temperatures remains outstanding. There are 3,005 Ho1 QC0 samples in 1999, though none at the selected Stage19 held cases. UTC−5 is the lowest-MAE tested offset, not independently BADM certified.

Next: scripts/stage35/35_audit_Howland_neighbour_QC0_temperatures.py — a read-only SHA256-pinned comparison against original measured-coded temperatures from nearby US-Ho2 west tower (available from 1999) and US-Ho3 harvest tower (available from 2003). It checks QC2 run lengths, annual neighbouring QC0 availability, matched-timestamp MAEs within 917 cases and the 425 negative Td-transfer cohort. The neighbouring towers are not necessarily independent instruments, the harvested site differs ecologically and Ho1 time metadata remains provisional. In 1998 neither neighbour has product coverage. No new CDS download or model action. Stage35 live IRIDIS result pending.

Official AmeriFlux site pages: https://ameriflux.lbl.gov/sites/siteinfo/US-Ho1 ; https://ameriflux.lbl.gov/sites/siteinfo/US-Ho2 ; https://ameriflux.lbl.gov/sites/siteinfo/US-Ho3 .

## Stage35 VERIFIED — adjacent Howland tower QC0 evidence (24 October 2026)

Operator ran Stage35 --check and --audit successfully on IRIDIS6, with all original Ho1/Ho2/Ho3 release SHA256 inputs and Stage19–21 lineage verified. The original source QC0 counts were Ho1 **274,148**, Ho2 **350,619**, Ho3 **332,303**. Ho1 retained 917 Stage19 HOLD records, including the 425 negative dewpoint-transfer water-VPD cases, all originally QC2 temperature; none are approved for forcing/model use.

**Critical long QC2 gaps in original Ho1:** 2000-12-27 09:30 to 2007-12-31 22:30 (122,907 half-hours / 2,560.56 d); 1997-01-01 to 1999-10-30 (49,554 half-hours / 1,032.38 d); 2021-10-19 to 2023-12-31 (38,582 half-hours / 803.79 d). These are long temperature-GAPFILL-coded runs, not evidence the physical temperature was continuously bad.

**Neighbour comparisons at the 425 negative VPD timestamps:**
- Ho2 measured-coded QC0 exists for **67** timestamps (2003:1, 2004:6, 2005:60); its MAE versus original Ho1 QC2 T is **9.573°C**, versus CDS ERA5 T **0.814°C**. CDS closer by >0.5°C at **67/67**.
- Ho3 measured-coded QC0 exists for **106** timestamps (2003:1, 2004:6, 2005:60, 2007:39); its MAE versus original Ho1 QC2 T is **9.207°C**, versus CDS ERA5 T **1.152°C**. CDS closer by >0.5°C at **98/106**, FLUXNET closer at 3.
- The Ho2 67 are all within the Ho3 106. Thus **106 unique affected timestamps** have at least one nearby QC0 anchor, not 173 independent events; **319/425 have neither**. There are NO original Ho2 or Ho3 tower records in 1998, and no comparable QC0 observed Ho2/Ho3 in 1999 or 2001.

**Critical independence caveat:** At other Ho1 held *non-negative Td-transfer* samples, Ho3 QC0 and Ho1 temperatures are almost exactly equal in some years: MAE Ho3-Ho1 in 2009 **0.010°C** (47 records), 2010 **0.007°C** (7 records), 2012 **0.000°C** (85 records). That suggests potential duplicated meteorological feed, shared instruments, or correlated processing, not automatically separate independent physical validation. Stage35 also found Ho2 and Ho3 BIFs reporting UTC offset -5, but those BIF files were **not Stage08 SHA-pinned**, so they cannot be regarded as independently certified source metadata. Ho1's release BIF remains absent.

**Next Stage36** \`scripts/stage36/36_audit_Howland_shared_temperature_sources.py\` is read-only and will quantify exact/near-exact QC0 temperature matches across ALL overlapping timestamps among Ho1, Ho2 and Ho3, longest identical runs, year-specific identity rates, and direct Ho2-Ho3 agreement on the exact 67 shared negative-VPD timestamps. It will reproduce unique 106 and missing 319 counts, and specifically investigate whether Ho3 is an independent sensor record before using the neighbouring towers as scientific evidence. Nothing in Stage36 creates or approves a forcing replacement. It has not yet been run on IRIDIS6.


## Stage36 completed: cross-tower source reuse; Stage37 targets 319 unanchored records (24 October 2026)

Stage36 passed both `--check` and `--audit` on IRIDIS6, verifying all original Ho1/Ho2/Ho3 SHA256 inputs and 917 Ho1 held timestamps / 425 original-QC2 negative-Td-transfer cases.

**Evidence of shared or reused temperatures:** QC0 simultaneous pairs Ho1–Ho2 n=219,044, only 1,778 within 0.001°C and longest identical run 4 half-hours; Ho1–Ho3 n=236,463 with 58,558 within 0.001°C, including a 14,957-half-hour *consecutive* identical-temperature run from 2012-01-01 to 2012-11-07 (~311.6 d); Ho2–Ho3 n=285,693 with only 1,287 within 0.001°C, longest run 3 half-hours. Ho1–Ho3 in 2010 and 2012 have unusually high exact-identity rates (~48.6% and ~85.1%). These near-perfect blocks strongly suggest shared/reused meteorological feeds or a processing lineage, but do **not independently prove which instrument contributed them**. The output labels QC0 as measured-coded, not physically independent.

**425 failed Td-transfer timestamps:** Ho2 observed-coded QC0=67, Ho3 QC0=106, both=67, Ho2-only=0, Ho3-only=39, neither=319; **106 unique** have a neighbour QC0. On the 67 doubly observed times, Ho2 versus Ho3 air-temperature difference median 0.32°C, p95 0.6641°C, and zero within 0.001°C: these records are two *distinct numerical sequences*, though hardware independence still requires metadata validation. Ho2 67-event MAE relative to original Ho1 QC2 T =9.573°C versus CDS ERA5 T=0.814°C; Ho3 same 67: Ho1 QC2=9.252°C, CDS ERA5=0.840°C. Observational support is stronger for CDS in this **limited 67-timestamp subset**, not a license for all-year replacement.

**Unanchored 319:** 1998 64, 1999 25, 2001 230; no original neighbour QC0 at these times. 1998 precedes both neighbouring FLUXNET releases; Ho2 release exists in 1999 and 2001 but has zero QC0 original temperature in those years; Ho3 begins 2003. The missing evidence requires externally measured source (e.g. AmeriFlux BASE original instrumentation, or NOAA NCEI Global Hourly measured records with verified timestamp/station representativeness).

**Stage37 (NEW, not yet tested on IRIDIS6):** `scripts/stage37/37_audit_Howland_319_unanchored_ERA_provenance.py`. It verifies prior manifests and SHA256, recomputes the 319 event identities and their clustering, and tests whether original **Ho2 FLUXNET ERA temperature** matches Ho1's ERA fill in 1999/2001 or points to a station-specific filling issue. Ho2 ERA is clearly labeled a *nonindependent gridded product*, never a QC0 observation. No external weather data are downloaded, no forcing files written, zero approvals. External station weather is a next-stage prospect, not already collected evidence. Technical source: https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database .

## Stage37 VERIFIED; Stage38 local BASE/BADM and NOAA GHCNh evidence preflight (24 October 2026)

Stage37 ran successfully on IRIDIS6 in both --check and --audit. The three original Howland FLUXMET/FULLSET releases and Stage19/20/21 SHA256 provenance passed; 917 Ho1 held, 425 negative dewpoint-water-VPD (all QC2 source T), and **319 with no Ho2/Ho3 QC0 observed-coded temperature** all reproduce prior Stage36. The 319 are **1998:64**, **1999:25**, **2001:230**.

**1999 (25 events, February 12–14):** original Ho1 QC2 is colder than independent CDS ERA5 T by median 9.4067°C, while original Ho2 TA_ERA is *warmer* than CDS ERA5 T by median 0.6394°C. Ho2 TA_ERA minus Ho1 TA_ERA has median 10.141°C. None of the 25 Ho1/Ho2 ERA T comparisons agree within 1°C; both data are processed sources, NOT independent tower measurements. Example 1999-02-13 01:00 local: Ho1 QC2 T=-12.561°C; Ho2 ERA T=+9.026°C; CDS ERA5 T=+9.2454°C, CDS dewpoint +8.7993°C.

**2001 (230 events, December 14–25):** Ho1 QC2 colder than CDS T by median 11.6203°C; Ho2 ERA T minus CDS T median +0.649°C and Ho2 ERA minus Ho1 ERA T median +12.353°C; no Ho1 vs Ho2 ERA T agreement within 1°C. These comparisons point to a Ho1-specific gapfill/processing issue but do not establish ground truth for those times. **1998 (64 events, November 20–24):** no Ho2 records at all; Ho1 QC2 is colder than CDS T by median 14.5782°C, thus requires independent source meteorology.

Next **Stage38**: `scripts/stage38/38_inventory_Howland_external_temperature_evidence.py`. This is a strictly read-only bounded inventory of local original US-Ho1 BASE/BADM/FLUXNET archives and exact timestamp episodes including *provisional UTC−5 conversion*. It checks the same three original SHA256 pins and 319/425 lineage before printing source acquisition priorities. It makes **no network requests and writes no data**. New candidate source: NOAA **GHCNh** hourly temperature observations, the modern replacement for ISD. NOAA's 23 June 2026 service-change announcement notes legacy ISD FTP/HTTPS retirement and recommends GHCNh for broader historical holdings: https://www.nesdis.noaa.gov/news/service-location-change-integrated-surface-data-global-hourly . Official NOAA GHCNh product: https://www.ncei.noaa.gov/products/global-historical-climatology-network-hourly . NOAA daily metadata identifies Bangor International Airport as USW00014606 (44.79791N, -68.81852W) but **hourly product availability for 1998, 1999, 2001 has not yet been verified**, and this is a candidate, not a validated observed source. NOAA official GHCNh station-year file URL patterns appear in audit output; no download/claim of availability. AmeriFlux official US-Ho1 page says BASE has data from 1996, but availability does not prove the temperature field is original and independent of historical FLUXNET: https://ameriflux.lbl.gov/sites/siteinfo/US-Ho1 .

Any future independent observation comparison must validate station QC, UTC timestamps, station distance/height/microclimate, whether the original sensor has a shared chain with the FLUXNET source, and exact event coverage. **4,884 remain science HOLD; zero approved forcing repairs.**

## Stage38 verified; Stage39 NOAA GHCNh evidence-availability probe (24 October 2026)

Stage38 --audit completed successfully on IRIDIS6. Exact 319 unanchored negative-Td-transfer records were verified against immutable source SHA256 lineage: 1998 **64** records over 4 contiguous episodes (20–24 Nov), 1999 **25** over 3 episodes (12–14 Feb), 2001 **230** over 9 episodes (14–25 Dec). The default local-to-UTC offset used for candidate windows is **-5 h, provisional**, not official BADM-certified. Median CDS T minus original Ho1 QC2 T in each respective year: **+14.578, +9.407, +11.620°C**.

Within a bounded local US-Ho1 forcing/source folder inspection, Stage38 found the original **149,847,335-byte FLUXNET FULLSET_1996-2023_3-6.zip** with 12 product files (FLUXMET, AUXMETEO/AUXNEE, embedded FLUXNET ERA5 aggregations), and **no BASE, BADM or BIF files or ZIP members**. This limited inventory does not exclude BASE/BADM archives elsewhere or their availability from AmeriFlux.

**Stage39 script:** scripts/stage39/39_probe_NOAA_GHCNh_Bangor_history.py. Three explicit modes: --self-test = in-memory test; --check = offline pinned Stage08/19/20/21 source SHA256 + exact 319 timestamps; --probe = make HTTPS GET requests for *candidate* NOAA GHCNh Bangor airport station USW00014606 per-year PSV 1998, 1999, 2001, entirely **in RAM** (32 MiB cap per file), report actual URL existence/status, SHA256, raw UTC DATE/temperature proximity to targets (30/60/90 min), and raw source/quality-code fields as uninterpreted strings. The script does **not** compare these temperatures numerically against FLUXNET, interpolate, assert NOAA quality approval, interpret BADM UTC, edit forcing, or store external data. If HPC cannot access HTTPS or NOAA year file is absent, the outcome must be reported rather than inventing data availability.

NOAA GHCNh official documentation confirms per-station/per-year PSV structure and raw observation source/QC fields: https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/doc/ghcnh_DOCUMENTATION.pdf and https://www.ncei.noaa.gov/products/global-historical-climatology-network-hourly . This does **not** independently confirm specific Bangor station/year PSV availability. Bangor airport is geographically separated from Howland and may reflect airport rather than forest microclimate; station metadata, elevation, UTC, and QC/source-code interpretation are separate science gates. AmeriFlux BASE acquisition remains a parallel source review: https://ameriflux.lbl.gov/sites/siteinfo/US-Ho1 .

**Science status:** Stage08 4,884 HOLD, 0 approved replacements; no DATM, CIME, forcing, NetCDF, model run, or source file modification.

## Stage39 v2 NumPy scalar-allclose preflight hotfix (24 October 2026)

First IRIDIS6 execution passed the Stage39 synthetic `--self-test` and verified original SHA256 for US-Ho1/Ho2/Ho3 (490,896 / 473,376 / 333,120 raw records). It **stopped before NOAA access** during the offline `--check`: `AttributeError: 'bool' object has no attribute 'all'` at original line 121. Root cause: `np.allclose()` itself returns a scalar bool, but two Stage39 preflight comparisons erroneously appended `.all()`. This is a script programming error **not evidence of changed source files or NOAA failure**.

Stage39 v2 removes both invalid `.all()` calls while retaining the original strict numerical equality/tolerance and SHA256 checks, and adds a synthetic NumPy regression check to `--self-test` for equal/mismatched arrays with NaNs. No source, forcing, ERA5, DATM, CIME or Slurm modification. Live `--check` and `--probe` are **pending** after this source change; NOAA file availability remains unverified.

## Stage39 v3 actual GHCNh STATION-column parser fix (24 October 2026)

On IRIDIS6, Stage39 v2 `--self-test` and `--check` passed, including all original Ho1/Ho2/Ho3 SHA256 and exact 319 target timestamps (1998:64, 1999:25, 2001:230). The network `--probe` successfully received three NOAA GHCNh **pipe-separated response headers**, but year-level parsing stopped for all three because v2 incorrectly required a `station_id` column. The real NOAA PSV field is `STATION`; its observed header included `STATION, Station_name, DATE, Year, Month, Day, Hour, Minute, LATITUDE, LONGITUDE, ELEVATION, temperature, temperature_Measurement_Code, temperature_Quality_Code, temperature_Report_Type, temperature_Source_Code`. Thus **PSV responses were reached, but no numeric temperature coverage was validated**.

Stage39 v3 accepts NOAA `STATION` (or legacy `Station_ID` alias), and still demands exactly matching Bangor station identifier `USW00014606`; it preserves original temperature/QC/source fields unchanged. Synthetic self-tests now reproduce NOAA's observed PSV header and QC fields, verify UTC proximity, retain the legacy alias and deliberately reject wrong station IDs, along with the prior scalar `np.allclose` regression check. Download footprint and science boundary remain unchanged: `--probe` reads at most three NOAA station-years into RAM (32 MiB each), prints SHA256 and raw temporal availability, and writes nothing. It **does not interpret NOAA quality flags, independently validate the meteorology, or approve any forcing**. IRIDIS6 Stage39 v3 result is pending; 4,884 remain scientific HOLD, 0 approvals.


## Stage39 v3 VERIFIED: Bangor NOAA GHCNh temperature availability; Stage40 planned (24 October 2026)

Stage39 v3 successfully passed its synthetic parser regression test, original US-Ho1/Ho2/Ho3 SHA256 preflight, exact 319 event scope, and memory-only NOAA GHCNh probe on IRIDIS6. Three REAL station-year PSV source files for Bangor airport USW00014606 were retrieved, with 329 columns and legitimate raw temperature/source/quality fields. In all three years, every Stage37/38 unanchored target has a numerical temperature report within +/-30 minutes at provisional Ho1 local-minus-UTC=-5. This is RAW numerical availability, not scientifically QC-screened eligibility, instrument independence or forcing approval.

| Year | Ho1 missing-neighbour-QC0 targets | NOAA PSV raw records | Plausible numeric-T records | NOAA source byte length | Stage39 v3 PSV SHA256 |
|---|---:|---:|---:|---:|---|
| 1998 | 64 | 10,206 | 10,186 | 7,552,129 | 5d57abd919b39781aca114180b87c51a6b5e80d23cfbc8b5f632ad55b650272d |
| 1999 | 25 | 10,726 | 9,934 | 9,098,114 | 6feeb4cf0cd93cf0ac6b9dc6e7cb2a3a452aa9cd4c7a42fb4212ec4c31869ae1 |
| 2001 | 230 | 10,890 | 10,866 | 9,647,557 | f4c24d57d257eccfc0d82c2c15bcd9b85ab2c65235068fc9f39ff34ae58939fe |

NOAA temperature source/quality fields from real operator data: the older 1998 source is primarily Source_Code 223, Source_Station_ID ICAO-KBGR, Quality_Code 1; years 1999/2001 include Source_Code 335, Source_Station_ID 726088-14606, Quality_Code 5, plus 223/1 reports. The official NOAA GHCNh documentation defines legacy quality code 1 for source 223 as GOOD and legacy code 5 for source 335 as passed all quality control checks with NCEI origin. The code systems are source-dependent. This source-specific screening is provisional only; NOAA integrated quality, physical measurement provenance and independent station microclimate remain scientific caveats. Official methods: https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/doc/ghcnh_DOCUMENTATION.pdf

Stage40 new read-only script: scripts/stage40/40_compare_NOAA_Bangor_QC_with_Ho1_CDS.py . The script REQUIRES pinned Stage39 v3 file 39_probe_NOAA_GHCNh_Bangor_history.py in the SAME local directory. Stage39.gate is reused for original Stage08/19/20/21 SHA256 and exact 319 events. Stage40 pins all three NOAA PSV SHA256s above, and STOPS if the remote station/year bytes differ. It checks both the source-specific QC pair and original source-station identifier, excludes unexpected measurement flags, requires numeric T, then chooses the nearest screened NOAA observation within 30 minutes of each provisional target UTC. It never interpolates or automatically certifies the station/source. It rejects equally near observations if conflicting numerically. Crucially it counts unique NOAA source reports separately from Ho1 half-hour pair count (one hourly report can serve two half-hour targets). It compares differences from Ho1 original QC2 T and from independent CDS ERA5 T only where source-specific QC has passed the provisional screen, with separate yearwise MAEs and error quantiles. No source/forcing/NetCDF edits, no other external stations, no GHCNh disk downloads, no Slurm or CIME jobs, and zero scientific repairs approved.

Bangor airport is approximately 46 km away from Howland Forest: altitude, topography, canopy exposure and local weather may differ substantially. Stage40 is external-location observational evidence, not a replacement instruction. Ho1 UTC_OFFSET is still provisional; AmeriFlux BADM/BASE original instrument provenance remains unresolved. Stage40 script has been staged for publication; actual IRIDIS6 runtime results are PENDING.

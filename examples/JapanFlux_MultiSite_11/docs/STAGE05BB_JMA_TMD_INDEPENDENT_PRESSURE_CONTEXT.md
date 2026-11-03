# Stage05BB: JMA pressure context for JP-Tmd and JP-Fjy

## Status and source boundary

An external, independently operated **JMA Tomakomai surface weather station** (station 47424) was examined read-only on the official JMA historical hourly pages for the three event dates. The browser displayed station pressure (`現地`), sea-level pressure (`海面`) and air temperature; the station-pressure column is used below, not sea-level pressure. JMA observations are not the JP-Tmd tower measurement; the two sites are spatially separated. Nor is statistical independence from ERA5 established: JMA observations could have been assimilated into the underlying atmospheric reanalysis. The Tmd source README local-solar versus operator UTC+9 conflict remains unresolved. These results do not approve or apply any half-hour value.

The Tmd tower BIF lists 42.735911°N, 141.523147°E and site elevation 117 m. A historical Hokkaido government station list gives Tomakomai JMA station 42°37.4′N, 141°32.8′E, station elevation 6 m: https://www.pref.hokkaido.lg.jp/fs/2/4/5/9/9/8/7/_/ooame12-I_file1.pdf . These coordinates imply approximately 12.7 km horizontal separation. The nominal elevation is station ground height; the exact barometer height history and tower pressure-sensor height are not verified here. JMA distributes separate historical station metadata and instrument-height records: https://www.data.jma.go.jp/stats/data/mdrr/man/kansoku_gaiyou.html .

## Directly observed JMA values

The JMA time column is Japanese standard time; the Tmd source-time mapping remains a hypothesis. Values below are the displayed **station pressure**, in hPa, and station air temperature, in °C. A nominal event-centre comparison pairs JMA 03:00, 07:00 and 03:00 with the Tmd native label under UTC+9; this does not establish their exact half-hour equivalence.

| Date | JMA hour (JST) | Station pressure hPa | Station temperature °C | Source |
|---|---|---:|---:|---|
| 2005-08-12 | 02:00 / 03:00 / 04:00 | 1011.4 / 1011.3 / 1011.3 | 19.8 / 19.9 / 20.3 | [JMA hourly page](https://ds.data.jma.go.jp/obd/stats/etrn/view/hourly_s1.php?prec_no=21&block_no=47424&year=2005&month=08&day=12&view=a1) |
| 2011-12-17 | 06:00 / 07:00 / 08:00 | 1012.5 / 1012.8 / 1013.4 | −11.5 / −7.6 / −5.9 | [JMA hourly page](https://ds.data.jma.go.jp/obd/stats/etrn/view/hourly_s1.php?prec_no=21&block_no=47424&year=2011&month=12&day=17&view=a1) |
| 2022-04-09 | 02:00 / 03:00 / 04:00 | 1014.4 / 1014.4 / 1014.2 | 4.7 / 4.3 / 4.2 | [JMA hourly page](https://ds.data.jma.go.jp/obd/stats/etrn/view/hourly_s1.php?prec_no=21&block_no=47424&year=2022&month=04&day=09&view=a1) |

These values were read from the displayed official pages during this work; no original JMA station file was downloaded or hashed. The broader JMA interface reports the selected period in Japan standard time: https://www.data.jma.go.jp/risk/obsdl/?vm=r . The JMA station record is an additional physical context source, not a replacement for missing JP-Tmd QC0 values.

## Explicitly illustrative altitude sensitivity

For a rough check, use the **centre-hour** JMA station pressure, JMA temperature, station elevation 6 m and tower BIF elevation 117 m with an isothermal dry-air hydrostatic approximation, `p(117 m) = p(6 m) × exp[-g × 111 m / (Rd × T)]`, `g=9.80665 m s⁻²`, `Rd=287.05 J kg⁻¹ K⁻¹`. The calculation assumes horizontal pressure homogeneity over ~12.7 km, dry station temperature as a constant layer temperature, and station/site elevation as barometer elevation; none is established to the accuracy needed for correction. The scenario band combines the three displayed JMA hourly pressures, a **chosen** 91–131 m height difference and JMA centre temperature ±10 °C. This is not a confidence interval and does not bound unknown spatial gradients or sensor-height differences.

| Event | JMA centre station pressure hPa | Illustrative site-height pressure kPa | Sensitivity band kPa | Existing QC2 shadow kPa | Shadow minus illustrative kPa | ERA5-Land centre-hour sp kPa |
|---|---:|---:|---:|---:|---:|---:|
| 2005-08-12 03:00 | 1011.3 | 99.82978 | 99.54356–100.10774 | 99.0085 | −0.82128 | 99.65828 |
| 2011-12-17 07:00 | 1012.8 | 99.84396 | 99.49225–100.20306 | 98.9625 | −0.88146 | 99.71734 |
| 2022-04-09 03:00 | 1014.4 | 100.06296 | 99.73699–100.34880 | 99.1950 | −0.86796 | 99.867445 |

The three centre-hour shadows lie roughly 0.82–0.88 kPa below this *illustrative* station-height estimate; the ERA5-Land grid is also lower than that estimate by roughly 0.13–0.20 kPa. This raises a materially important possibility that the Tmd selected QC2 PA background itself is systematically low on these dates, rather than the entire shadow/grid mismatch being explained by a benign station-to-grid offset. It does **not** prove the absolute bias, identify its cause, show that the surrounding QC2 values are wrong, or justify correcting the whole QC2 record. The three episodic comparisons are not 45 independent validation cases, and the JMA values are not tower measurements.

The local calculator `05bb_jma_tmd_pressure_context_READONLY.py` reproduces these numbers without network, source ZIP access, forcing writes or approval. It hardcodes the observations, making their sources and assumptions inspectable. Re-evaluate using historical JMA barometer heights, Tmd sensor height, documented clock, an appropriate spatial-pressure analysis, and additional independent instruments/periods before any bias correction. The separate 45-field shadow package remains HOLD.

## Independent-operation context for JP-Fjy

The official JMA hourly pages also show local station pressure at **Kawaguchiko**, station 47640. Its JMA inventory gives coordinates 35°30.0′N, 138°45.6′E and elevation 860 m ([JMA station inventory](https://www.jma.go.jp/jma/kishou/know/amedas/ame_master_20241218.pdf)). The JP-Fjy BIF lists 35.45454°N, 138.76225°E and site elevation 1043 m, implying approximately 5.1 km horizontal separation and nominal 183 m elevation difference. The station inventory is not a verification of actual barometer heights on either event date.

| Date | JMA hour (JST) | Station pressure hPa | Station temperature °C | Source |
|---|---|---:|---:|---|
| 2005-08-12 | 02:00 / 03:00 / 04:00 | 916.5 / 916.8 / 916.7 | 21.3 / 21.0 / 21.0 | [JMA hourly page](https://ds.data.jma.go.jp/obd/stats/etrn/view/hourly_s1.php?prec_no=49&block_no=47640&year=2005&month=08&day=12&view=a1) |
| 2011-12-17 | 06:00 / 07:00 / 08:00 | 916.0 / 916.9 / 917.2 | −3.5 / −4.4 / −2.1 | [JMA hourly page](https://ds.data.jma.go.jp/obd/stats/etrn/view/hourly_s1.php?prec_no=49&block_no=47640&year=2011&month=12&day=17&view=a1) |

Using the same illustrative dry isothermal method, with 183 m nominal difference and the corresponding centre temperature, gives 89.75197 and 89.58163 kPa. The centre shadow values 89.987 and 89.999 kPa are respectively 0.23503 and 0.41737 kPa higher. Chosen sensitivity scenarios using adjacent JMA pressures, a 163–203 m elevation difference and centre temperature ±10 °C yield 89.44019–90.01671 and 89.17748–89.90587 kPa. These are assumption ranges, not statistical intervals and not bounds on local terrain or spatial gradients. In 2011 the shadow is above this limited scenario range, so the comparison cannot certify it. Hourly station observations and native half-hour tower records also need precise time-interval matching. Fjy's prior UTC+9 convention is better supported than the unresolved Tmd convention; nonetheless the two instrument records, elevation metadata, and possible shared reanalysis inputs still need independent verification. As with Tmd, no JMA source file was downloaded or hashed.

## Related publisher-source caution

JapanFlux2024 is a different dataset from the current JPF FLUXNET release. Its data paper describes ERA5-based annual bias correction and original/multiple-sensor fields; it may offer additional site-level context, but its filled fields are not automatically independent because station observations and ERA5 may be shared: https://essd.copernicus.org/articles/17/3807/2025/essd-17-3807-2025.html . The publisher ADS site was visibly under maintenance at review time, so no alternate release file or clock documentation was accessed. The paper's reference list assigns `10.17592/001.2024102230` to both JP-Tmd and JP-KaL, while the national CiNii metadata sourced from NIPR-ADS identifies JP-Tmd with `10.17592/001.2024121030` and ADS record `A20241210-030`: https://cir.nii.ac.jp/crid/1460022487773192448?lang=en . Treat this as a citation/metadata discrepancy pending direct publisher confirmation, and do not use the duplicated DOI to select a site file.

**All 45 remain SCIENCE HOLD; zero replacement values approved.** No production forcing, original ZIP, PFT, cases, Slurm or AD400 were changed.

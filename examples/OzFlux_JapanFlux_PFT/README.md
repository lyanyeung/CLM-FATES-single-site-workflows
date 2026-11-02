# OzFlux and JapanFlux PFT inputs — 20 stations

Guidance for the fixed-composition (FIXNC) PFT inputs of the 9 OzFlux stations in [OzFlux_MultiSite_09](../OzFlux_MultiSite_09/) and the 11 JapanFlux stations in [JapanFlux_MultiSite_11](../JapanFlux_MultiSite_11/). The structure follows [Ameriflux_PFT](../Ameriflux_Site/Ameriflux_PFT/) and [ICOS_PFT](../ICOS_sites/ICOS_PFT/).

**Status, 2 November 2026.** The v1 tables below are a modelling proposal, not observations. They were reviewed the same day:

- The arithmetic is internally consistent: every row sums to 100, host and FATES vectors agree through DEFAULT14, and the three matrices match. `scripts/check_recommended_inputs.py` checks this.
- A literature re-check changed the verdict for several sites. See [Review verdict](#review-verdict) and the machine-readable [review table](OZ_JP_PFT_REVIEW_20261102.csv).

The v1 files are unchanged. The review proposes revisions for 4 sites (AU-ASM, AU-DaS, AU-How, JP-Yms) and holds 3 (AU-Gin, JP-Tef, JP-Tmd). Nothing becomes an input until the operator accepts it. No surface, parameter file, forcing, case or job was created or changed.

## Files

| File | Contents |
| --- | --- |
| [OZ_JP_RECOMMENDED_INPUT_PFT_20_SITES_20261102.md](OZ_JP_RECOMMENDED_INPUT_PFT_20_SITES_20261102.md) | v1 per-site rationale (Chinese). Read it together with the errata below. |
| [OZ_JP_RECOMMENDED_CLM_FATES_INPUT_PFT_20261102.csv](OZ_JP_RECOMMENDED_CLM_FATES_INPUT_PFT_20261102.csv) | v1 master table: vectors, basis, residual and bare policy, HOLD flags, next evidence |
| [OZ_JP_RECOMMENDED_CLM_PCT_NAT_PFT_20261102.csv](OZ_JP_RECOMMENDED_CLM_PCT_NAT_PFT_20261102.csv) | v1 CLM host `PCT_NAT_PFT_0..14` (0 = bare), each row sums to 100 |
| [OZ_JP_RECOMMENDED_FATES_PFT_PERCENT_20261102.csv](OZ_JP_RECOMMENDED_FATES_PFT_PERCENT_20261102.csv) | v1 FATES `pct_natland` (with bare, sums to 100) and `pct_vegetated_only` (sums to 100 on its own) |
| [OZ_JP_PFT_INPUT_SENSITIVITY_SCENARIOS_20261102.csv](OZ_JP_PFT_INPUT_SENSITIVITY_SCENARIOS_20261102.csv) | 26 alternative or period vectors |
| [OZ_JP_PFT_INPUT_VALIDATION_20261102.csv](OZ_JP_PFT_INPUT_VALIDATION_20261102.csv) | v1 sum / live-PFT / DEFAULT14 round-trip check |
| [OZ_JP_PFT_EVIDENCE_LEDGER_20261102.csv](OZ_JP_PFT_EVIDENCE_LEDGER_20261102.csv) | 67 evidence rows with denominator, period, scope, source and verification status |
| [OZ_JP_PFT_REVIEW_20261102.csv](OZ_JP_PFT_REVIEW_20261102.csv) | **Review of 2 Nov:** verdict, proposed vector, reason, sources, read status, open decision per site |
| [scripts/check_recommended_inputs.py](scripts/check_recommended_inputs.py) | Standard-library consistency check of all of the above |

## How to read these numbers

1. **Each percentage is a share of the model's natural-vegetation landunit, including bare ground (host 0).** It is not a measured footprint cover fraction. FATES `use_fates_nocomp` gives each PFT its own patch, so overlapping strata cannot be represented. Grass under trees, *Sasa* under a forest canopy and a eucalypt understorey all have to be either dropped or given their own area. The forest convention used here drops them.
2. **The source quantity changes from site to site:** stems, basal area, biomass, LAI, crown cover or satellite foliage projective cover (FPC). Each row of the master table names its basis. The values are never silently renormalised.
3. **"Bare" is a model allocation everywhere in this collection.** No station has a measured bare-soil fraction.
   - AU-How, AU-DaS, AU-Dry, AU-Stp: bare is 100 minus peak monthly FPC, so call it "uncovered at peak FPC", not bare soil. At Howard Springs the satellite FPC is biased low by lagoons in the grid cell (Nijzink et al. 2022, pp. 541–542).
   - AU-Cpr: bare is 100 minus the listed strata, and it includes unmeasured *Triodia* hummock grass, litter and crust.
   - The [AmeriFlux design note](../Ameriflux_Site/Ameriflux_PFT/PFT_MAPPING_AND_EXPERIMENT_DESIGN.md) warns against deriving bare ground from 100 minus cover; these rows break that rule knowingly and are labelled.
4. **All 20 sites use only one-to-one DEFAULT14 rows:**

   | Host (CLM) | FATES PFT |
   | --- | --- |
   | 1 | 2 ENF |
   | 3 | 3 DNF |
   | 4 | 1 TropEBT |
   | 5 | 4 EBT |
   | 6 | 5 HydrodecidTropTree |
   | 7 | 6 DBF |
   | 9 | 7 EvergreenShrub |
   | 13 | 13 CoolC3 |
   | 14 | 14 C4 |

   This matches `DEFAULT14` in the AmeriFlux B3_01 machinery. No site-private map is needed. The active FATES parameter file of any new Oz/JP case still has to be checked (`active_case_parameter_verified=NO`).
5. **Each vector describes one stated period.** Driving it with the full release years is a fixed-state experiment. See [Time-dependent sites](#time-dependent-sites).

## Review verdict

Verdicts:
- `KEEP`: v1 stands.
- `REVISE`: the literature supports a different primary.
- `KEEP_PROVISIONAL` / `KEEP_PRIOR` / `KEEP_PERIOD_LIMITED`: usable only with the stated caveat.
- `HOLD`: do not use until the operator decides.

The `Proposed primary` column is a proposal only.

| Site | v1 primary | Verdict | Proposed primary | Uncertainty | Main reason |
| --- | --- | --- | --- | --- | --- |
| AU-ASM | EBT 43 / C4 22 / bare 35 | **REVISE** | EBT 65 / C4 35 | HIGH | Three crown-cover estimates are higher than 43: lidar 65, 74.5 % of land area, core plot 70–80. Bare came from a gridded surface. Grasses form near-complete cover when wet. *Thyridolepis* is C3. |
| AU-Cow | TropEBT 100 | KEEP | — | LOW | Evergreen canopy confirmed. Palms are 9.7 % of basal area and are folded in. |
| AU-Cpr | EBT 33 / EvergreenShrub 10 / C4 3 / bare 54 | KEEP_PROVISIONAL | — | HIGH | Strata values confirmed. *Triodia* (C4) is inside the 54 "bare". Forbs are C3. Tree range 33–43. |
| AU-DaS | TropEBT 30 / HydrodecidTropTree 7.5 / C4 42.5 / bare 20 | **REVISE** | TropEBT 37.5 / C4 42.5 / bare 20 | HIGH | The Nijzink tree cover is already the evergreen component, so splitting it is inconsistent. The 80:20 ratio was borrowed from another site. |
| AU-Dry | TropEBT 26.6 / C4 49.4 / bare 24 | KEEP | — | HIGH | Consistent with the source definition; no deciduous species reported. |
| AU-How | TropEBT 31.8 / HydrodecidTropTree 8 / C4 44.3 / bare 15.9 | **REVISE** | TropEBT 39.8 / C4 44.3 / bare 15.9 | MEDIUM | Same definition issue as AU-DaS. The "~80 %" figure is Hutley 2000, and other sources say 60–70 %. Sensitivity in the review table. |
| AU-Gin | EBT 45 / EvergreenShrub 35 / bare 20 | **HOLD** | — | HIGH | Still no cover number. All three values are priors. |
| AU-Stp | C4 65 / bare 35 | KEEP | — | MEDIUM | *Astrebla* is C4 (NAD-ME). Nijzink also counted all cover as grass. |
| AU-Tum | EBT 100 | KEEP | — | MEDIUM | Understorey LAI 1.5 equals tree LAI 1.4 and is dropped. The 2019 fire changes the state. |
| JP-Api | DBF 100 | KEEP | — | LOW | *Fagus crenata*, no understorey. |
| JP-Fhk | DNF 84.6 / ENF 7.7 / DBF 7.7 | KEEP | — | MEDIUM | Takahashi 2015 confirmed. The equal ENF/DBF split of the non-larch share is an assumption. |
| JP-Fjy | ENF 100 | KEEP | — | MEDIUM | *Ilex* subtree share unknown. |
| JP-Khw | ENF 100 | KEEP | — | LOW | Daytime fluxes are from the sugi sector only. |
| JP-Spp | DBF 100 | KEEP_PERIOD_LIMITED | — | MEDIUM | Valid for 2000–2004 only. After the typhoon, *Sasa* LAI exceeds tree LAI. |
| JP-Tak | DBF 100 | KEEP | — | LOW | Deciduous 97.2 % of basal area. *Sasa* is about 24 % of LAI. |
| JP-Tef | DNF 100 | **HOLD** | — | HIGH | Pre-harvest mixed forest until 2003, then *Sasa*-dominated. DNF 100 fits only part of the record. |
| JP-Tmd | DBF 19 / CoolC3 81 | **HOLD** | — | HIGH | The windthrown former larch site changes every year: *Rubus* shrub, then *Solidago*, then birch. The LAI behind 19/81 was not confirmed. |
| JP-Tom | DBF 100 | KEEP | — | MEDIUM | Qualitative only; no basal-area shares. |
| JP-Tgf | CoolC3 40 / C4 60 | KEEP_PRIOR | — | HIGH | No measured split. The C4 lean is supported by the autumn biomass peak and by C4 respiration of 63–67 %. |
| JP-Yms | DBF 72 / EBT 28 | **REVISE** | DBF 66 / EBT 28 / ENF 6 | MEDIUM | 66/28/6 are functional-group biomass shares. The 6 % residual is conifer, not deciduous. |

## Sites whose PFT fractions are uncertain

**Do not use without an operator decision**
- **AU-ASM:** woody fraction under-estimated in v1. The C3 share of the herb layer and the bare policy are unknown.
- **AU-Gin:** pure prior.
- **JP-Tef:** state changes during the record.
- **JP-Tmd:** state changes every year; key number unverified.

**Usable with the stated caveat**
- **AU-Cpr:** *Triodia* and bare ground are unmeasured.
- **AU-DaS:** deciduous share unknown.
- **AU-How:** deciduous share and bare are uncertain.
- **JP-Tgf:** the C3/C4 split is a prior.
- **JP-Spp:** valid for 2000–2004 only.
- **JP-Yms:** basal area would give about 68/32.
- **AU-Dry:** cover-only evidence.
- **AU-Stp:** bare is a satellite complement.

**Reasonably constrained**
- AU-Cow, AU-Tum, JP-Api, JP-Fhk, JP-Fjy, JP-Khw, JP-Tak, JP-Tom.
- Each still carries the forest-convention omission of its understorey.

## Errata to the v1 Markdown

- **AU-How:**
  - The ~80 % evergreen basal-area share is Hutley et al. 2000 (*Functional Ecology* 14:183), not Hutley et al. 2001 (*Oecologia*). It was seen only as a search snippet.
  - Schymanski et al. 2008 (citing O'Grady et al. 2000) gives 60–70 %.
- **AU-DaS:** the "evergreen : deciduous 80:20" split cannot be applied to the Nijzink tree cover. That cover is the minimum monthly FPC, which the paper itself calls the evergreen component (p. 533). Deciduous foliage is in the seasonal term.
- **AU-Dry:**
  - Interpretation point 3 says the 80:20 prior was applied to AU-DaS and AU-Dry. The AU-Dry primary does not apply it; the split exists only as the `How_like_deciduous_share` scenario.
  - The AU-Dry primary is correct.
- **AU-ASM:** the herb layer is mixed C3/C4. *Thyridolepis mitchelliana* is C3 (Khoshravesh et al. 2020), so the "C4-dominated" reading is not supported.
- **AU-Cpr:** the "shrub 4.4" stratum is itself chenopod (*Maireana pentatropis*). *Triodia scariosa* is the only grass recorded in the core 1 ha plot.
- **JP-Yms:**
  - Kominami et al. 2008 give 66/28/6 as deciduous / evergreen broadleaf / conifer shares of 1999 living-tree biomass.
  - The residual is *Pinus densiflora*, so DBF 72 should be DBF 66 + ENF 6.
- **JP-Tef:**
  - The reference is Takagi et al. 2009, *Global Change Biology* 15:1275.
  - *Sasa* was strip-cut on half of the area before planting.

## Decisions needed from the operator

1. **AU-ASM:** accept woody 65 with the herb remainder and bare 0, following the US-CMW woodland convention? Or keep a bare share? The C3 share of the herb layer also needs deciding. FATES4 versus FATES7 stays as decided in OzFlux Stage21.
2. **Savanna bare:** for AU-How, AU-DaS and AU-Dry, keep "uncovered at peak FPC" as bare, or set bare 0 and renormalise tree:grass as a separate run?
3. **AU-How mode:** run FIXNC, or keep the existing full-competition AU-How case as a control?
4. **Sasa understorey (JP-Spp post-2004, JP-Tak, JP-Tef, JP-Tom):** keep forests tree-only, or give *Sasa* a CoolC3 patch? JP-Tak's LAI share is about 24 %.
5. **JP-Tef and JP-Tmd:** pick one target state and restrict the evaluation years, or hold both sites out of the first FIXNC run.
6. **Revisions:** accept the four REVISE rows (AU-ASM, AU-DaS, AU-How, JP-Yms) and the errata as v1.1?

## Time-dependent sites

| Site | Event inside the release years | Vector represents |
| --- | --- | --- |
| AU-ASM | 2018–2020 mulga dieback; Mulga1 and Mulga2 are separate files | pre-dieback woodland |
| AU-Cpr | 15–19 Jan 2014 fire | pre-fire mallee |
| AU-Tum | 31 Dec 2019 fire (near-100 % ash mortality, understorey consumed) | pre-fire forest |
| AU-Gin | 2023–24 dieback; fuel-reduction burn (date unknown) | intact woodland |
| JP-Api | 2007 beech caterpillar defoliation | undisturbed stand |
| JP-Fhk | thinning May 2014 and Mar 2015 (409 → 249 stems/ha) | pre-thinning, 2006–2013 |
| JP-Spp | Typhoon Songda 8 Sep 2004 (33 % canopy, 28 % tree biomass lost) | pre-typhoon, 2000–2004 |
| JP-Tef | clear-cut Jan–Mar 2003, larch planted Oct 2003 | planted larch only |
| JP-Tmd | windthrow 2004, salvage logging, natural regrowth through 2023 | one undefined regrowth state |
| JP-Tgf | mowing; twice a year since 2006 | mown grassland |

## Validation

```bash
python3 scripts/check_recommended_inputs.py
```

On 2 Nov 2026 the result was `CHECK PASS`: 20 sites, 26 scenarios, 67 ledger rows, and all review proposals pass. The check confirms arithmetic and mapping only. It does not check evidence, and it does not open a FATES parameter file.

## Sources read for the review

Read status:
- **full:** full text or data file opened.
- **second-hand:** the value was taken from another paper that cites the original.
- **snippet:** only a search excerpt or abstract was seen.

Paywalled originals that were not read: Hutley et al. 2011, Cleverly et al. 2013/2016, Eamus et al. 2013, Meyer et al. 2015, Leuning et al. 2005, Yazaki et al. 2016 (blocked), Cao et al. 2024 (blocked).

| Source | Used for | Read |
| --- | --- | --- |
| [Nijzink et al. 2022, HESS 26:525](https://hess.copernicus.org/articles/26/525/2022/), Table 1, pp. 530, 533, 535, 541–542 | Tree/grass FPC definition and values for How, DaS, Dry, Stp | full |
| [Whitley et al. 2016, BG 13:3245](https://bg.copernicus.org/articles/13/3245/2016/), Table 1 | Basal area, height, LAI (values from Hutley 2011) | full / second-hand |
| [Moore et al. 2016, BG 13:2387](https://bg.copernicus.org/articles/13/2387/2016/), Sect. 2.1, 4.3 | AU-How stems, 15 % deciduous overstorey, leaf drop | full |
| [Bristow et al. 2016, BGD preprint](https://bg.copernicus.org/preprints/bg-2016-191/bg-2016-191.pdf), Table 1 | AU-DaS structure | full (preprint) |
| [FloraBase *T. grandiflora*](https://florabase.dbca.wa.gov.au/browse/profile/5305); [EUCLID *C. latifolia*](https://apps.lucidcentral.org/euclid/text/entities/corymbia_latifolia.htm) | Leaf phenology | full |
| [Pinto et al. 2014, J. Exp. Bot.](https://pmc.ncbi.nlm.nih.gov/articles/PMC4085965/), Table 2 | *Astrebla* C4 NAD-ME | full |
| [Fischer et al. 2024, bioRxiv](https://www.biorxiv.org/content/10.1101/2024.03.27.586702), Table 1 | Lidar canopy cover ASM 65 %, Cpr 43 % | full (preprint) |
| [Tarin 2019, UTS thesis](https://opus.lib.uts.edu.au/bitstream/10453/133258/2/02whole.pdf), p. 29 | Mulga 74.5 % of land area (from Cleverly 2016) | second-hand |
| [Eamus et al. 2016, ERL 11:125011](https://iopscience.iop.org/article/10.1088/1748-9326/11/12/125011), Sect. 1.1 | AU-ASM structure, grass cover statement | full |
| [Khoshravesh et al. 2020, Plant Physiol 182:566](https://academic.oup.com/plphys/article/182/1/566/6116299) | *Thyridolepis mitchelliana* is C3 | full |
| [TERN Calperum NVIS 2012](https://portal.tern.org.au/metadata/TERN/6c9f5bdc-c800-497f-ac5b-ffae848b3d82); [TERN Calperum species 2013](https://portal.tern.org.au/metadata/TERN/170a547c-690c-4f7c-8794-35395a9f65c6) | AU-Cpr strata and grass species | full |
| [Stephens et al. 2025, GCB](https://pmc.ncbi.nlm.nih.gov/articles/PMC12291013/), Table 1 | Basal area / height for Gin, Tum, Cpr, ASM | full (Table S1 unread) |
| [TERN Gingin](https://portal.tern.org.au/metadata/TERN/b66d399a-8d40-4e68-a820-c2e06689ac8b); Pisek et al. 2025, Front. Remote Sens., Table 1 | AU-Gin height, LAI | full |
| [van Gorsel et al., AMS 9A.4](https://ams.confex.com/ams/pdfpapers/139191.pdf), Sect. 2 | AU-Tum understorey LAI | full |
| [TERN Cow Bay census](https://portal.tern.org.au/metadata/TERN/ad4c0487-b6c0-463c-bbf9-4dc0c52b28ef) | Palm share (recomputed from CSV) | full |
| [Ueyama et al. 2025, ESSD 17:3807](https://essd.copernicus.org/articles/17/3807/2025/), Table 1 (xlsx), Sect. 2.1, 2.4 | JapanFlux IGBP, years, disturbance, JP-Tmd identity | full |
| [Takahashi et al. 2015, J. Agric. Meteorol. 71:302](https://www.jstage.jst.go.jp/article/agrmet/71/4/71_D-14-00009/_pdf), Sect. 2.1 | JP-Fhk basal area and stems | full |
| Kominami et al. 2008, AFM 148:723, Sect. 2.1, 3.2.2 | JP-Yms functional-group biomass | full |
| [Yamanoi et al. 2015, BG 12:6837](https://bg.copernicus.org/articles/12/6837/2015/), Sect. 2.1, Table 1 | JP-Spp typhoon loss, *Sasa* | full |
| Ohtsuka 2013, J. Geogr. 122:615, Table 1; [AsiaFlux TKY](https://asiaflux.nies.go.jp/site-info/TKY.html) | JP-Tak structure, *Sasa* LAI | full |
| [AsiaFlux TSE](https://asiaflux.nies.go.jp/site-info/TSE.html) | JP-Tef history, *Sasa* strip-cutting | full |
| [AsiaFlux TOE](https://asiaflux.nies.go.jp/site-info/TOE.html) | JP-Tom species | full |
| Shimoda et al. 2005, SOLA 1:169; Ma et al. 2018, ESSD, Sect. 2.1 | JP-Tgf seasonal C3/C4 dominance, mowing | full |
| Shimoda et al. 2009, AFM 149:603 | JP-Tgf C4 share of respiration | snippet |

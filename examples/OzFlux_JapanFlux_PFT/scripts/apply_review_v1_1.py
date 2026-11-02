#!/usr/bin/env python3
"""Apply the operator-accepted 2 Nov 2026 literature review (v1.1) to the v1 OzFlux/JapanFlux PFT tables.

Operator decisions (2 Nov 2026): accept the revisions; bare ground keeps its own share wherever the site has
open ground (same policy as the 50 AmeriFlux and 38 ICOS stations); JP-Tef uses the post-clearcut state; JP-Tmd
after a dedicated trajectory review. Former v1 primaries are kept as `v1_primary_20261102` sensitivity rows, as
the AmeriFlux tables did on 26 Oct 2026.

Refuses to run unless all seven inputs are the exact v1 files (sha256 below); git keeps the v1 versions.
    python3 scripts/apply_review_v1_1.py [directory]
"""
import csv, hashlib, io, json, sys
from pathlib import Path

D = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
T = "20261102"
F = {k: D / f"OZ_JP_{k}_{T}.{'md' if k == 'RECOMMENDED_INPUT_PFT_20_SITES' else 'csv'}" for k in (
    "RECOMMENDED_CLM_FATES_INPUT_PFT", "RECOMMENDED_CLM_PCT_NAT_PFT", "RECOMMENDED_FATES_PFT_PERCENT",
    "PFT_INPUT_SENSITIVITY_SCENARIOS", "PFT_INPUT_VALIDATION", "PFT_EVIDENCE_LEDGER", "RECOMMENDED_INPUT_PFT_20_SITES")}
V1_SHA = {"RECOMMENDED_CLM_FATES_INPUT_PFT": "9f1eee721548bb5b81ea9675b4cae8c269d094650d8931d1e0a58b29ad5f1256",
          "RECOMMENDED_CLM_PCT_NAT_PFT": "96bf80a4cf744edb2c7b2725824ff915202f7ed6379505730f679a406b9c8818",
          "RECOMMENDED_FATES_PFT_PERCENT": "8b4b3fc7c183d41744a8d883a32945879168e2e9e8d437fc5db238713f680bc0",
          "PFT_INPUT_SENSITIVITY_SCENARIOS": "374abf1ff5b7d596f105c7c7a7eb0a0f896e1d7ff16cd02cb38f7484a15ccca9",
          "PFT_INPUT_VALIDATION": "2c211941f00b1559d00b2866c922747b20ab4bfeb153746df2bfc494b7ce7fb3",
          "PFT_EVIDENCE_LEDGER": "1e6ec9c5eb532f7392fe07e6ef3c827720713c033dff30f1bbc0eb51cf240459",
          "RECOMMENDED_INPUT_PFT_20_SITES": "33656ea7c58a0441fe32521fbbae48a6cc04925b8b5436b7b3ecad2b2bf5a9be"}
HOST2FATES = {1: 2, 2: 2, 3: 3, 4: 1, 5: 4, 6: 5, 7: 6, 8: 6, 9: 7, 10: 9, 12: 12, 13: 13, 14: 14}
ABBR = {"TropEBT": 4, "ENF": 1, "DNF": 3, "EBT": 5, "HydrodecidTropTree": 6, "DBF": 7, "EvergreenShrub": 9,
        "ColdDecidShrub": 10, "CoolC3": 13, "C4": 14}   # text label -> CLM host index
STATUS = "RECOMMENDED_MODEL_HYPOTHESIS_V1_1_NOT_OBSERVATION"


def vectors(text):
    """'EBT 65 / C4 4 / CoolC3 2 / bare 29' -> bare, host json, FATES natland json, FATES vegetated-only json."""
    host, bare = {}, 0.0
    for part in text.split("/"):
        k, v = part.split(); v = float(v)
        if k == "bare": bare = v
        else: host[ABBR[k]] = host.get(ABBR[k], 0) + v
    if abs(sum(host.values()) + bare - 100) > 1e-9: raise SystemExit(f"{text}: sums to {sum(host.values()) + bare}")
    nat = {HOST2FATES[h]: v for h, v in host.items()}
    veg = {f: round(v / (100 - bare) * 100, 4) for f, v in nat.items()}
    js = lambda d: json.dumps({str(k): float(v) for k, v in d.items()})
    return bare, js(host), js(nat), js(veg)


# ------------------------------------------------------------------ revisions accepted 2 Nov 2026
REV = {
 "AU-ASM": dict(
    recommended_percent="EBT 65 / C4 4 / CoolC3 2 / bare 29", uncertainty="MEDIUM",
    evidence_level="NUMERIC_CROWN_COVER_PLUS_FIELD_POINT_INTERCEPT",
    basis="CROWN_COVER_PLUS_AUSPLOTS_POINT_INTERCEPT_REMAINDER_SPLIT",
    rationale="v1.1 (2 Nov 2026): woody 65 = airborne-lidar canopy cover (pixels >2 m, 5x5 km; Fischer et al. 2024), the lowest "
              "of three crown-cover estimates (74.5 % of land area, Cleverly et al. 2016 AFM 220:151 Sect. 2.1; TERN core plot 70-80 %); "
              "v1 woody 43 came from an LAI ratio. The remaining 35 is split herb 18 % / bare 82 % from TERN AusPlots point-intercept "
              "points without a woody hit (NTABRT0001/0002 next to the tower, 1,010 points, Mar 2012 wet and Jul-Aug 2020 dry; "
              "herb share 7-27 %, mean 18 %). Herb C3:C4 = 35:65, the mean of the four visits (2012 C3 ~68 % of grass, mainly "
              "Thyridolepis mitchelliana; 2020 C4 ~99 %, Paspalidium, Aristida). Mulga stays FATES4 as decided in OzFlux Stage21.",
    residual_policy="Herbs under the mulga canopy cannot be represented with nocomp patches and are omitted; the herb share counts "
                    "only open-ground points, which may under-estimate open-interspace grass.",
    bare_policy="Bare 29 = 0.82 x (100 - 65). AusPlots points with no plant hit are 37-49 % of all points; their substrate is "
                "about 30-50 % bare soil, 25-45 % litter and 24-32 % cryptogam crust. The FATES bare share therefore includes litter and crust.",
    nonvascular_policy="Cryptogam crust (15-20 % of substrate points) is inside the bare share; not a FATES PFT.",
    source_denominator="Crown cover: lidar 65 % of CHM pixels >2 m (preprint); 74.5 % of land area (method not stated); TERN core plot "
                       "70-80 %. AusPlots 1,010-point intercept: woody hit 37-56 %, herb hit 13-31 %, no plant hit 37-49 %.",
    provisional_prior="NO", hold_flag="Woody 65 (lidar) vs 74.5 (Cleverly 2016) kept as sensitivity; herb density in open interspaces assumed "
                                       "equal to crown gaps; FATES4 vs FATES7 per Stage21-22",
    next_evidence="Cleverly et al. 2013 JGR site description; Eamus et al. 2013 AFM cover value (search snippet says 76 %)."),
 "AU-DaS": dict(
    recommended_percent="TropEBT 37.5 / C4 42.5 / bare 20", basis="PUBLISHED_MODEL_COVER_PRECEDENT_NIJZINK_DEFINITION",
    rationale="v1.1 (2 Nov 2026): Nijzink et al. 2022 tree cover is the minimum monthly foliage projective cover, which the paper calls "
              "the evergreen component (p. 533), so all 37.5 is TropEBT. Deciduous and semi-deciduous foliage (Terminalia grandiflora "
              "semi-deciduous co-dominant; Corymbia latifolia dry-season deciduous) is inside the seasonal 42.5 term, represented as C4. "
              "The v1 80:20 split borrowed from Howard Springs is removed.",
    residual_policy="No published deciduous share for Daly River; it is not split out. Structure: basal area 8.3 m2/ha, 330 stems/ha "
                    "(>5 cm DBH), height 16.4 m, dry-season overstorey LAI 0.8 (Bristow et al. 2016 preprint Table 1, from Hutley 2011).",
    bare_policy="Bare 20 = 100 minus peak monthly FPC: ground uncovered at peak green cover (soil, litter, cured grass), a remote-sensing "
                "complement kept as the bare share; no field bare-soil fraction found.",
    provisional_prior="NO", hold_flag="Deciduous tree share unquantified; Hutley 2011 site table not read (paywalled)",
    next_evidence="Hutley et al. 2011 AFM 151:1417 site table; species basal area at Daly River."),
 "AU-How": dict(
    recommended_percent="TropEBT 39.8 / C4 44.3 / bare 15.9", uncertainty="MEDIUM",
    evidence_level="REMOTE_SENSING_COVER_PLUS_PLOT_STRUCTURE", basis="PUBLISHED_MODEL_COVER_PRECEDENT_NIJZINK_DEFINITION",
    rationale="v1.1 (2 Nov 2026): Nijzink et al. 2022 tree cover (39.8) is the minimum monthly FPC, i.e. the evergreen component, so "
              "all of it is TropEBT; the seasonal 44.3 is C4 grass plus deciduous tree foliage. About 15 % of the overstorey is semi-, "
              "brevi- or fully deciduous (Moore et al. 2016 Sect. 4.3, citing Hutley 2011): see sensitivity deciduous_15pct_from_seasonal. "
              "The v1 '~80 % eucalypt basal area' figure is Hutley et al. 2000 Funct. Ecol. 14:183 (snippet); other sources give 60-70 %.",
    residual_policy="Deciduous trees (Erythrophleum chlorostachys, Terminalia ferdinandiana, 50-100 % leaf drop) are inside the seasonal "
                    "term and not split out in the primary.",
    bare_policy="Bare 15.9 = 100 minus peak monthly FPC (uncovered at peak green cover), kept as the bare share. Nijzink pp. 541-542 note "
                "the satellite cell includes seasonal lagoons, so this share is probably an over-estimate.",
    provisional_prior="NO", hold_flag="Existing AU-How case is full FATES competition with the default surface; this FIXNC vector is a separate experiment",
    next_evidence="Hutley et al. 2011 site table; Hutley et al. 2000 full text for the basal-area share."),
 "JP-Yms": dict(
    recommended_percent="DBF 66 / EBT 28 / ENF 6", basis="EXPLICIT_FUNCTIONAL_GROUP_BIOMASS_SHARE",
    rationale="v1.1 (2 Nov 2026): Kominami et al. 2008 AFM 148:723 Sect. 2.1 (full text, citing Goto 2003): 1999 living-tree biomass "
              "(DBH >= 3 cm) is deciduous broadleaf 66 % (Quercus serrata), evergreen broadleaf 28 % (Ilex pedunculosa, which became a "
              "dominant canopy species, Sect. 3.2.2) and coniferous 6 % (Pinus densiflora). Used directly; v1 had put the 6 % into DBF.",
    residual_policy="No residual. Deciduous trees sit mainly on the ridge, evergreens across all slope positions (Sect. 4).",
    provisional_prior="NO", hold_flag="Basal-area alternative ~68/32 deciduous/evergreen (Kominami 2003, snippet only)",
    next_evidence="Goto et al. 2003 species biomass table."),
 "JP-Tef": dict(
    recommended_percent="DNF 50 / CoolC3 50", uncertainty="MEDIUM", evidence_level="NUMERIC_PLANTING_DESIGN_AREA",
    basis="STRIP_GEOMETRY_AREA_SHARE",
    target_state="Post-clearcut state (operator decision 2 Nov 2026): hybrid larch strips plus retained Sasa strips",
    target_period="2004-2023; the 2001-2002 pre-harvest mixed forest is not represented",
    rationale="v1.1 (2 Nov 2026): after the Jan-Mar 2003 clear-cut the Sasa was strip-cut in 4 m rows and ~2500/ha hybrid larch "
              "(Larix gmelinii x kaempferi) were planted in the cut rows in Oct 2003; cut and uncut rows each cover half of the area "
              "(Aguilos et al. 2014 Sect. 3.2; AsiaFlux TSE; Tsunogai et al. 2014 Sect. 2.1). This planting design is an area "
              "measurement: larch rows -> DNF 50, Sasa rows -> CoolC3 50 (Sasa senanensis/kurilensis, evergreen dwarf bamboo).",
    residual_policy="Sasa re-invaded the larch rows after weeding stopped (2007) and covered the gaps between trees by 2008-2010; nocomp "
                    "patches keep the 50/50 area split and drop the Sasa under larch. Natural Betula/Quercus regeneration is unquantified. "
                    "Seasonal-mean PAI: larch 0.9 (2004) -> 1.7 (2013), Sasa 4.3-6.1 (Sun et al. 2020 Table 1).",
    bare_policy="Bare 0 from 2007; the larch rows were weeded in 2004-2006 and were partly bare then (sensitivity weeded_strips_2004_2006).",
    source_composition="Hybrid larch ~2500/ha planted Oct 2003 in 4 m strip-cut rows; Sasa in the alternate uncut rows; natural "
                       "Betula ermanii, B. platyphylla, Quercus crispula. Pre-cut: Q. crispula, Betula, Abies sachalinensis, Picea jezoensis.",
    source_denominator="Planting design: strip-cut and uncut rows each half of the study area; PAI by year (Sun et al. 2020 Table 1).",
    provisional_prior="NO", hold_flag="Sasa is approximated as cool C3 grass; pre-2003 forest years not represented",
    next_evidence="Larch height and canopy closure after 2010; birch share; JapanFlux BADM vegetation file."),
 "JP-Tmd": dict(
    recommended_percent="DBF 30 / CoolC3 60 / ColdDecidShrub 5 / bare 5", uncertainty="HIGH",
    evidence_level="NUMERIC_LAI_BIOMASS_TRAJECTORY_NO_AREA", basis="MULTI_YEAR_TRAJECTORY_COMPROMISE",
    target_state="Windthrown former larch plantation in natural regrowth; compromise between the C3-herb state (2010-2014) and the "
                 "birch state (after ~2015)",
    target_period="2005-2023; evaluate 2005-2014 and 2015-2023 separately",
    rationale="v1.1 (2 Nov 2026): Typhoon Songda (8 Sep 2004) blew down >90 % of the trees; trunks were salvage-logged by summer 2005, "
              "stumps and branches left, no replanting, no larch survived (Sano et al. 2010 Sect. 2.1; Yazaki et al. 2016 Sect. 2.1, "
              "3.1). Understorey: Rubus idaeus ~60 % of biomass and ~50 % of LAI in 2006, >60 % of biomass to 2009; Solidago gigantea "
              "~70 % of understorey biomass in 2011. Birch (B. platyphylla, B. ermanii): overstorey LAI 0.40 (2010) and 0.76 (2014) "
              "against understorey LAI 2.7-3.6; trees 48 % of aboveground biomass in 2014; Betula-dominated by ~2019-2022 "
              "(qualitative). The primary is the mid state shifted toward trees; period scenarios give each state.",
    residual_policy="LAI and biomass shares are used as area proxies; no area or cover fraction exists for any year. All understorey "
                    "species are C3 (Rubus, Solidago, Dryopteris, Pachysandra); no Sasa at this site.",
    bare_policy="Bare 5 is a placeholder for stump pits, coarse woody debris and machine-disturbed soil; the 2006 understorey LAI ~3.8 "
                "implies a nearly closed low canopy.",
    source_composition="Rubus idaeus (deciduous shrub) 2005-2009, Solidago gigantea (C3 forb) 2010-2014, Betula platyphylla and "
                       "B. ermanii saplings rising to dominance; larch 67/ha in 2014.",
    source_denominator="Yazaki et al. 2016 Table 1, Table A1, Sect. 3.1-3.3; Sano et al. 2010 Sect. 3.1; qualitative 2019-2022 statements.",
    provisional_prior="YES",
    hold_flag="Dominant PFT changes twice within the record; nothing quantitative after 2014; a scraped bare-pumice patch ~0.2 km "
              "north may or may not be in the footprint",
    next_evidence="Yazaki 2016 Tables S5-S6; Hirano et al. 2017 AFM 232:457; JapanFlux BADM vegetation files."),
}
SCEN = {   # site -> (rows to drop by scenario name, rows to add/replace)
 "AU-ASM": ({"mixed_C3_C4_herb"}, [
    ("v1_primary_20261102", "EBT 43 / C4 22 / bare 35", "v1 primary: woody from LAI ratio, bare from the gridded CTSM surface; superseded by field cover data."),
    ("mulga_as_shrub_FATES7", "EvergreenShrub 65 / C4 4 / CoolC3 2 / bare 29", "v1.1 split with mulga as evergreen shrub; default FATES7 height cap 4.735 m is below 26 % of 2014 Acacia stems."),
    ("woody_74p5_Cleverly2016", "EBT 74.5 / C4 3 / CoolC3 1.5 / bare 21", "Woody = 74.5 % of land area (Cleverly 2016); remainder split 18:82 as in the primary."),
    ("herb_C4_only", "EBT 65 / C4 6 / bare 29", "Herb share all C4 (2020 dry-season composition).")]),
 "AU-DaS": ({"all_evergreen_tree"}, [
    ("v1_primary_20261102", "TropEBT 30 / HydrodecidTropTree 7.5 / C4 42.5 / bare 20", "v1 primary: 80:20 split of the Nijzink tree cover, inconsistent with its evergreen-component definition.")]),
 "AU-How": (set(), [
    ("v1_primary_20261102", "TropEBT 31.8 / HydrodecidTropTree 8 / C4 44.3 / bare 15.9", "v1 primary: 80:20 split of the Nijzink tree cover, inconsistent with its evergreen-component definition."),
    ("deciduous_15pct_from_seasonal", "TropEBT 39.8 / HydrodecidTropTree 7 / C4 37.3 / bare 15.9", "15 % deciduous overstorey (Moore 2016 citing Hutley 2011) added on top of the evergreen 39.8 and taken out of the seasonal term.")]),
 "JP-Yms": (set(), [
    ("v1_primary_20261102", "DBF 72 / EBT 28", "v1 primary: the 6 % conifer residual was assigned to DBF.")]),
 "JP-Tef": (set(), [
    ("v1_primary_20261102", "DNF 100", "v1 primary: planted larch only, Sasa omitted."),
    ("weeded_strips_2004_2006", "DNF 20 / CoolC3 50 / bare 30", "Early state: larch rows weeded 2004-2006 with larch LAI <= 1.3; the bare share is unmeasured.")]),
 "JP-Tmd": (set(), [
    ("v1_primary_20261102", "DBF 19 / CoolC3 81", "v1 primary: 2014 LAI shares only."),
    ("early_Rubus_2005_2009", "CoolC3 40 / ColdDecidShrub 55 / bare 5", "Rubus idaeus ~50 % of LAI, ~60 % of biomass; grasses ~20 % of LAI (Sano 2010; Yazaki 2016)."),
    ("mid_Solidago_2010_2014", "DBF 15 / CoolC3 70 / ColdDecidShrub 10 / bare 5", "Tree LAI 10-22 % of total; Solidago ~70 % of understorey biomass (Yazaki 2016)."),
    ("late_Betula_2015_2023", "DBF 55 / CoolC3 40 / ColdDecidShrub 5", "'Betula-dominated' after ~2015 (qualitative only, NIES/CGER/ESJ).")]),
}
LEDGER_ADD = [   # site, quantity, value, denominator_or_basis, period, spatial_scope, source, source_url, locator, verification
 ("AU-ASM", "woody canopy cover (lidar)", "65 %", "CHM pixels >2 m over 5x5 km", "survey year in source", "5x5 km", "Fischer et al. 2024 bioRxiv (preprint)", "https://www.biorxiv.org/content/10.1101/2024.03.27.586702", "Table 1", "REVIEW_FULLTEXT"),
 ("AU-ASM", "Acacia cover", "74.5 % of the land area", "land area; method not stated", "", "site", "Cleverly et al. 2016 AFM 220:151", "https://papers.agrivy.com/webfiles/papers/2016-AFM-JAMES-CLEVERLY.pdf", "Sect. 2.1", "REVIEW_FULLTEXT"),
 ("AU-ASM", "core plot cover", "dense mulga woodland, cover 70-80 %", "TERN text", "", "core 1 ha", "TERN SuperSite text (reproduced by Australian Acoustic Observatory)", "https://acousticobservatory.org/sites/alice-mulga-tern-supersite-54/", "site text", "REVIEW_SECONDHAND"),
 ("AU-ASM", "point-intercept cover", "woody hit 40.2/37.1 (0001) 55.7/45.0 (0002); herb hit 18.1/28.7, 12.9/30.6; no plant hit 47.0/49.1, 37.3/40.3 % (2012/2020)", "1,010 points per visit", "Mar 2012 (wet), Jul-Aug 2020 (dry)", "NTABRT0001 and NTABRT0002, 100-240 m from tower", "TERN AusPlots point-intercept (computed from raw hits)", "http://swarmapi.ausplots.aekos.org.au/veg_pi?site_location_name=in.(NTABRT0001,NTABRT0002,NTABRT0003)", "veg_pi records", "REVIEW_FULLTEXT+DERIVED"),
 ("AU-ASM", "herb share of points without woody hit", "15.6, 21.9 (0001); 7.2, 26.9 (0002) %; mean ~18 %", "points with no woody hit", "2012, 2020", "NTABRT0001/0002", "TERN AusPlots point-intercept", "http://swarmapi.ausplots.aekos.org.au/veg_pi?site_location_name=in.(NTABRT0001,NTABRT0002,NTABRT0003)", "veg_pi records", "REVIEW_FULLTEXT+DERIVED"),
 ("AU-ASM", "grass photosynthetic pathway", "2012: C3 ~68 % of identified grass (Thyridolepis mitchelliana, Monachather); 2020: C4 ~99 % (Paspalidium rarum, Aristida holathera)", "live grass point hits, genus-based pathway", "2012, 2020", "NTABRT0001/0002", "TERN AusPlots point-intercept; Khoshravesh et al. 2020 Plant Physiol 182:566 (Thyridolepis C3)", "https://academic.oup.com/plphys/article/182/1/566/6116299", "veg_pi; Results", "REVIEW_FULLTEXT+DERIVED"),
 ("AU-DaS", "tree cover definition", "tree cover = minimum monthly FPC = 'the evergreen component of cover'", "FPC = fPAR/0.95", "1980-2017", "site grid cell", "Nijzink et al. 2022 HESS 26:525", "https://hess.copernicus.org/articles/26/525/2022/", "Table 1, p. 530, p. 533", "REVIEW_FULLTEXT"),
 ("AU-DaS", "structure", "BA 8.3 m2/ha, 330 stems/ha (>5 cm), height 16.4 m, dry-season LAI 0.8", "plot", "", "site", "Bristow et al. 2016 BGD preprint (from Hutley 2011)", "https://bg.copernicus.org/preprints/bg-2016-191/bg-2016-191.pdf", "Table 1", "REVIEW_SECONDHAND"),
 ("AU-DaS", "leaf phenology", "Terminalia grandiflora semi-deciduous; Corymbia latifolia dry-season deciduous", "species flora", "", "species", "FloraBase; EUCLID", "https://florabase.dbca.wa.gov.au/browse/profile/5305", "profile pages", "REVIEW_FULLTEXT"),
 ("AU-How", "deciduous overstorey share", "~15 % of the overstorey semi-, brevi- or fully deciduous", "overstorey (metric not stated)", "", "site", "Moore et al. 2016 BG 13:2387 (citing Hutley 2011)", "https://bg.copernicus.org/articles/13/2387/2016/", "Sect. 4.3, p. 2398", "REVIEW_SECONDHAND"),
 ("AU-How", "eucalypt basal-area share", "c. 80 % (Hutley 2000); 60-70 % (Schymanski 2008 citing O'Grady 2000)", "tree basal area", "", "site", "Hutley et al. 2000 Funct. Ecol. 14:183; Schymanski et al. 2008 HESSD 5:51", "", "Hutley 2000 snippet; Schymanski p. 71", "REVIEW_SNIPPET"),
 ("AU-How", "satellite cover bias", "seasonal lagoons in the grid cell bias FPC low", "", "", "grid cell", "Nijzink et al. 2022 HESS 26:525", "https://hess.copernicus.org/articles/26/525/2022/", "pp. 541-542", "REVIEW_FULLTEXT"),
 ("AU-Dry", "structure", "BA 5.4 m2/ha, height 12.3 m, LAI 0.58", "plot", "", "site", "Whitley et al. 2016 BG 13:3245 (from Hutley 2011)", "https://bg.copernicus.org/articles/13/3245/2016/", "Table 1", "REVIEW_SECONDHAND"),
 ("AU-Stp", "Astrebla pathway", "Astrebla lappacea C4 NAD-ME", "species", "", "species", "Pinto et al. 2014 J. Exp. Bot.", "https://pmc.ncbi.nlm.nih.gov/articles/PMC4085965/", "Table 2", "REVIEW_FULLTEXT"),
 ("AU-Cpr", "grass species", "Triodia scariosa the only grass in the core 1 ha plot; Austrostipa only in plot SASMDD0005", "species list", "2013", "core 1 ha", "TERN Calperum species list", "https://portal.tern.org.au/metadata/TERN/170a547c-690c-4f7c-8794-35395a9f65c6", "dataset", "REVIEW_FULLTEXT"),
 ("AU-Cpr", "canopy cover (lidar)", "43 %", "CHM pixels >2 m", "", "Chowilla area", "Fischer et al. 2024 bioRxiv (preprint)", "https://www.biorxiv.org/content/10.1101/2024.03.27.586702", "Table 1", "REVIEW_FULLTEXT"),
 ("AU-Gin", "structure", "BA 11.6 m2/ha, height 6.8 m, LAI 1.3; in-situ LAI 0.8 (7 Sep 2020)", "plot", "", "site", "Stephens et al. 2025 GCB; Pisek et al. 2025 Front. Remote Sens.", "https://pmc.ncbi.nlm.nih.gov/articles/PMC12291013/", "Table 1", "REVIEW_FULLTEXT"),
 ("AU-Tum", "understorey LAI", "understorey LAI 1.5 vs tree LAI 1.4", "LAI", "pre-2019", "site", "van Gorsel et al., AMS 9A.4", "https://ams.confex.com/ams/pdfpapers/139191.pdf", "Sect. 2", "REVIEW_FULLTEXT"),
 ("AU-Cow", "palm share", "palms 121 of 625 stems (19.4 %), 3.3 of 34.1 m2/ha (9.7 %)", "1 ha, stems >=10 cm", "2012", "1 ha core", "TERN Cow Bay census (recomputed)", "https://portal.tern.org.au/metadata/TERN/ad4c0487-b6c0-463c-bbf9-4dc0c52b28ef", "CSV", "REVIEW_FULLTEXT+DERIVED"),
 ("JP-Yms", "functional-group biomass", "deciduous broadleaf 66 %, evergreen broadleaf 28 %, coniferous 6 %", "living-tree biomass DBH >=3 cm", "1999", "1.7 ha catchment", "Kominami et al. 2008 AFM 148:723 (citing Goto 2003)", "https://ftp.forest.sr.unh.edu/mcday/Biometric_Eddy-covariance/papers/", "Sect. 2.1, 3.2.2", "REVIEW_FULLTEXT"),
 ("JP-Fhk", "larch basal area", "30.3 of 35.8 m2/ha; 369 of ~423 stems/ha", "overstory trees", "2010", "stand", "Takahashi et al. 2015 J. Agric. Meteorol. 71:302", "https://www.jstage.jst.go.jp/article/agrmet/71/4/71_D-14-00009/_pdf", "Sect. 2.1", "REVIEW_FULLTEXT"),
 ("JP-Spp", "typhoon loss", "33 % of canopy and 28 % of tree biomass removed; Sasa LAI 4.05 by 2007", "canopy / biomass / LAI", "2004-2007", "stand", "Yamanoi et al. 2015 BG 12:6837", "https://bg.copernicus.org/articles/12/6837/2015/", "Sect. 2.1, Table 1", "REVIEW_FULLTEXT"),
 ("JP-Tak", "Sasa share of LAI", "tree LAI ~5.5, Sasa ~1.7 (Sasa ~24 % of total)", "LAI", "Jun-Sep", "site", "AsiaFlux TKY page", "https://asiaflux.nies.go.jp/site-info/TKY.html", "site page", "REVIEW_FULLTEXT+DERIVED"),
 ("JP-Api", "understorey", "no understory vegetation", "qualitative", "", "site", "Koarashi et al. 2025 Frontiers", "", "Sect. 2.1", "REVIEW_FULLTEXT"),
 ("JP-Tef", "strip geometry", "strip-cut and uncut Sasa rows each half of the study area; Sasa crushed in cut rows Oct 2003, weeded 2004-2006, re-invaded from 2007", "area", "2003-2010", "study area", "Aguilos et al. 2014 AFM 197:26 (author manuscript); Tsunogai et al. 2014 BG 11:5411", "https://eprints.lib.hokudai.ac.jp/repo/huscap/all/57455/Aguilos_AFM2014_HUSCUP.pdf", "Sect. 2.1, 3.2; Tsunogai Sect. 2.1", "REVIEW_FULLTEXT"),
 ("JP-Tef", "plant area index by year", "larch 0.9/1.3/1.4/1.6/1.4/1.3/1.7/1.6, Sasa 4.3/5.1/5.6/6.1/5.3/5.5/5.9/5.4 (2004-2009, 2013, 2014)", "seasonal-mean PAI", "2004-2014", "site", "Sun et al. 2020 J. Agric. Meteorol. 76:119", "https://www.jstage.jst.go.jp/article/agrmet/76/3/76_D-19-00026/_pdf", "Table 1", "REVIEW_FULLTEXT"),
 ("JP-Tef", "carbon recovery", "larch 1.04 MgC/ha (2009) vs Sasa gain 16.3 MgC/ha (2003-09); post-harvest CO2 recaptured by 2020", "biomass / NEE", "2003-2020", "site", "Aguilos et al. 2014; Takagi et al. 2022 EJFR 22:49", "https://eprints.lib.hokudai.ac.jp/repo/huscap/all/84962/", "Sect. 3.2; abstract", "REVIEW_FULLTEXT"),
 ("JP-Tmd", "windthrow and salvage", ">90 % of trees blown down 8 Sep 2004; trunks removed by summer 2005; stumps, branches, 11 MgC/ha CWD left; no replanting", "stand", "2004-2005", "site", "Sano et al. 2010 FEM 260:2214 (author manuscript); Yazaki et al. 2016 Forests 7:287", "https://eprints.lib.hokudai.ac.jp/dspace/bitstream/2115/45748/12/hirano2.pdf", "Sano Sect. 2.1, 4.2; Yazaki Sect. 2.1", "REVIEW_FULLTEXT"),
 ("JP-Tmd", "early understorey", "2006: AGB 2.69 Mg/ha, LAI 3.85; Rubus idaeus ~60 % of AGB, ~50 % of LAI; grasses ~20 % of LAI", "AGB / LAI", "2006-2009", "1.4 ha plot", "Sano et al. 2010; Yazaki et al. 2016", "https://eprints.lib.hokudai.ac.jp/repo/huscap/all/64380/Forests7-11_287.pdf", "Sano Sect. 3.1; Yazaki Sect. 3.1, 3.3", "REVIEW_FULLTEXT"),
 ("JP-Tmd", "tree regrowth", "2010: 3190 trees/ha >0.5 m, height 1.49 m, LAI 0.40; 2014: 4380/ha, height 2.02 m, BA 1.12 m2/ha, LAI 0.76, trees 48 % of AGB; Solidago ~70 % of understorey biomass 2011", "trees >0.5 m; AGB; LAI", "2010-2014", "1.4 ha plot", "Yazaki et al. 2016 Forests 7:287", "https://eprints.lib.hokudai.ac.jp/repo/huscap/all/64380/Forests7-11_287.pdf", "Table 1, Table A1, Sect. 3.1-3.3, 4.1", "REVIEW_FULLTEXT"),
 ("JP-Tmd", "later state", "Betula growth 'remarkable' 15 yr after the typhoon (30 m tower built 2019); vegetation 'Betula-dominated' ~2022", "qualitative", "2017-2022", "site", "CGER News Jul 2023; NIES SR-132; ESJ69 S21-3", "https://cger.nies.go.jp/cgernews/202307/392004.html", "article text", "REVIEW_FULLTEXT"),
 ("JP-Tmd", "dataset land cover", "windthrow period (<=10 yr after disturbance) GRA, afterwards DBF; Tmk and Tmd a continuous series", "dataset label", "2001-2023", "site", "Ueyama et al. 2025 ESSD 17:3807", "https://essd.copernicus.org/articles/17/3807/2025/", "Table 1, Table 3", "REVIEW_FULLTEXT"),
 ("JP-Tgf", "C3/C4 seasonality and mowing", "C4 biomass peak Aug-Nov 680-886 g/m2; mowing twice a year since 2006", "biomass", "2001-2003; 2006-", "field", "Shimoda et al. 2005 SOLA 1:169; Ma et al. 2018 ESSD", "https://doi.org/10.2151/sola.2005-044", "Table 3; Sect. 2.1", "REVIEW_FULLTEXT"),
]
MD_ROWS = {   # summary-table rows of the v1 Markdown that change
 "AU-ASM": "| OzFlux | AU-ASM | EBT 65 / C4 4 / CoolC3 2 / bare 29 | CROWN_COVER_PLUS_AUSPLOTS_POINT_INTERCEPT_REMAINDER_SPLIT | 中 | 否 | 有 |",
 "AU-DaS": "| OzFlux | AU-DaS | TropEBT 37.5 / C4 42.5 / bare 20 | PUBLISHED_MODEL_COVER_PRECEDENT_NIJZINK_DEFINITION | 高 | 否 | 有 |",
 "AU-How": "| OzFlux | AU-How | TropEBT 39.8 / C4 44.3 / bare 15.9 | PUBLISHED_MODEL_COVER_PRECEDENT_NIJZINK_DEFINITION | 中 | 否 | 有 |",
 "JP-Yms": "| JapanFlux | JP-Yms | DBF 66 / EBT 28 / ENF 6 | EXPLICIT_FUNCTIONAL_GROUP_BIOMASS_SHARE | 中 | 否 | 有 |",
 "JP-Tef": "| JapanFlux | JP-Tef | DNF 50 / CoolC3 50 | STRIP_GEOMETRY_AREA_SHARE | 中 | 否 | 有 |",
 "JP-Tmd": "| JapanFlux | JP-Tmd | DBF 30 / CoolC3 60 / ColdDecidShrub 5 / bare 5 | MULTI_YEAR_TRAJECTORY_COMPROMISE | 高 | 是 | 有 |",
}
MD_POINT3 = ("3. **常绿/落叶树的拆分是区域先验。** AU-DaS 与 AU-Dry 借用 Howard Springs 的断面积比 80:20；DaS 按株数则偏落叶，已作为替代方案给出。",
             "3. **（v1.1 更正）Nijzink 2022 的树覆盖度是月最小投影覆盖，原文称其为常绿部分**，所以 AU-How 与 AU-DaS 不再按 80:20 拆分，"
             "落叶树叶片落在季节性的“草”项里。AU-Dry 的主推荐本来就没有拆分，80:20 只出现在它的替代方案中。")
MD_BANNER = ("> **v1.1 修订（2026-11-02，操作者已接受文献复核）：** 下表已更新为 v1.1 主推荐。逐站最终说明、依据与不确定性以同目录 "
             "[README.md](README.md) 为准；下方“每站决策与证据”中 {sites} 的段落描述的是 v1，替换前的 v1 主推荐保留在敏感性表的 "
             "`v1_primary_20261102` 行。裸地一律保留为独立比例（与 AmeriFlux 50 站、ICOS 38 站一致）。\n\n")


def read_csv(p):
    raw = p.read_bytes(); nl = "\r\n" if b"\r\n" in raw else "\n"
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    return rows, list(rows[0].keys()), nl, raw.startswith(b"\xef\xbb\xbf")


def write_csv(p, rows, fields, nl, bom):
    buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=fields, lineterminator=nl); w.writeheader(); w.writerows(rows)
    p.write_bytes((b"\xef\xbb\xbf" if bom else b"") + buf.getvalue().encode("utf-8"))


def num(v): return "0" if v == 0 else (str(float(v)) if float(v) == round(v, 1) else str(round(v, 4)))


def main():
    for k, p in F.items():
        if hashlib.sha256(p.read_bytes()).hexdigest() != V1_SHA[k]: raise SystemExit(f"{p.name} is not the v1 file; refusing")
    master, mf, mnl, mbom = read_csv(F["RECOMMENDED_CLM_FATES_INPUT_PFT"])
    for r in master:
        if r["site"] not in REV: continue
        rev = dict(REV[r["site"]]); bare, h, n, v = vectors(rev["recommended_percent"])
        rev.update(bare_percent=str(bare), clm_pct_nat_pft_json=h, fates_natland_percent_json=n,
                   fates_vegetated_only_percent_json=v, status=STATUS)
        unknown = set(rev) - set(mf)
        if unknown: raise SystemExit(f"unknown columns {unknown}")
        r.update(rev)
    write_csv(F["RECOMMENDED_CLM_FATES_INPUT_PFT"], master, mf, mnl, mbom)
    by = {r["site"]: r for r in master}

    pct, pf, pnl, pbom = read_csv(F["RECOMMENDED_CLM_PCT_NAT_PFT"])
    for r in pct:
        if r["site"] not in REV: continue
        h = {int(k): x for k, x in json.loads(by[r["site"]]["clm_pct_nat_pft_json"]).items()}
        for i in range(15): r[f"PCT_NAT_PFT_{i}"] = str(float(by[r["site"]]["bare_percent"] if i == 0 else h.get(i, 0.0)))
    write_csv(F["RECOMMENDED_CLM_PCT_NAT_PFT"], pct, pf, pnl, pbom)

    fat, ff, fnl, fbom = read_csv(F["RECOMMENDED_FATES_PFT_PERCENT"])
    for r in fat:
        if r["site"] not in REV: continue
        m = by[r["site"]]; n = json.loads(m["fates_natland_percent_json"]); v = json.loads(m["fates_vegetated_only_percent_json"])
        r["bare_pct_natland"] = str(float(m["bare_percent"]))
        for i in range(1, 15):
            r[f"FATES_PFT_{i:02d}_pct_natland"] = num(n.get(str(i), 0)); r[f"FATES_PFT_{i:02d}_pct_vegetated_only"] = num(v.get(str(i), 0))
    write_csv(F["RECOMMENDED_FATES_PFT_PERCENT"], fat, ff, fnl, fbom)

    sen, sf, snl, sbom = read_csv(F["PFT_INPUT_SENSITIVITY_SCENARIOS"])
    out = []
    for site in [r["site"] for r in master]:
        drop, add = SCEN.get(site, (set(), []))
        names = {a[0] for a in add}
        rows = [r for r in sen if r["site"] == site and r["scenario"] not in drop and r["scenario"] not in names]
        kept = {r["scenario"]: r for r in sen if r["site"] == site and r["scenario"] in names}
        for name, text, interp in add:
            bare, h, n, v = vectors(text)
            base = kept.get(name, {"mapping_profile": "DEFAULT14"})
            rows.append({"site": site, "scenario": name, "recommended_percent": text, "bare_percent": str(bare),
                         "mapping_profile": base.get("mapping_profile", "DEFAULT14"), "fates_natland_percent_json": n,
                         "clm_pct_nat_pft_json": h, "fates_vegetated_only_percent_json": v, "interpretation": interp})
        out += rows
    write_csv(F["PFT_INPUT_SENSITIVITY_SCENARIOS"], out, sf, snl, sbom)

    val, vf, vnl, vbom = read_csv(F["PFT_INPUT_VALIDATION"])
    rows = []
    for m in master:
        for scen, h, bare in [("PRIMARY", m["clm_pct_nat_pft_json"], m["bare_percent"])] + \
                [(s["scenario"], s["clm_pct_nat_pft_json"], s["bare_percent"]) for s in out if s["site"] == m["site"]]:
            hv = {int(k): x for k, x in json.loads(h).items()}
            ok = all(k in HOST2FATES for k in hv) and abs(sum(hv.values()) + float(bare) - 100) < 1e-9 and len(hv) <= 4
            rows.append({"site": m["site"], "scenario": scen, "natural_area_sum": f"{sum(hv.values()) + float(bare):.4f}",
                         "live_type_count": str(len(hv)), "round_trip": "PASS" if ok else "FAIL", "mapping_profile": m["mapping_profile"]})
    write_csv(F["PFT_INPUT_VALIDATION"], rows, vf, vnl, vbom)

    led, lf, lnl, lbom = read_csv(F["PFT_EVIDENCE_LEDGER"])
    net = {m["site"]: m["network"] for m in master}
    for t in LEDGER_ADD:
        led.append(dict(zip(lf, (t[0], net[t[0]]) + t[1:])))
    write_csv(F["PFT_EVIDENCE_LEDGER"], led, lf, lnl, lbom)

    md = F["RECOMMENDED_INPUT_PFT_20_SITES"]; text = md.read_text(encoding="utf-8")
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        for site, row in MD_ROWS.items():
            if ln.startswith(f"| OzFlux | {site} |") or ln.startswith(f"| JapanFlux | {site} |"): lines[i] = row
        for site in REV:
            if ln.startswith(f"### {site} — "): lines[i] = ln + "（v1；v1.1 见 README）"
    if not lines[0].endswith("百分比 v1"): raise SystemExit("v1 Markdown title changed")
    lines[0] += ".1（2026-11-02 文献复核修订）"
    text = "\n".join(lines)
    if MD_POINT3[0] not in text: raise SystemExit("v1 Markdown point 3 not found")
    text = text.replace(*MD_POINT3)
    head, sep, rest = text.partition("\n## 文件")
    if not sep: raise SystemExit("v1 Markdown '## 文件' heading not found")
    text = head.rstrip("\n") + "\n\n" + MD_BANNER.format(sites="、".join(REV)) + sep.lstrip("\n") + rest
    md.write_text(text, encoding="utf-8")
    print("APPLIED v1.1 to", ", ".join(REV), "| scenarios", len(out), "| ledger rows", len(led), "| validation rows", len(rows))


if __name__ == "__main__":
    main()

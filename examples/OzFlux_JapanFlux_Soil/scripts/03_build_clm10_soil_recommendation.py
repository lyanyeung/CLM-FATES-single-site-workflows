#!/usr/bin/env python3
"""Stage03: build the recommended 10-layer CLM soil texture for the 20 OzFlux / JapanFlux sites from the evidence files.

Inputs (all in ../data unless given):
  literature_soil_evidence_20261103.csv   tower evidence; rows with use_numeric=YES are used (sand/silt/clay by depth)
  manual_depth_assignments_20261103.csv   evidence rows whose application depth is set by hand, each with a reason
  site_soil_decisions_20261103.csv        per site: source priority and notes
  gridded_soil_at_towers_long.csv         Stage01 output (SoilGrids, and SLGA when a TERN key was available)
  current_surface_soil_layers.tsv         optional, Stage02 output (IRIDIS6): the soil now in each surface file

Particle-size schemes. CLM's pedotransfer functions expect USDA sand (50-2000 um). ISSS / Australian / Japanese data
(silt 2-20 um, sand 20-2000 um) are converted before use; clay (< 2 um) is the same in both:
  - fine sand (20-200 um) reported: log-linear interpolation of the cumulative curve inside 20-200 um,
    USDA silt = ISSS silt + fine sand * ln(50/20) / ln(200/20)                                  [LOGLINEAR_20_200]
  - only total sand reported: Minasny & McBratney (2001, Aust. J. Soil Res. 39:1443, 1620 Australian samples,
    R2 0.823; coefficients as reproduced in Hengl, Predictive Soil Mapping with R, sect. 3.4.2):
    USDA silt = -18.3914 + 2.0971 S + 0.6726 Sa - 0.0142 S^2 - 0.0049 Sa^2, or 0.8289 S + 0.0198 Sa if that is < 0,
    with S = ISSS silt and Sa = ISSS sand, kept within [S, S + Sa]                               [MM2001]
  USDA sand = 100 - clay - USDA silt.

Layers. The 10 CLM surface-dataset layers have node depths 0.007 ... 2.86 m. Layer by layer, the first source in the
site's priority that covers the node depth is used; below the deepest covered depth the profile that supplied the
layer above is extended (functions copied from Ameriflux_Soil/scripts/01_collect_soil_texture_evidence.py, so the two
products follow the same rule). The 0-30 cm value is the mean of layers 1-5.

ORGANIC (kg m-3 organic matter) candidates are reported, not applied: SOC (g kg-1) x bulk density (g cm-3) x 1.724.

Usage:  python3 -B 03_build_clm10_soil_recommendation.py --self-test
        python3 -B 03_build_clm10_soil_recommendation.py --gridded G.csv [--current-surface S.tsv] --out-dir ..
"""
from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
DATE = "20261103"
NODES_M = [0.025 * (math.exp(0.5 * (j - 0.5)) - 1.0) for j in range(1, 11)]   # CLM nlevsoifl=10
NODES_CM = [100.0 * z for z in NODES_M]
DEFAULT_PRIORITY = ("LIT", "SLGA", "SOILGRIDS")
DEEP_FILL = ("SLGA", "SOILGRIDS", "LIT", "LITN")
TIER = {"LIT": "T1 site measured", "LITN": "T1N neighbour measured", "SLGA": "T2 SLGA 90 m",
        "SOILGRIDS": "T3 SoilGrids 250 m", "SURFACE": "T4 keep surface"}
OM_PER_C = 1.724


def num(x):
    try:
        v = float(str(x).strip())
        return v if math.isfinite(v) and v > -9990 else None
    except (TypeError, ValueError):
        return None


def usda_class(sand, clay):
    if sand is None or clay is None:
        return ""
    silt = 100.0 - sand - clay
    if silt + 1.5 * clay < 15: return "sand"
    if silt + 2 * clay < 30: return "loamy sand"
    if (7 <= clay < 20 and sand > 52) or (clay < 7 and silt < 50): return "sandy loam"
    if 7 <= clay < 27 and 28 <= silt < 50 and sand <= 52: return "loam"
    if silt >= 80 and clay < 12: return "silt"
    if silt >= 50 and clay < 27: return "silt loam"
    if 20 <= clay < 35 and silt < 28 and sand > 45: return "sandy clay loam"
    if 27 <= clay < 40 and 20 < sand <= 45: return "clay loam"
    if 27 <= clay < 40 and sand <= 20: return "silty clay loam"
    if clay >= 35 and sand > 45: return "sandy clay"
    if clay >= 40 and silt >= 40: return "silty clay"
    return "clay"


def isss_to_usda(clay, silt, sand, fine_sand=None):
    """ISSS clay / silt (2-20) / sand (20-2000) [+ fine sand 20-200] -> USDA (sand, clay, method)."""
    tot = clay + silt + sand
    if tot <= 0:
        raise ValueError("empty particle-size record")
    clay, silt, sand = (100.0 * v / tot for v in (clay, silt, sand))
    if fine_sand is not None:
        fine_sand = 100.0 * fine_sand / tot
        if not 0 <= fine_sand <= sand + 1e-6:
            raise ValueError(f"fine sand {fine_sand} outside 0..{sand}")
        usilt = silt + fine_sand * math.log(50 / 20) / math.log(200 / 20)
        how = "LOGLINEAR_20_200"
    else:
        usilt = -18.3914 + 2.0971 * silt + 0.6726 * sand - 0.0142 * silt ** 2 - 0.0049 * sand ** 2
        if usilt < 0:
            usilt = 0.8289 * silt + 0.0198 * sand
        usilt = min(max(usilt, silt), silt + sand)
        how = "MM2001"
    return 100.0 - clay - usilt, clay, how


# ---------------------------------------------------------------- copied from Ameriflux_Soil Stage01
def interval_profile(rows, label):
    """rows: dicts top, bot, sand, clay (+silt, om_kgm3). Returns sorted intervals."""
    out = []
    for r in rows:
        if r.get("sand") is None or r.get("clay") is None:
            continue
        s, c = float(r["sand"]), float(r["clay"])
        if s + c > 100.0 + 1e-6:
            f = 100.0 / (s + c); s, c = s * f, c * f
        out.append({"top": float(r["top"]), "bot": float(r["bot"]), "sand": s, "clay": c,
                    "om_kgm3": r.get("om_kgm3"), "label": label, "note": r.get("note", "")})
    return sorted(out, key=lambda r: (r["top"], r["bot"]))


def value_at(profile, depth_cm):
    for r in profile:
        if r["top"] <= depth_cm < r["bot"]:
            return r
    return None


def recommend(profiles, priority):
    """profiles: {source: [intervals]} -> list of 10 layer dicts. Unlike the Ameriflux_Soil copy, SURFACE may also
    appear inside the priority (a per-site decision to keep the current surface ahead of a gridded source)."""
    layers = []
    for j, z in enumerate(NODES_CM, start=1):
        pick, how = None, ""
        for src in priority:
            if src == "SURFACE":
                if profiles.get("SURFACE"):
                    pick, how = ("SURFACE", profiles["SURFACE"][j - 1]), "KEEP_SURFACE"
                    break
                continue
            r = value_at(profiles.get(src, []), z)
            if r:
                pick, how = (src, r), "COVERED"
                break
        if pick is None:
            prev = layers[-1]["source"] if layers else None
            for src in ((prev,) if prev in DEEP_FILL else ()) + DEEP_FILL:
                prof = [r for r in profiles.get(src, []) if r.get("bot") is not None]
                if prof:
                    deepest = max(prof, key=lambda r: r["bot"])
                    if z >= deepest["bot"]:
                        pick, how = (src, deepest), f"EXTENDED_BELOW_{deepest['bot']:g}cm"
                        break
        if pick is None and profiles.get("SURFACE"):
            r = profiles["SURFACE"][j - 1]
            pick, how = ("SURFACE", r), "KEEP_SURFACE"
        if pick is None:
            layers.append({"layer": j, "node_m": round(NODES_M[j - 1], 4), "PCT_SAND": None, "PCT_CLAY": None,
                           "source": "NONE", "how": "NO_DATA", "usda_class": ""})
            continue
        src, r = pick
        layers.append({"layer": j, "node_m": round(NODES_M[j - 1], 4), "PCT_SAND": round(r["sand"], 2),
                       "PCT_CLAY": round(r["clay"], 2), "source": src, "how": how,
                       "usda_class": usda_class(r["sand"], r["clay"]),
                       "ORGANIC_candidate_kgm3": None if r.get("om_kgm3") is None else round(r["om_kgm3"], 1),
                       "note": r.get("note", "")})
    return layers


def top_mean(layers, key):
    v = [l[key] for l in layers[:5] if l.get(key) is not None]
    return round(sum(v) / len(v), 1) if v else None


# ---------------------------------------------------------------- evidence readers
def read_csv(p, delim=","):
    p = Path(p)
    return list(csv.DictReader(p.open(encoding="utf-8-sig"), delimiter=delim)) if p.is_file() else []


def lit_profiles(lit_rows, manual):
    """{site: {"LIT": [intervals], "LITN": [...]}} from use_numeric=YES rows, converted to USDA."""
    out, conv = {}, []
    for r in lit_rows:
        if r.get("use_numeric", "").strip().upper() != "YES":
            continue
        site, eid = r["site"], r.get("evidence_id", "")
        top, bot = num(r["depth_top_cm"]), num(r["depth_bottom_cm"])
        m = manual.get((site, eid))
        if m:
            top, bot = num(m["applied_top_cm"]), num(m["applied_bottom_cm"])
        if top is None or bot is None or bot <= top:
            raise ValueError(f"{site} {eid}: no usable depth (set one in manual_depth_assignments)")
        sand, silt, clay = num(r["sand_pct"]), num(r["silt_pct"]), num(r["clay_pct"])
        if clay is None or (sand is None and silt is None):
            raise ValueError(f"{site} {eid}: numeric row without clay and sand/silt")
        if sand is None:
            sand = 100.0 - clay - silt
        if silt is None:
            silt = 100.0 - clay - sand
        scheme = r.get("size_scheme", "").strip().upper()
        if scheme.startswith("ISSS"):
            us, uc, how = isss_to_usda(clay, silt, sand, num(r.get("fine_sand_20_200_pct")))
        elif scheme.startswith("USDA") or scheme.startswith("UNSTATED"):
            # UNSTATED: used as reported (an explicit curation decision); the ISSS reading is kept as a sensitivity
            tot = sand + silt + clay
            us, uc = 100.0 * sand / tot, 100.0 * clay / tot
            how = "USDA_AS_REPORTED" if scheme.startswith("USDA") else "UNSTATED_AS_REPORTED"
        else:
            raise ValueError(f"{site} {eid}: size_scheme must be USDA, ISSS or UNSTATED (is '{scheme}')")
        alt = round(isss_to_usda(clay, silt, sand, num(r.get("fine_sand_20_200_pct")))[0], 2) \
            if how == "UNSTATED_AS_REPORTED" else None
        bd, oc = num(r.get("bulk_density_g_cm3")), num(r.get("organic_carbon_pct"))
        om = round(oc * 10.0 * bd * OM_PER_C, 1) if bd is not None and oc is not None else None
        label = "LITN" if r.get("tower_specific", "").strip().upper().startswith("NEAR") else "LIT"
        out.setdefault(site, {}).setdefault(label, []).append(
            {"top": top, "bot": bot, "sand": us, "clay": uc, "om_kgm3": om, "note": f"{eid} {how}"})
        conv.append({"site": site, "evidence_id": eid, "depth_top_cm": top, "depth_bottom_cm": bot,
                     "scheme": scheme, "reported_sand": sand, "reported_silt": silt, "reported_clay": clay,
                     "usda_sand": round(us, 2), "usda_clay": round(uc, 2), "conversion": how,
                     "usda_sand_if_ISSS": alt, "manual_depth": "YES" if m else "", "citation": r.get("citation", "")})
    for site in out:
        for k in out[site]:
            out[site][k] = interval_profile(out[site][k], k)
            check_overlaps(site, out[site][k])
    return out, conv


def check_overlaps(site, prof):
    for a, b in zip(prof, prof[1:]):
        if b["top"] < a["bot"] - 1e-6:
            raise ValueError(f"{site}: overlapping evidence intervals {a['top']}-{a['bot']} and {b['top']}-{b['bot']}"
                             " (keep one, or set depths in manual_depth_assignments)")


def gridded_profiles(rows):
    """{site: {"SOILGRIDS": [...], "SLGA": [...]}} from Stage01 long CSV (mean / EV only)."""
    acc = {}
    for r in rows:
        if r["status"] != "OK" or r["statistic"] not in ("mean", "EV"):
            continue
        key = (r["site"], r["source"], int(float(r["depth_top_cm"])), int(float(r["depth_bottom_cm"])))
        acc.setdefault(key, {})[r["property"]] = num(r["value"])
    out = {}
    for (site, src, top, bot), v in sorted(acc.items()):
        if src == "SOILGRIDS":
            if None in (v.get("sand"), v.get("clay")):
                continue
            tot = v["sand"] + v["clay"] + (v.get("silt") or 0.0)
            sand, clay = (100.0 * v["sand"] / tot, 100.0 * v["clay"] / tot) if tot > 0 else (None, None)
            om = (round(v["soc"] * v["bdod"] * OM_PER_C, 1) if v.get("soc") is not None and v.get("bdod") is not None
                  else None)
            note = "SoilGrids mean, USDA"
        else:
            if None in (v.get("clay"), v.get("sand_ISSS_20um"), v.get("silt_ISSS_2_20um")):
                continue
            sand, clay, how = isss_to_usda(v["clay"], v["silt_ISSS_2_20um"], v["sand_ISSS_20um"])
            om, note = None, f"SLGA EV, {how}"
        out.setdefault(site, {}).setdefault(src, []).append(
            {"top": top, "bot": bot, "sand": sand, "clay": clay, "om_kgm3": om, "note": note})
    for site in out:
        for k in out[site]:
            out[site][k] = interval_profile(out[site][k], k)
    return out


def surface_profiles(rows):
    """{site: [(found_by, path, [10 layer dicts])]} from Stage02 current_surface_soil_layers.tsv."""
    by = {}
    for r in rows:
        by.setdefault((r["site"], r["found_by"], r["path"]), []).append(r)
    out = {}
    for (site, how, path), rr in by.items():
        rr = sorted(rr, key=lambda r: int(r["level"]))[:10]
        out.setdefault(site, []).append((how, path, [{"sand": num(r["PCT_SAND"]), "clay": num(r["PCT_CLAY"]),
                                                     "om_kgm3": num(r["ORGANIC"])} for r in rr]))
    return out


# ---------------------------------------------------------------- driver
def build(a):
    lit, conv = lit_profiles(read_csv(a.literature), {(m["site"], m["evidence_id"]): m for m in read_csv(a.manual)})
    grid = gridded_profiles(read_csv(a.gridded))
    surf = surface_profiles(read_csv(a.current_surface, "\t")) if a.current_surface else {}
    decisions = {r["site"]: r for r in read_csv(a.decisions)}
    sites = [r["site"] for r in read_csv(a.coords)]
    long_rows, wide_rows, cand_rows, summary = [], [], [], []
    for site in sites:
        d = decisions.get(site, {})
        prio = tuple(x.strip() for x in d.get("priority", "").split(">") if x.strip()) or DEFAULT_PRIORITY
        profiles = {**grid.get(site, {}), **lit.get(site, {})}
        if surf.get(site):
            how, path, lay = surf[site][0]
            profiles["SURFACE"] = [{"top": None, "bot": None, "label": "SURFACE", **l} for l in lay]
        layers = recommend(profiles, prio)
        cur = surf.get(site, [(None, None, None)])[0][2]
        for l in layers:
            c = cur[l["layer"] - 1] if cur else None
            long_rows.append({"site": site, **l,
                              "current_PCT_SAND": None if not c else c["sand"],
                              "current_PCT_CLAY": None if not c else c["clay"],
                              "current_ORGANIC": None if not c else c["om_kgm3"]})
        for src, prof in profiles.items():
            if src == "SURFACE":
                continue
            for j, z in enumerate(NODES_CM, 1):
                r = value_at(prof, z)
                cand_rows.append({"site": site, "source": src, "layer": j, "node_m": round(NODES_M[j - 1], 4),
                                  "PCT_SAND": None if not r else round(r["sand"], 2),
                                  "PCT_CLAY": None if not r else round(r["clay"], 2),
                                  "ORGANIC_candidate_kgm3": None if not r else r.get("om_kgm3")})
        top_src = [l["source"] for l in layers[:5]]
        primary = max(set(top_src), key=top_src.count) if top_src else "NONE"
        flags = []
        for src in ("SLGA", "SOILGRIDS"):
            if primary in ("LIT", "LITN") and src in profiles:
                g = [value_at(profiles[src], z) for z in NODES_CM[:5]]
                g = [x["sand"] for x in g if x]
                if g and abs(statistics.mean(g) - top_mean(layers, "PCT_SAND")) > 25:
                    flags.append(f"SITE_VS_{src}_SAND_DIFF_GT25")
        for l1, l2 in zip(layers, layers[1:]):
            if l1["source"] != l2["source"] and None not in (l1["PCT_SAND"], l2["PCT_SAND"]) \
                    and abs(l1["PCT_SAND"] - l2["PCT_SAND"]) > 25:
                flags.append(f"SOURCE_JUMP_L{l1['layer']}_{l2['layer']}")
        if any(c["site"] == site and c["conversion"] == "UNSTATED_AS_REPORTED" for c in conv) \
                and any(l["source"] in ("LIT", "LITN") for l in layers):
            flags.append("PSD_SCHEME_UNSTATED")
        om = [l.get("ORGANIC_candidate_kgm3") for l in layers[:4] if l.get("ORGANIC_candidate_kgm3")]
        if om and max(om) > 100:
            flags.append("REVIEW_ORGANIC")
        if d.get("flags"):
            flags += [x.strip() for x in d["flags"].split(";") if x.strip()]
        cur_top = None
        if cur:
            cur_top = f"{round(sum(c['sand'] for c in cur[:5]) / 5, 1)}/{round(sum(c['clay'] for c in cur[:5]) / 5, 1)}"
        summary.append({"site": site, "network": "OzFlux" if site.startswith("AU-") else "JapanFlux",
                        "tier": TIER.get(primary, "NO_DATA"), "priority": ">".join(prio),
                        "PCT_SAND_0_30cm": top_mean(layers, "PCT_SAND"), "PCT_CLAY_0_30cm": top_mean(layers, "PCT_CLAY"),
                        "usda_class_0_30cm": usda_class(top_mean(layers, "PCT_SAND"), top_mean(layers, "PCT_CLAY")),
                        "layer_sources": "|".join(l["source"] for l in layers), "current_surface_0_30cm": cur_top,
                        "flags": ";".join(flags), "basis": d.get("basis", ""), "note": d.get("note", "")})
        wide_rows.append({"site": site, "tier": TIER.get(primary, "NO_DATA"),
                          **{f"PCT_SAND_L{l['layer']}": l["PCT_SAND"] for l in layers},
                          **{f"PCT_CLAY_L{l['layer']}": l["PCT_CLAY"] for l in layers}})
    out = Path(a.out_dir)
    write(out / f"OZ_JP_RECOMMENDED_CLM10_SOIL_TEXTURE_LONG_{DATE}.csv", long_rows,
          ["site", "layer", "node_m", "PCT_SAND", "PCT_CLAY", "usda_class", "source", "how", "note",
           "ORGANIC_candidate_kgm3", "current_PCT_SAND", "current_PCT_CLAY", "current_ORGANIC"])
    write(out / f"OZ_JP_RECOMMENDED_CLM10_SOIL_TEXTURE_WIDE_{DATE}.csv", wide_rows,
          ["site", "tier"] + [f"PCT_SAND_L{j}" for j in range(1, 11)] + [f"PCT_CLAY_L{j}" for j in range(1, 11)])
    write(out / f"OZ_JP_RECOMMENDED_INPUT_SOIL_TEXTURE_20_SITES_{DATE}.csv", summary,
          ["site", "network", "tier", "PCT_SAND_0_30cm", "PCT_CLAY_0_30cm", "usda_class_0_30cm", "priority",
           "layer_sources", "current_surface_0_30cm", "flags", "basis", "note"])
    write(out / "data" / f"clm10_candidates_by_source_{DATE}.csv", cand_rows,
          ["site", "source", "layer", "node_m", "PCT_SAND", "PCT_CLAY", "ORGANIC_candidate_kgm3"])
    write(out / "data" / f"literature_usda_conversion_{DATE}.csv", conv,
          ["site", "evidence_id", "depth_top_cm", "depth_bottom_cm", "scheme", "reported_sand", "reported_silt",
           "reported_clay", "usda_sand", "usda_clay", "conversion", "usda_sand_if_ISSS", "manual_depth", "citation"])
    for s in summary:
        print(f"{s['site']:7s} {s['tier']:22s} 0-30 cm {s['PCT_SAND_0_30cm']}/{s['PCT_CLAY_0_30cm']} "
              f"{s['usda_class_0_30cm']:16s} {s['layer_sources']} {s['flags']}")
    return 0


def write(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def self_test():
    assert abs(NODES_M[0] - 0.0071) < 1e-4 and abs(NODES_M[9] - 2.8646) < 1e-3
    # MM2001: coarse sand keeps nearly all its sand; a 74/11/15 Kandosol loses ~15 points of sand to silt
    s, c, h = isss_to_usda(2, 1, 97)
    assert h == "MM2001" and abs(s - 95.17) < 0.05 and c == 2, (s, c)
    s, c, h = isss_to_usda(15, 11, 74)
    assert abs(s - 59.1) < 0.1, s
    s, c, h = isss_to_usda(0, 0, 100)                       # quadratic < 0 -> linear branch
    assert abs(s - 98.02) < 0.01, s
    s, c, h = isss_to_usda(35, 60, 5)                       # clipped: USDA silt >= ISSS silt
    assert abs(s - 5.0) < 1e-9, s
    s, c, h = isss_to_usda(10, 20, 70, fine_sand=30)        # log-linear inside 20-200 um
    assert h == "LOGLINEAR_20_200" and abs(s - (70 - 30 * math.log(2.5) / math.log(10))) < 1e-9
    # evidence: an ISSS 0-30 cm record over SoilGrids, extended below 200 cm from SoilGrids
    lit = [{"site": "X", "evidence_id": "X-L1", "use_numeric": "YES", "depth_top_cm": "0", "depth_bottom_cm": "30",
            "sand_pct": "74", "silt_pct": "11", "clay_pct": "15", "size_scheme": "ISSS", "tower_specific": "YES",
            "bulk_density_g_cm3": "1.5", "organic_carbon_pct": "0.5"}]
    lp, conv = lit_profiles(lit, {})
    assert conv[0]["conversion"] == "MM2001" and lp["X"]["LIT"][0]["om_kgm3"] == round(0.5 * 10 * 1.5 * 1.724, 1)
    g = gridded_profiles([{"site": "X", "source": "SOILGRIDS", "depth_top_cm": str(t), "depth_bottom_cm": str(b),
                           "statistic": "mean", "status": "OK", "property": p, "value": str(v)}
                          for t, b in ((0, 5), (5, 15), (15, 30), (30, 60), (60, 100), (100, 200))
                          for p, v in (("sand", 50), ("clay", 30), ("silt", 20), ("soc", 10), ("bdod", 1.2))])
    lay = recommend({**g["X"], **lp["X"]}, DEFAULT_PRIORITY)
    assert [l["source"] for l in lay] == ["LIT"] * 5 + ["SOILGRIDS"] * 5, [l["source"] for l in lay]
    assert lay[9]["how"] == "EXTENDED_BELOW_200cm" and lay[5]["PCT_SAND"] == 50.0
    assert abs(top_mean(lay, "PCT_SAND") - 59.1) < 0.1
    # manual depth: a no-depth bulk value applied to the whole profile
    lit[0].update(depth_top_cm="", depth_bottom_cm="")
    lp, _ = lit_profiles(lit, {("X", "X-L1"): {"applied_top_cm": "0", "applied_bottom_cm": "300"}})
    lay = recommend({**g["X"], **lp["X"]}, DEFAULT_PRIORITY)
    assert all(l["source"] == "LIT" and l["how"] == "COVERED" for l in lay)      # node 10 is 286 cm < 300
    try:
        lit_profiles(lit, {})
        raise AssertionError("missing depth must fail")
    except ValueError:
        pass
    # SURFACE inside the priority wins over SoilGrids, but not over site evidence above it
    surf = [{"top": None, "bot": None, "sand": 20.0, "clay": 54.0, "om_kgm3": 25.0} for _ in range(10)]
    lay = recommend({**g["X"], "SURFACE": surf}, ("LIT", "SLGA", "SURFACE", "SOILGRIDS"))
    assert all(l["source"] == "SURFACE" and l["how"] == "KEEP_SURFACE" and l["PCT_CLAY"] == 54.0 for l in lay)
    lay = recommend({**g["X"], **lp["X"], "SURFACE": surf}, ("LIT", "SURFACE", "SOILGRIDS"))
    assert all(l["source"] == "LIT" for l in lay)
    assert usda_class(95, 2) == "sand" and usda_class(59, 15) == "sandy loam" and usda_class(20, 55) == "clay"
    print("STAGE03 SELF-TEST PASS (ISSS->USDA MM2001 and log-linear, layer mapping, deep extension, manual depth, "
          "SURFACE in priority, ORGANIC candidate)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--literature", default=str(DATA / f"literature_soil_evidence_{DATE}.csv"))
    ap.add_argument("--manual", default=str(DATA / f"manual_depth_assignments_{DATE}.csv"))
    ap.add_argument("--decisions", default=str(DATA / f"site_soil_decisions_{DATE}.csv"))
    ap.add_argument("--coords", default=str(DATA / f"OZ_JP_20_SITE_COORDINATES_{DATE}.csv"))
    ap.add_argument("--gridded", default=str(DATA / "gridded" / "gridded_soil_at_towers_long.csv"))
    ap.add_argument("--current-surface")
    ap.add_argument("--out-dir", default=str(HERE.parent))
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    return build(a)


if __name__ == "__main__":
    sys.exit(main())

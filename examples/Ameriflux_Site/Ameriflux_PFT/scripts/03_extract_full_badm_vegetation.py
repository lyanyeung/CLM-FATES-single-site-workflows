#!/usr/bin/env python3
"""Extract vegetation / PFT evidence from the full AmeriFlux BADM downloads
(AMF_<SITE>_BIF_<YYYYMMDD>.xlsx) for the 50 sites. Read-only, standard library only.

BADM groups read:
  GRP_IGBP          IGBP class, comment, start date
  GRP_SITE_DESC     free-text site description
  GRP_SPP_O, GRP_SPP_U  SPP_O / SPP_U (species, NRCS code or scientific name) or
                    SPP_O_VEGTYPE / SPP_U_VEGTYPE, with SPP_*_PERC and SPP_PERC_UNIT
                    (Area, Mass, Number or Estimated abundance), approach, date, comment
  GRP_LAI, GRP_HEIGHTC, GRP_AG_BIOMASS*, GRP_BASAL_AREA, GRP_TREES_NUM, GRP_DM_*
                    kept as long rows for context

  python3 -B 03_extract_full_badm_vegetation.py --badm-dir /mnt/d/.../BADM --output-dir /mnt/d/.../BADM_veg_extract

Outputs:
  E_badm_igbp_site_desc.csv      one row per site
  F_badm_species_cover.csv       one row per SPP group
  G_badm_species_codes.csv       unique species codes / names with sites (for PFT mapping)
  H_badm_veg_context_long.csv    LAI, canopy height, biomass, basal area, disturbance rows
  I_badm_veg_site_summary.csv    per-site overstory / understory totals and units
"""
import argparse, csv, importlib.util, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOIL01 = HERE.parent.parent / "Ameriflux_Soil/scripts/01_collect_soil_texture_evidence.py"
spec = importlib.util.spec_from_file_location("soil01", SOIL01)
S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
CONTEXT = re.compile(r"^GRP_(LAI|HEIGHTC|AG_BIOMASS|BASAL_AREA|TREES_NUM|DM_|ROOT_BIOMASS|AG_PROD)", re.I)


def write(path, rows):
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields or ["site"]); w.writeheader(); w.writerows(rows)


def groups_of(path, site):
    groups = {}
    for r in S.read_bif_rows(path):
        if r.get("SITE_ID") and r["SITE_ID"].strip().upper() != site.upper():
            continue
        g = groups.setdefault(str(r["GROUP_ID"]).strip(), {"_group": r["VARIABLE_GROUP"].strip(), "_rows": []})
        g["_rows"].append((r["VARIABLE"].strip(), str(r["DATAVALUE"]).strip()))
        g.setdefault(r["VARIABLE"].strip(), str(r["DATAVALUE"]).strip())
    return groups


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--badm-dir", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    a = ap.parse_args()
    a.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = list(csv.DictReader(S.MANIFEST.open(encoding="utf-8")))
    E, F, H, I = [], [], [], []
    codes = {}
    for m in manifest:
        s = m["site"]; f = S.find_full_badm(a.badm_dir, s)
        if not f:
            E.append({"site": s, "batch": m["batch"], "badm_file": "NOT_FOUND"}); print(f"{s:7} NOT FOUND"); continue
        G = groups_of(f, s)
        igbp = [g for g in G.values() if g["_group"].upper() == "GRP_IGBP"]
        desc = [g.get("SITE_DESC", "") for g in G.values() if g["_group"].upper() == "GRP_SITE_DESC"]
        E.append({"site": s, "batch": m["batch"], "badm_file": f.name,
                  "IGBP": "; ".join(g.get("IGBP", "") for g in igbp),
                  "IGBP_DATE_START": "; ".join(g.get("IGBP_DATE_START", "") for g in igbp if g.get("IGBP_DATE_START")),
                  "IGBP_COMMENT": " | ".join(g.get("IGBP_COMMENT", "") for g in igbp if g.get("IGBP_COMMENT")),
                  "SITE_DESC": " | ".join(x.replace("\n", " ") for x in desc)})
        spp = []
        for gid, g in G.items():
            grp = g["_group"].upper()
            if grp.startswith("GRP_SPP"):
                for layer in ("O", "U"):
                    name, veg = (" ".join(g.get(f"SPP_{layer}", "").split()), " ".join(g.get(f"SPP_{layer}_VEGTYPE", "").split()))
                    if not (name or veg):
                        continue
                    code = re.sub(r"\s*\(NRCS plant code\)\s*$", "", name, flags=re.I).strip()
                    row = {"site": s, "group_id": gid, "layer": "overstory" if layer == "O" else "understory",
                           "species": code, "species_raw": name, "vegtype": veg,
                           "perc": g.get(f"SPP_{layer}_PERC", ""), "perc_unit": g.get("SPP_PERC_UNIT", ""),
                           "prevalence": g.get(f"SPP_{layer}_PREVALENCE", ""),
                           "statistic": g.get(f"SPP_{layer}_PERC_STATISTIC", ""), "approach": g.get("SPP_APPROACH", ""),
                           "date": g.get("SPP_DATE", "") or "-".join(x for x in (g.get("SPP_DATE_START", ""), g.get("SPP_DATE_END", "")) if x),
                           "comment": g.get("SPP_COMMENT", "").replace("\n", " ")[:400], "badm_file": f.name}
                    F.append(row); spp.append(row)
                    key = code or veg
                    c = codes.setdefault(key, {"species_or_vegtype": key, "is_vegtype": bool(veg and not code), "raw_examples": set(), "sites": set()})
                    c["raw_examples"].add(name or veg); c["sites"].add(s)
            elif CONTEXT.match(grp):
                for var, val in g["_rows"]:
                    H.append({"site": s, "group_id": gid, "variable_group": g["_group"], "variable": var,
                              "value": val.replace("\n", " ")[:300], "badm_file": f.name})
        def tot(layer):
            v = [S.num(r["perc"]) for r in spp if r["layer"] == layer and S.num(r["perc"]) is not None]
            return round(sum(v), 2) if v else ""
        I.append({"site": s, "batch": m["batch"], "IGBP": E[-1]["IGBP"],
                  "n_overstory": sum(r["layer"] == "overstory" for r in spp), "n_understory": sum(r["layer"] == "understory" for r in spp),
                  "overstory_perc_sum": tot("overstory"), "understory_perc_sum": tot("understory"),
                  "perc_units": "; ".join(sorted({r["perc_unit"] for r in spp if r["perc_unit"]})) or ("NOT_GIVEN" if spp else ""),
                  "overstory": "; ".join(f"{r['species'] or r['vegtype']}={r['perc'] or '?'}" for r in spp if r["layer"] == "overstory"),
                  "understory": "; ".join(f"{r['species'] or r['vegtype']}={r['perc'] or '?'}" for r in spp if r["layer"] == "understory")})
        print(f"{s:7} IGBP={E[-1]['IGBP']:8} O={I[-1]['n_overstory']:2} (sum {I[-1]['overstory_perc_sum']}) "
              f"U={I[-1]['n_understory']:2} unit={I[-1]['perc_units'][:20]:20} {I[-1]['overstory'][:80]}", flush=True)
    Gr = [{"species_or_vegtype": c["species_or_vegtype"], "is_vegtype": c["is_vegtype"], "n_sites": len(c["sites"]),
           "sites": " ".join(sorted(c["sites"])), "raw_examples": " | ".join(sorted(c["raw_examples"]))[:200]}
          for c in sorted(codes.values(), key=lambda c: c["species_or_vegtype"])]
    for name, rows in (("E_badm_igbp_site_desc.csv", E), ("F_badm_species_cover.csv", F), ("G_badm_species_codes.csv", Gr),
                       ("H_badm_veg_context_long.csv", H), ("I_badm_veg_site_summary.csv", I)):
        write(a.output_dir / name, rows)
    print(f"\nFILES {sum(1 for e in E if e['badm_file'] != 'NOT_FOUND')}/50 | sites with SPP {sum(1 for i in I if i['n_overstory'] or i['n_understory'])} "
          f"| SPP rows {len(F)} | unique species/vegtypes {len(Gr)} -> {a.output_dir}")


if __name__ == "__main__":
    main()

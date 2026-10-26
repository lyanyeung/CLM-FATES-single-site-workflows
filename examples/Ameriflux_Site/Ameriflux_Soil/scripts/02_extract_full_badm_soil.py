#!/usr/bin/env python3
"""Stage02: extract every soil record from the full AmeriFlux BADM downloads
(AMF_<SITE>_BIF_<YYYYMMDD>.xlsx) for the 50 sites. Read-only, standard library only
(works on a laptop or in WSL without extra packages or internet access).

Uses the same parser and depth rules as Stage01 (01_collect_soil_texture_evidence.py):
depth from SOIL_TEX_PROFILE_MIN/MAX, else the same horizon in another soil group,
else data/badm_manual_depth_assignments_20261026.csv. A group without depth is
reported but never used.

  python3 -B 02_extract_full_badm_soil.py --badm-dir /mnt/d/.../BADM --output-dir /mnt/d/.../BADM_soil_extract

Outputs:
  A_badm_file_inventory.csv          site, file found, BIF date, soil-row counts, coordinates
  B_badm_soil_rows_long.csv          every GRP_SOIL_* variable (TEX, CHEM, DEPTH, CLASSIFICATION ...)
  C_badm_soil_tex_groups.csv         each SOIL_TEX group, depth source and USED/NOT_USED decision
  D_badm_site_soil_summary.csv       one row per site: classification, depth, texture used/unused
"""
import argparse, csv, importlib.util, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("soil01", HERE / "01_collect_soil_texture_evidence.py")
S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)


def write(path, rows):
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields or ["site"]); w.writeheader(); w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--badm-dir", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    a = ap.parse_args()
    if not a.badm_dir.is_dir():
        raise SystemExit(f"Not a folder: {a.badm_dir}")
    a.output_dir.mkdir(parents=True, exist_ok=True)
    manual = S.read_manual()
    manifest = list(csv.DictReader(S.MANIFEST.open(encoding="utf-8")))
    inv, long_rows, groups, summ = [], [], [], []
    for m in manifest:
        s = m["site"]
        f = S.find_full_badm(a.badm_dir, s)
        if not f:
            inv.append({"site": s, "batch": m["batch"], "badm_file": "NOT_FOUND"})
            summ.append({"site": s, "batch": m["batch"], "badm_file": "NOT_FOUND"})
            print(f"{s:7} NOT FOUND", flush=True)
            continue
        try:
            lat, lon, rows, prof, dec = S.parse_bif(f, s, manual)
        except Exception as e:
            inv.append({"site": s, "batch": m["batch"], "badm_file": f.name, "error": f"{type(e).__name__}: {e}"})
            print(f"{s:7} ERROR {e}", flush=True)
            continue
        long_rows += [{"site": s, **r} for r in rows]
        groups += [{"site": s, **d} for d in dec]
        by = {}
        for r in rows:
            by.setdefault(r["variable_group"], set()).add(r["group_id"])
        val = lambda var: "; ".join(sorted({r["value"].replace("\n", " ").strip() for r in rows if r["variable"] == var and r["value"].strip()}))
        used = [d for d in dec if d["decision"] == "USED"]
        inv.append({"site": s, "batch": m["batch"], "badm_file": f.name, "lat": lat, "lon": lon, "soil_rows": len(rows),
                    **{f"n_{g}": len(v) for g, v in sorted(by.items())}})
        summ.append({"site": s, "batch": m["batch"], "badm_file": f.name,
                     "soil_classification": val("SOIL_CLASSIFICATION"), "soil_depth_cm": val("SOIL_DEPTH"),
                     "n_tex_groups": len(dec), "n_tex_used": len(used),
                     "tex_not_used": "; ".join(f"{d['group_id']}:{d['decision']}" for d in dec if d["decision"] != "USED"),
                     "used_profile_sand_clay": " | ".join(f"{r['top']:g}-{r['bot']:g}cm {r['sand']:.1f}/{r['clay']:.1f}" for r in prof)})
        print(f"{s:7} {f.name:34} soil_rows={len(rows):3} tex_groups={len(dec):2} used={len(used):2} "
              f"{summ[-1]['used_profile_sand_clay'][:90]}", flush=True)
    write(a.output_dir / "A_badm_file_inventory.csv", inv)
    write(a.output_dir / "B_badm_soil_rows_long.csv", long_rows)
    write(a.output_dir / "C_badm_soil_tex_groups.csv", groups)
    write(a.output_dir / "D_badm_site_soil_summary.csv", summ)
    found = sum(1 for r in inv if r.get("badm_file") not in ("NOT_FOUND", None) and "error" not in r)
    withtex = sum(1 for r in summ if r.get("n_tex_groups"))
    print(f"\nFILES {found}/50 | sites with SOIL_TEX groups {withtex} | groups {len(groups)} "
          f"(used {sum(1 for g in groups if g['decision'] == 'USED')}) -> {a.output_dir}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Download and tabulate ICOS ETC ancillary reports for the 38 European sites.

Standard library only (works in WSL, on a laptop or on IRIDIS login nodes).
For each site it fetches
  https://icos.uantwerpen.be/Content/AncillaryReports/<SITE>_Ancillary_Report.html
  https://icos.uantwerpen.be/Content/AncillaryReports/<SITE>_Full_Ancillary_Report.html
and exports every HTML <table> and every embedded DataTables (htmlwidgets JSON)
table to CSV. Tables that look like species composition (GRP_TREE / SPP_PERC /
species) or soil (GRP_SOIL / texture / sand / clay) are collected separately.
Sites that are not ICOS stations simply return 404 and are recorded as such.

  python3 -B 01_fetch_ICOS_ancillary_reports.py --out ~/ICOS_ancillary_20261026
  python3 -B 01_fetch_ICOS_ancillary_reports.py --self-test

Outputs in --out:
  raw/<SITE>_<summary|full>.html
  tables/<SITE>_<summary|full>_<n>.csv     every table found
  01_report_inventory.csv                   one row per site x report
  02_species_tables_long.csv                all rows of species-like tables
  03_soil_tables_long.csv                   all rows of soil-like tables
  04_keyword_context.csv                    text around sand/silt/clay/texture/SPP_PERC
"""
import argparse, csv, html, json, re, sys, time, urllib.error, urllib.request
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://icos.uantwerpen.be/Content/AncillaryReports/"
SITES = ["DE-Tha", "NL-Loo", "DE-Hai", "RU-Fyo", "DK-Sor", "IL-Yat", "CZ-BK1", "IT-Ren", "FR-Hes", "FR-FBn",
         "DE-Hzd", "CH-Dav", "BE-Vie", "IT-Lav", "BE-Bra", "FR-Fon", "GL-ZaH", "IT-Noe", "AT-Neu", "FI-Sod",
         "CH-Aws", "CH-Cha", "CH-Fru", "CH-Lae", "CZ-Stn", "DE-Lnf", "DE-Obe", "ES-Agu", "ES-LJu", "IT-Col",
         "DE-Gri", "DE-RuR", "FI-Hyy", "FI-Let", "FR-Pue", "GF-Guy", "IT-MBo", "IT-Tor"]
REPORTS = {"summary": "{s}_Ancillary_Report.html", "full": "{s}_Full_Ancillary_Report.html"}
SPECIES_RE = re.compile(r"SPP|species|GRP_TREE|TREE_SPP|VEGTYPE|AGB_VEG", re.I)
SOIL_RE = re.compile(r"GRP_SOIL|SOIL|sand|silt|clay|textur|horizon|bulk.?dens|SOC", re.I)
KEY_RE = re.compile(r"(sand|silt|clay|soil textur\w*|SOIL_TEX\w*|SPP_PERC\w*|WRB|soil type|soil class\w*)", re.I)


class Tables(HTMLParser):
    """Collect <table> cells and <script type=application/json> payloads."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables, self.scripts, self.text = [], [], []
        self._stack, self._row, self._cell, self._script = [], None, None, None
        self.section, self._head = "", None
        self.table_sec, self.script_sec, self.images = [], [], {}
        self.image_src = []  # (section, data-URI)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("h1", "h2", "h3", "h4"): self._head = []
        elif tag == "img" and (a.get("src") or "").startswith("data:image"):
            self.images[self.section] = self.images.get(self.section, 0) + 1
            self.image_src.append((self.section, a["src"]))
        if tag == "table": self._stack.append([])
        elif tag == "tr" and self._stack: self._row = []
        elif tag in ("td", "th") and self._row is not None: self._cell = []
        elif tag == "script" and "json" in (a.get("type") or ""): self._script = []

    def handle_endtag(self, tag):
        if tag in ("h1", "h2", "h3", "h4") and self._head is not None:
            t = " ".join("".join(self._head).split())
            if t: self.section = t[:120]
            self._head = None
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(" ".join("".join(self._cell).split())); self._cell = None
        elif tag == "tr" and self._row is not None and self._stack:
            if self._row: self._stack[-1].append(self._row)
            self._row = None
        elif tag == "table" and self._stack:
            t = self._stack.pop()
            if t: self.tables.append(t); self.table_sec.append(self.section)
        elif tag == "script" and self._script is not None:
            self.scripts.append("".join(self._script)); self.script_sec.append(self.section); self._script = None

    def handle_data(self, d):
        if self._script is not None: self._script.append(d); return
        if self._head is not None: self._head.append(d)
        if self._cell is not None: self._cell.append(d)
        self.text.append(d)


def widget_tables(scripts):
    """DataTables htmlwidgets: {"x": {"data": [[col values]...], "container": "<table>..<th>..</th>"}}."""
    out = []
    for raw in scripts:
        try: obj = json.loads(raw)
        except Exception: continue
        x = obj.get("x") if isinstance(obj, dict) else None
        if not isinstance(x, dict) or "data" not in x: continue
        data = x["data"]
        heads = [html.unescape(re.sub(r"<[^>]+>", "", h)).strip() for h in re.findall(r"<th[^>]*>(.*?)</th>", x.get("container", ""), re.S)]
        if isinstance(data, list) and data and isinstance(data[0], list):
            n = max(len(c) for c in data)
            if len(data) == len(heads) or (heads and len(data) == len(heads) - 1):  # column-major
                cols = data if len(data) == len(heads) else [[str(i + 1) for i in range(n)]] + data
                rows = [[str(c[i]) if i < len(c) else "" for c in cols] for i in range(n)]
            else:  # row-major
                rows = [[str(v) for v in r] for r in data]
        elif isinstance(data, dict):
            heads = heads or list(data)
            cols = [data[k] for k in data]
            n = max(len(c) for c in cols)
            rows = [[str(c[i]) if i < len(c) else "" for c in cols] for i in range(n)]
        else:
            continue
        out.append(([heads] if heads else []) + rows)
    return out


def plotly_traces(scripts, sections):
    """htmlwidgets plotly: {"x": {"data": [{"type":..,"name":..,"x":[..],"y":[..]}], "layout": {...}}}."""
    rows = []
    for w, (raw, sec) in enumerate(zip(scripts, sections), 1):
        try: obj = json.loads(raw)
        except Exception: continue
        x = obj.get("x") if isinstance(obj, dict) else None
        if not isinstance(x, dict) or not isinstance(x.get("data"), list) or not x["data"] or not isinstance(x["data"][0], dict): continue
        lay = x.get("layout", {}) or {}
        def title(o):
            t = o.get("title") if isinstance(o, dict) else None
            return (t.get("text") if isinstance(t, dict) else t) or ""
        meta = {"section": sec, "widget": w, "plot_title": re.sub(r"<[^>]+>", " ", str(title(lay)))[:150],
                "xaxis": re.sub(r"<[^>]+>", " ", str(title(lay.get("xaxis", {}))))[:80],
                "yaxis": re.sub(r"<[^>]+>", " ", str(title(lay.get("yaxis", {}))))[:80]}
        for t, tr in enumerate(x["data"], 1):
            def seq(k):
                v = tr.get(k)
                if v is None: return []
                return v if isinstance(v, list) else [v]
            xs, ys, tx = seq("x"), seq("y"), seq("text") or seq("hovertext")
            n = max(len(xs), len(ys), len(tx), 1)
            for i in range(n):
                pick = lambda a: a[i] if i < len(a) else (a[0] if len(a) == 1 else "")
                rows.append({**meta, "trace": t, "trace_name": str(tr.get("name", ""))[:120], "type": tr.get("type", ""),
                             "legendgroup": str(tr.get("legendgroup", ""))[:80], "x": str(pick(xs))[:120],
                             "y": str(pick(ys))[:60], "text": re.sub(r"<br\s*/?>", "; ", str(pick(tx)))[:300]})
    return rows


def fetch(url, tries=3):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research; CLM-FATES site inputs)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, b""
        except Exception as e:
            if k == tries - 1: return f"ERR {type(e).__name__}: {e}", b""
            time.sleep(3)


def parse(raw, full=False):
    p = Tables(); p.feed(raw.decode("utf-8", "replace"))
    if full: return p
    return p.tables, widget_tables(p.scripts), " ".join(" ".join(p.text).split())


def classify(table):
    head = " ".join(table[0]) if table else ""
    body = " ".join(" ".join(r) for r in table[:6])
    kinds = []
    if SPECIES_RE.search(head) or re.search(r"\b[A-Z][a-z]+ [a-z]{3,}\b.*(L\.|Mill\.|Karst|Ehrh|Roth)", body): kinds.append("species")
    if SOIL_RE.search(head): kinds.append("soil")
    return kinds


def run(out, sites, pause):
    out = Path(out).expanduser(); (out / "raw").mkdir(parents=True, exist_ok=True); (out / "tables").mkdir(exist_ok=True)
    inv, spp, soil, keys = [], [], [], []
    for s in sites:
        for kind, pat in REPORTS.items():
            url = BASE + pat.format(s=s)
            status, raw = fetch(url)
            row = {"site": s, "report": kind, "url": url, "http_status": status, "bytes": len(raw)}
            if status == 200 and raw:
                (out / "raw" / f"{s}_{kind}.html").write_bytes(raw)
                tabs, widgets, text = parse(raw)
                allt = [("html", t) for t in tabs] + [("widget", t) for t in widgets]
                row.update(n_html_tables=len(tabs), n_widget_tables=len(widgets),
                           groups_mentioned=" ".join(sorted(set(re.findall(r"GRP_[A-Z_]+", text)))))
                for i, (src, t) in enumerate(allt, 1):
                    f = out / "tables" / f"{s}_{kind}_{i:02d}.csv"
                    with f.open("w", newline="", encoding="utf-8") as fh: csv.writer(fh).writerows(t)
                    for k in classify(t):
                        head = t[0]
                        for r in t[1:]:
                            rec = {"site": s, "report": kind, "table": f.name, "source": src,
                                   "header": " | ".join(head), "row": " | ".join(r)}
                            (spp if k == "species" else soil).append(rec)
                for m in KEY_RE.finditer(text):
                    keys.append({"site": s, "report": kind, "keyword": m.group(1),
                                 "context": text[max(0, m.start() - 120): m.end() + 160]})
                row["species_rows"] = sum(1 for r in spp if r["site"] == s and r["report"] == kind)
                row["soil_rows"] = sum(1 for r in soil if r["site"] == s and r["report"] == kind)
            inv.append(row)
            print(f"{s:7} {kind:7} HTTP {status} {len(raw):>9} B tables={row.get('n_html_tables', '-')}"
                  f"+{row.get('n_widget_tables', '-')} species_rows={row.get('species_rows', '-')} soil_rows={row.get('soil_rows', '-')}", flush=True)
            time.sleep(pause)
    def write(name, rows):
        fields = []
        for r in rows:
            for k in r:
                if k not in fields: fields.append(k)
        with (out / name).open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields or ["site"]); w.writeheader(); w.writerows(rows)
    write("01_report_inventory.csv", inv); write("02_species_tables_long.csv", spp)
    write("03_soil_tables_long.csv", soil); write("04_keyword_context.csv", keys)
    ok = sorted({r["site"] for r in inv if r["http_status"] == 200})
    print(f"\nSITES WITH ANY REPORT {len(ok)}/{len(sites)}: {' '.join(ok)}")
    print(f"SPECIES ROWS {len(spp)} | SOIL ROWS {len(soil)} | KEYWORD HITS {len(keys)} -> {out}")


def from_raw(out):
    """Re-parse already downloaded raw/*.html (no network): plotly traces + structure per section."""
    out = Path(out).expanduser(); traces, struct = [], []
    for f in sorted((out / "raw").glob("*.html")):
        site, kind = f.stem.rsplit("_", 1)
        p = parse(f.read_bytes(), full=True)
        tr = plotly_traces(p.scripts, p.script_sec)
        for r in tr: traces.append({"site": site, "report": kind, **r})
        secs = sorted(set(p.table_sec) | set(p.script_sec) | set(p.images))
        for sec in secs:
            struct.append({"site": site, "report": kind, "section": sec,
                           "html_tables": p.table_sec.count(sec), "json_widgets": p.script_sec.count(sec),
                           "plotly_points": sum(1 for r in tr if r["section"] == sec),
                           "embedded_images": p.images.get(sec, 0)})
        print(f"{site:7} {kind:7} sections={len(secs):3} widgets={len(p.scripts):3} plotly_points={len(tr):6} "
              f"images={sum(p.images.values()):3}", flush=True)
    for name, rows in (("05_plotly_traces_long.csv", traces), ("06_report_structure_by_section.csv", struct)):
        fields = []
        for r in rows:
            for k in r:
                if k not in fields: fields.append(k)
        with (out / name).open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fields or ["site"]); w.writeheader(); w.writerows(rows)
    print(f"PLOTLY POINTS {len(traces)} | SECTIONS {len(struct)} -> {out}")


IMG_SECTIONS = re.compile(r"GRP_TREE|GRP_AGB|GRP_SOIL|species|tree|understor|soil", re.I)


def export_images(out, all_sections=False):
    """Write chart PNGs of the species/understory/soil sections to <out>/images (no network)."""
    import base64
    out = Path(out).expanduser(); d = out / "images"; d.mkdir(exist_ok=True); idx = []
    for f in sorted((out / "raw").glob("*.html")):
        site, kind = f.stem.rsplit("_", 1)
        p = parse(f.read_bytes(), full=True); n = 0
        for i, (sec, src) in enumerate(p.image_src, 1):
            if not all_sections and not IMG_SECTIONS.search(sec): continue
            m = re.match(r"data:image/(\w+);base64,(.*)", src, re.S)
            if not m: continue
            ext = "jpg" if m.group(1) == "jpeg" else m.group(1)
            tag = re.sub(r"[^A-Za-z0-9]+", "_", sec)[:40].strip("_") or "nosection"
            name = f"{site}_{i:02d}_{tag}.{ext}"
            (d / name).write_bytes(base64.b64decode(m.group(2))); n += 1
            idx.append({"site": site, "report": kind, "image": name, "section": sec, "order_in_report": i})
        print(f"{site:7} exported {n} images", flush=True)
    with (out / "07_exported_images_index.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["site", "report", "image", "section", "order_in_report"]); w.writeheader(); w.writerows(idx)
    print(f"IMAGES {len(idx)} -> {d}")


def self_test():
    page = ("<html><body><h2>GRP_TREE</h2><table><tr><th>SPP</th><th>YEAR</th><th>PLOT</th><th>SPP_PERC</th></tr>"
            "<tr><td>Picea abies (L.) H.Karst.</td><td>2022</td><td>CP</td><td>41.24</td></tr></table>"
            "<p>GRP_SOIL bulk density; soil texture not measured; clay 20%</p>"
            '<script type="application/json" data-for="w1">{"x":{"data":[["1","2"],["A","B"],["10","20"]],'
            '"container":"<table><thead><tr><th> </th><th>SOIL_HORIZON</th><th>SOIL_SAND</th></tr></thead></table>"}}</script>'
            "</body></html>").encode()
    tabs, widgets, text = parse(page)
    assert tabs[0][1] == ["Picea abies (L.) H.Karst.", "2022", "CP", "41.24"], tabs
    assert widgets[0][0] == ["", "SOIL_HORIZON", "SOIL_SAND"] and widgets[0][1] == ["1", "A", "10"], widgets
    assert classify(tabs[0]) == ["species"] and "soil" in classify(widgets[0])
    assert {m.group(1).lower() for m in KEY_RE.finditer(text)} >= {"clay", "soil texture"}
    assert len(SITES) == 38 and len(set(SITES)) == 38
    pg = ('<h2>GRP_TREE</h2><img src="data:image/png;base64,AAAA"><script type="application/json" data-for="p1">'
          '{"x":{"data":[{"type":"bar","name":"Fagus sylvatica","x":["2021","2023"],"y":[60.5,62.1]}],'
          '"layout":{"title":{"text":"Species ratio"}}}}</script><h2>GRP_SOIL</h2>').encode()
    pp = parse(pg, full=True); tr = plotly_traces(pp.scripts, pp.script_sec)
    assert len(tr) == 2 and tr[1]["trace_name"] == "Fagus sylvatica" and tr[1]["y"] == "62.1" and tr[0]["section"] == "GRP_TREE"
    assert pp.images == {"GRP_TREE": 1} and pp.image_src[0][0] == "GRP_TREE"
    print("ICOS ANCILLARY FETCH SELF-TEST PASS (no network)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="~/ICOS_ancillary_20261026")
    ap.add_argument("--sites", nargs="+", default=SITES)
    ap.add_argument("--pause", type=float, default=1.0, help="seconds between requests")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--from-raw", action="store_true", help="re-parse <out>/raw/*.html only (no network)")
    ap.add_argument("--export-images", action="store_true", help="write species/understory/soil chart PNGs (no network)")
    ap.add_argument("--all-sections", action="store_true", help="with --export-images: every section")
    a = ap.parse_args()
    if a.self_test: self_test(); sys.exit(0)
    if a.from_raw: from_raw(a.out); sys.exit(0)
    if a.export_images: export_images(a.out, a.all_sections); sys.exit(0)
    run(a.out, a.sites, a.pause)

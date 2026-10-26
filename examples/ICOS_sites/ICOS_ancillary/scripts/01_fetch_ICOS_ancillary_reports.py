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

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table": self._stack.append([])
        elif tag == "tr" and self._stack: self._row = []
        elif tag in ("td", "th") and self._row is not None: self._cell = []
        elif tag == "script" and "json" in (a.get("type") or ""): self._script = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(" ".join("".join(self._cell).split())); self._cell = None
        elif tag == "tr" and self._row is not None and self._stack:
            if self._row: self._stack[-1].append(self._row)
            self._row = None
        elif tag == "table" and self._stack:
            t = self._stack.pop()
            if t: self.tables.append(t)
        elif tag == "script" and self._script is not None:
            self.scripts.append("".join(self._script)); self._script = None

    def handle_data(self, d):
        if self._script is not None: self._script.append(d); return
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


def parse(raw):
    p = Tables(); p.feed(raw.decode("utf-8", "replace"))
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
    print("ICOS ANCILLARY FETCH SELF-TEST PASS (no network)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="~/ICOS_ancillary_20261026")
    ap.add_argument("--sites", nargs="+", default=SITES)
    ap.add_argument("--pause", type=float, default=1.0, help="seconds between requests")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test: self_test(); sys.exit(0)
    run(a.out, a.sites, a.pause)

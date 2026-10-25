#!/usr/bin/env python3
"""US-SP1 Oct 15-18 + Oct 22-23 2007, six exact full local-standard days.

Checks SHA-pinned ORIGINAL full-release 368,208 HH FLUXMET source and extracts
exact 288 native HH (48 each). Prints full original TA_F, native TA_F_QC,
TA_F_MDS/QC, TA_ERA, VPD_F/QC and delta to ERA for human review. --report
additionally writes *only new standalone evidence reports* (six-day 288-row
CSV and self-contained static HTML charts/tables) under user HOME.
No original, Stage14, model, DATM or other input modifications.
"""
import argparse, csv, hashlib, html, math
from datetime import datetime, timedelta
from pathlib import Path

SRC=Path("/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/US-SP1/forcing/raw/"
 "AMF_US-SP1_FLUXNET_2000-2020_v1.3_r1/"
 "AMF_US-SP1_FLUXNET_FLUXMET_HH_2000-2020_v1.3_r1.csv")
ORIGINAL_SHA="d5fe39d617e1e7964542cf3d3f8f068e00b028a37e4db7814b77c6cd813e1963"
EXPECTED_ROWS=368208
DATES=("20071015","20071016","20071017","20071018","20071022","20071023")
NEEDED=("TIMESTAMP_START","TA_F","TA_F_QC","TA_F_MDS",
        "TA_F_MDS_QC","TA_ERA","VPD_F","VPD_F_QC")
ANCHORS={
 "20071015":(11.150,23.220),
 "20071016":(11.149,23.220),
 "20071017":(11.169,23.710),
 "20071018":(11.138,26.240),
 "20071022":(11.126,23.390),
 "20071023":(11.123,25.570),
}
OUTPUT=Path.home()/"ameriflux_batch04_manual_review"
def finite(x):
    try:v=float(x)
    except (TypeError,ValueError):return None
    return v if math.isfinite(v) and v not in (-9999,-6999) else None
def digest(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(4<<20),b""):h.update(chunk)
    return h.hexdigest()
def read_original():
    if SRC.is_symlink() or not SRC.is_file():raise ValueError("Original input missing or symlinked "+str(SRC))
    got=digest(SRC)
    if got!=ORIGINAL_SHA:raise ValueError("Original source SHA256 mismatch "+got)
    found={d:{} for d in DATES};n=0
    with SRC.open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        if not rd.fieldnames or not set(NEEDED).issubset(rd.fieldnames):
            raise ValueError("Original FLUXMET_HH field names unexpected")
        for row in rd:
            n+=1
            key=row["TIMESTAMP_START"]
            day=key[:8]
            if day not in found:continue
            if len(key)!=12 or key in found[day]:raise ValueError("Repeated/invalid HH source key "+key)
            found[day][key]={col:row[col] for col in NEEDED}
    if n!=EXPECTED_ROWS:raise ValueError(f"Unexpected entire source row count {n}")
    for day in DATES:
        start=datetime.strptime(day,"%Y%m%d")
        keys=[(start+timedelta(minutes=30*i)).strftime("%Y%m%d%H%M") for i in range(48)]
        if set(found[day])!=set(keys):
            raise ValueError(f"Full 00:00–23:30 native day missing, duplicate or unexpected {day}; found {len(found[day])}")
        left=found[day][day+"1730"];right=found[day][day+"1800"]
        expected0,expected1=ANCHORS[day]
        if (left["TA_F_QC"]!="0" or right["TA_F_QC"]!="0" or
            finite(left["TA_F"]) is None or finite(right["TA_F"]) is None or
            abs(float(left["TA_F"])-expected0)>0.002 or
            abs(float(right["TA_F"])-expected1)>0.002):
            raise ValueError("Prior verified 17:30/18:00 source anchor changed "+day)
    print("FULL ORIGINAL SOURCE VERIFIED",got,"original_rows",n)
    print("EXACTLY SIX FULL LOCAL-STANDARD DAYS, 288 NATIVE HH, 00:00–23:30 EACH")
    return found

def summary(day,rows):
    records=[rows[day+f"{h:02d}{m:02d}"] for h in range(24) for m in (0,30)]
    obs=[finite(r["TA_F"]) for r in records]
    orig=[(float(r["TA_F"]),r["TIMESTAMP_START"][-4:])
          for r in records if finite(r["TA_F"]) is not None]
    era=[finite(r["TA_ERA"]) for r in records]
    valid=sum(t is not None for t in obs)
    z=[t-e for t,e in zip(obs,era) if t is not None and e is not None]
    qc={}
    for r in records:qc[r["TA_F_QC"]]=qc.get(r["TA_F_QC"],0)+1
    abnormal=sum(t is not None and e is not None and r["TA_F_QC"]=="0" and t-e<=-10
                 for t,e,r in zip(obs,era,records))
    jump=finite(rows[day+"1800"]["TA_F"])-finite(rows[day+"1730"]["TA_F"])
    print(f"DAY SUMMARY {day} valid_T_HH={valid}/48 TA_QC_counts={qc} "
          f"min_T={min(orig)[0]:.3f} max_T={max(orig)[0]:.3f} "
          f"QC0_halfhours_T_minus_ERA_le_-10C={abnormal} jump_1730_to_1800={jump:+.3f}C")
    return records

def show(found):
    print("\nKEY: TA_F and TA_ERA degrees Celsius; VPD_F hPa; QC0 direct OBS, QC1 MDS fill, QC2 ERA fill")
    print("IMPORTANT: Source TA_ERA is FLUXNET processed ERA, NOT a second tower sensor")
    for day in DATES:
        records=summary(day,found[day])
        print("\n"+"="*88)
        print("ORIGINAL FULL DAY",day,"00:00–23:30 48 HH ALL TIMES IN LOCAL STANDARD TIME (UTC−05)")
        print("TIME     TA_F    TA_QC  TA_F_MDS MDS_QC  TA_ERA    T-ERA   VPD_F  VPD_QC")
        for r in records:
            t=finite(r["TA_F"]);e=finite(r["TA_ERA"])
            diff=t-e if t is not None and e is not None else None
            fmt=lambda x: f"{x:8.3f}" if x is not None else "      NA"
            print(r["TIMESTAMP_START"][-4:],
                  fmt(t),f"{r['TA_F_QC']:>6}",fmt(finite(r["TA_F_MDS"])),
                  f"{r['TA_F_MDS_QC']:>6}",fmt(e),fmt(diff),
                  fmt(finite(r["VPD_F"])),f"{r['VPD_F_QC']:>6}")
        print("END FULL DAY",day)
    print("\nSIX-DAY FULL SOURCE READ ONLY COMPLETE 288/288 HH, no original/forcing/model edits")

def svg_poly(rows,key,w=770,h=240):
    vals=[finite(r[key]) for r in rows]
    pairs=[(i,v) for i,v in enumerate(vals) if v is not None]
    if not pairs:return ""
    allx=[]
    for col in ("TA_F","TA_ERA"):
        allx.extend(finite(r[col]) for r in rows if finite(r[col]) is not None)
    mn=min(allx)-2;mx=max(allx)+2
    left=55;right=w-22;top=16;bottom=h-30
    x=lambda i:left+(right-left)*i/47
    y=lambda v:bottom-(v-mn)/(mx-mn)*(bottom-top)
    return " ".join(f"{x(i):.1f},{y(v):.1f}" for i,v in pairs)

def plot_svg(rows):
    w,h=770,240
    yvals=[finite(r[c]) for r in rows for c in ("TA_F","TA_ERA")]
    yvals=[v for v in yvals if v is not None]
    mn=min(yvals)-2;mx=max(yvals)+2
    left=55;right=w-22;top=16;bottom=h-30
    y=lambda v:bottom-(v-mn)/(mx-mn)*(bottom-top)
    x=lambda i:left+(right-left)*i/47
    elems=[f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="Original tower temperature and FLUXNET ERA hourly timeline">']
    for i in (0,12,24,36,47):
        hr=f"{i//2:02d}:{(i%2)*30:02d}"
        elems.append(f'<text x="{x(i):.1f}" y="{h-6}" font-size="12" text-anchor="middle" fill="#666">{hr}</text>')
    for j in range(5):
        val=mn+(mx-mn)*j/4
        yi=y(val)
        elems.append(f'<line x1="{left}" x2="{right}" y1="{yi:.1f}" y2="{yi:.1f}" stroke="#ddd"/>')
        elems.append(f'<text x="{left-6}" y="{yi+4:.1f}" font-size="12" text-anchor="end" fill="#666">{val:.0f}°</text>')
    for col,color in (("TA_F","#1464b4"),("TA_ERA","#d15b25")):
        vals=[finite(r[col]) for r in rows]
        pts=[(i,v) for i,v in enumerate(vals) if v is not None]
        segments=[];cur=[];prev=-2
        for i,v in pts:
            if i!=prev+1 and cur:segments.append(cur);cur=[]
            cur.append((i,v));prev=i
        if cur:segments.append(cur)
        for part in segments:
            coords=" ".join(f"{x(i):.2f},{y(v):.2f}" for i,v in part)
            elems.append(f'<polyline points="{coords}" stroke="{color}" fill="none" stroke-width="2.2"/>')
    idx=36 # 18:00: 36 half-hours from midnight
    elems.append(f'<line x1="{x(idx):.1f}" x2="{x(idx):.1f}" y1="{top}" y2="{bottom}" stroke="#777" stroke-dasharray="4,4"/>')
    elems.append('</svg>')
    return "".join(elems)

def report(found):
    OUTPUT.mkdir(parents=True,exist_ok=True)
    outcsv=OUTPUT/"US-SP1_original_6_full_days_2007Oct15_18_22_23_TA_ERA_QC.csv"
    outhtml=OUTPUT/"US-SP1_original_6_full_days_2007Oct15_18_22_23_visual_review.html"
    headers=list(NEEDED)+["TA_minus_TA_ERA_C"]
    with outcsv.open("x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=headers);writer.writeheader()
        for day in DATES:
            for k in sorted(found[day]):
                r=found[day][k];t=finite(r["TA_F"]);e=finite(r["TA_ERA"])
                writer.writerow({**r,"TA_minus_TA_ERA_C":f"{t-e:.6f}" if t is not None and e is not None else ""})
    cards=[]
    for day in DATES:
        r=[found[day][k] for k in sorted(found[day])]
        lines=[]
        for x in r:
            t=finite(x["TA_F"]);e=finite(x["TA_ERA"])
            delta=f"{t-e:+.3f}" if t is not None and e is not None else "NA"
            style=' class="flag"' if t is not None and e is not None and t-e<=-10 and x["TA_F_QC"]=="0" else ""
            fields=[x["TIMESTAMP_START"][-4:],x["TA_F"],x["TA_F_QC"],x["TA_ERA"],delta,x["TA_F_MDS"],x["TA_F_MDS_QC"],x["VPD_F"],x["VPD_F_QC"]]
            lines.append("<tr"+style+">"+"".join("<td>"+html.escape(v)+"</td>" for v in fields)+"</tr>")
        jump=finite(found[day][day+"1800"]["TA_F"])-finite(found[day][day+"1730"]["TA_F"])
        cards.append(f'<section><h2>{day[:4]}-{day[4:6]}-{day[6:]}</h2>'
          f'<p>Original QC0 17:30 → 18:00: <b>{jump:+.3f}°C</b></p>{plot_svg(r)}'
          '<p><span style="color:#1464b4">━━</span> Tower TA_F | <span style="color:#d15b25">━━</span> TA_ERA (processed) | dashed: 18:00</p>'
          '<table><thead><tr><th>Time</th><th>TA_F°C</th><th>TA_QC</th>'
          '<th>TA_ERA°C</th><th>ΔT°C</th><th>TA_F_MDS°C</th><th>MDS_QC</th><th>VPD hPa</th><th>VPD_QC</th></tr></thead>'
          '<tbody>'+"".join(lines)+'</tbody></table></section>')
    page='''<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>US-SP1 Six Full Days Original Temperature</title>
<style>body{font:15px system-ui,sans-serif;max-width:1000px;margin:25px auto;padding:0 15px;color:#242424}
section{margin:25px 0 48px;padding:15px;border:1px solid #ddd;border-radius:12px}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums;font-size:13px}
th,td{padding:4px 8px;border-bottom:1px solid #eee;text-align:right}
th:first-child,td:first-child{text-align:left}.flag{background:#fff0d4}thead{background:#f0f0f0}
h1{margin-bottom:6px}p{line-height:1.5}svg{max-width:100%;height:auto}</style></head><body>
<h1>US-SP1 | Six complete 24-hour original temperature records</h1>
<p>2007-10-15–18 and 2007-10-22–23. 48 half-hours/day, native local standard time (UTC−05). 
Original FLUXNET FLUXMET only, SHA256 pinned. Orange background denotes QC0 tower TA at least 10°C colder than TA_ERA.
Lines: original tower TA_F and original processed FLUXNET TA_ERA; TA_ERA is not a second observed tower sensor.
No science repairs applied.</p>'''+ "".join(cards) + "</body></html>"
    outhtml.write_text(page,encoding="utf-8")
    print("SIX-DAY HUMAN REVIEW CSV",outcsv)
    print("SIX-DAY HUMAN REVIEW HTML",outhtml)
    print("SIX-DAY REPORTS WRITTEN ONLY IN USER HOME, no input/model modifications")

def selftest():
    assert len(DATES)==6 and len(ANCHORS)==6 and len(ORIGINAL_SHA)==64
    assert sum(b-a>=10 for a,b in ANCHORS.values())==6
    assert len(set(DATES))==6
    assert finite("-9999") is None and finite("11.150")==11.15
    print("SP1 SIX COMPLETE DAYS SELF-TEST PASS: SHA, 6x48 HH, six original 18h anchors, report-only")
def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--inspect",action="store_true")
    g.add_argument("--report",action="store_true")
    args=p.parse_args()
    selftest()
    if args.self_test:return
    found=read_original()
    show(found)
    if args.report:report(found)
if __name__=="__main__":main()

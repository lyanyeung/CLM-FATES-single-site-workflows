#!/usr/bin/env python3
"""Batch05 Stage23: five HOLD windows + four large VPD edges, original tower/ERA.

Source: original SHA-verified Stage18 context and executed Stage22 reports.
These are not independent ERA5-Land data. Produces ONE human decision dossier,
CSV of four edge source values + explicitly hypothetical neighbor replacements,
and HOLD summary, without editing forcing, source data, QC, model, or Slurm.
"""
import argparse,csv,json,math
from collections import Counter
from datetime import datetime,timedelta
from pathlib import Path

HOLDS=(
 ("H01_Vcm_Dec2007","US-Vcm","200712152100","200712160600",19),
 ("H02_Vcm_Feb2008","US-Vcm","200802060130","200802060800",12),
 ("H03_Vcm_Dec2008","US-Vcm","200812272100","200812272130",2),
 ("H04_Vcm_Dec2015","US-Vcm","201512060430","201512060930",10),
 ("H05_Vcp_Jan2011","US-Vcp","201101010700","201101010800",3),
)
ORIG={"site","time_native","is_P1","TA_F_C","VPD_F_hPa","RH_original_pct",
      "TA_F_QC","VPD_F_QC","TA_ERA_C","VPD_ERA_hPa",
      "ERA_RH_Magnus_water_pct","TA_MDS_C","VPD_MDS_hPa"}
CHANGE={"site","native_time","modified_RH_pct","modified_VPD_hPa"}
HOLD={"site","native_time","hold_reason"}
EDGE={"site","start_native","end_native","jump_VPD_hPa","over_4hPa_30min",
      "explicitly_held_for_manual_review"}
COLUMNS=("time_native","phase","TA_F_C","TA_F_QC","VPD_F_hPa",
         "VPD_F_QC","RH_original_pct","RH_Magnus_pct",
         "TA_ERA_C","VPD_ERA_hPa","ERA_RH_Magnus_pct",
         "TA_MDS_C","VPD_MDS_hPa","selected_VPD_hPa",
         "possible_neighbor_ERA_RH_pct","possible_neighbor_VPD_on_selected_T_hPa")
EDGE_COLS=("boundary","site","native_time","phase",
           "TA_F_C","TA_F_QC","VPD_F_hPa","VPD_F_QC","RH_original_pct",
           "TA_ERA_C","VPD_ERA_hPa","ERA_RH_Magnus_pct",
           "selected_RH_pct","selected_VPD_hPa",
           "possible_neighbor_ERA_RH_pct","possible_neighbor_VPD_on_selected_T_hPa",
           "is_approved_overlay","manual_decision")
def n(s):
 try:
  x=float(s)
  if math.isfinite(x) and x not in (-9999.,-6999.):return x
 except (TypeError,ValueError):pass
 return None
def es(t):
 if t is None or not -80<=t<=60:return None
 return 6.112*math.exp(17.67*t/(243.5+t))
def dt(s):
 if len(s)!=12 or not s.isdigit():raise ValueError("native HH clock malformed: "+repr(s))
 return datetime.strptime(s,"%Y%m%d%H%M")
def stamp(d):return d.strftime("%Y%m%d%H%M")
def read(path,need):
 if not path.is_file() or path.is_symlink():raise ValueError("source report absent "+str(path))
 with path.open(encoding="utf-8-sig",newline="") as f:
  dr=csv.DictReader(f)
  if not need.issubset(dr.fieldnames or []) or len(set(dr.fieldnames or []))!=len(dr.fieldnames or []):
   raise ValueError("invalid report columns "+str(path))
  rows=list(dr)
 if any(None in r or any(v is None for v in r.values()) for r in rows):
  raise ValueError("malformed report rows")
 return rows
def ix(rows,tcol):
 m={}
 for r in rows:
  key=(r["site"],r[tcol])
  dt(key[1])
  if key in m:raise ValueError("duplicate original source half-hour "+str(key))
  m[key]=r
 return m
def load(d18,d22):
 meta18=json.loads((d18/"stage18_summary.json").read_text())
 meta22=json.loads((d22/"stage22_manifest.json").read_text())
 if (meta18.get("P1_original_HH"),meta18.get("context_rows"))!=(176,775):
  raise ValueError("original Stage18 cohort drift")
 if (meta22.get("approved_modified_RH_VPD_native_half_hours"),
     meta22.get("hold_original_P1_half_hours"),meta22.get("DATM_forcing_written"))!=(162,46,False):
  raise ValueError("Stage22 revision/count/forcing status mismatch")
 o=ix(read(d18/"stage18_all_p1_original_6hour_context.csv",ORIG),"time_native")
 edits=ix(read(d22/"stage22_VERSIONED_APPROVED_RH_VPD_native_overlay.csv",CHANGE),"native_time")
 hold=ix(read(d22/"stage22_46_MANUAL_HOLD_P1_untouched.csv",HOLD),"native_time")
 edges=read(d22/"stage22_all_overlay_boundary_transitions.csv",EDGE)
 if len(o)!=775 or len(edits)!=162 or len(hold)!=46 or len(edges)!=60:
  raise ValueError("source report exact populations unexpectedly changed")
 if not set(edits).issubset(o) or not set(hold).issubset(o) or set(edits)&set(hold):
  raise ValueError("HOLD/overlay provenance conflict")
 bad=[r for r in edges if abs(float(r["jump_VPD_hPa"]))>4]
 if len(bad)!=4:raise ValueError("expected exactly four Stage22 large edge jumps")
 for g,site,a,b,count in HOLDS:
  matches=[k for k in hold if k[0]==site and a<=k[1]<=b]
  if len(matches)!=count:raise ValueError("HOLD five group population change "+g+" "+str(len(matches)))
 return o,edits,hold,edges,bad
def hypothetical(r):
 tf=n(r["TA_F_C"])
 rh=n(r["ERA_RH_Magnus_water_pct"])
 sa=es(tf)
 if rh is None or sa is None or not 0<=rh<=100:return None,None
 return rh,sa*(1-rh/100)
def viewrow(r,phase,edits):
 k=r["site"],r["time_native"]
 e=edits.get(k)
 hypRH,hypV=hypothetical(r)
 return dict(
  time_native=r["time_native"],phase=phase,
  TA_F_C=r["TA_F_C"],TA_F_QC=r["TA_F_QC"],
  VPD_F_hPa=r["VPD_F_hPa"],VPD_F_QC=r["VPD_F_QC"],
  RH_original_pct=r["RH_original_pct"],
  RH_Magnus_pct=r.get("RH_Magnus_water_pct",""),
  TA_ERA_C=r["TA_ERA_C"],VPD_ERA_hPa=r["VPD_ERA_hPa"],
  ERA_RH_Magnus_pct=r["ERA_RH_Magnus_water_pct"],
  TA_MDS_C=r["TA_MDS_C"],VPD_MDS_hPa=r["VPD_MDS_hPa"],
  selected_VPD_hPa=e["modified_VPD_hPa"] if e else r["VPD_F_hPa"],
  possible_neighbor_ERA_RH_pct=(round(hypRH,6) if hypRH is not None else ""),
  possible_neighbor_VPD_on_selected_T_hPa=(round(hypV,6) if hypV is not None else ""),
 )
def table(rows,cols):
 text=["| "+" | ".join(cols)+" |","| "+" | ".join("---" for _ in cols)+" |"]
 for r in rows:
  text.append("| "+" | ".join(str(r.get(c,"")).replace("|","/") for c in cols)+" |")
 return "\n".join(text)
def window(orig,site,a,b,pad_h=3):
 lo=dt(a)-timedelta(hours=pad_h)
 hi=dt(b)+timedelta(hours=pad_h)
 return [r for (s,t),r in sorted(orig.items()) if s==site and lo<=dt(t)<=hi]
def dossier(orig,edits,holds,bad):
 sections=[
 "# Stage23 — 46 human HOLD (five windows) and four VPD boundaries",
 "",
 "**Only actual original SHA-audited FLUXMET records and Stage22 overlay are included.**",
 "QC0 = original tower measurement, QC1 = MDS-selected, QC2 = processed ERA-selected.",
 "The ERA_T/ERA_VPD fields below are original processed ERA columns, **NOT new ERA5/ERA5-Land data**.",
 "ERA-derived RH is computed via source TA_ERA/VPD_ERA, not independently observed RH.",
 "Potential neighboring ERA RH/VPD alternatives are **hypothetical and NEVER approved or written**.",
 "All times are original native printed tower timestamps, NOT inferred UTC.",
 "",
 "## Five manual HOLD windows (each with ±3 h source context)",
 ""
 ]
 counts={}
 for group,site,a,b,expected in HOLDS:
  holdkeys={k for k in holds if k[0]==site and a<=k[1]<=b}
  items=window(orig,site,a,b)
  present={r["time_native"] for r in items}
  if not {k[1] for k in holdkeys}.issubset(present):
   raise ValueError("HOLD missing native source context "+group)
  rows=[viewrow(r,"MANUAL_HOLD" if (site,r["time_native"]) in holdkeys else
                   ("PRE_HOLD" if r["time_native"]<a else
                    "POST_HOLD" if r["time_native"]>b else
                    "INTERNAL_CONTEXT"),edits) for r in items]
  counts[group]=dict(held=len(holdkeys),context=len(rows),
    source_RH_nonmissing=sum(n(orig[k]["RH_original_pct"]) is not None for k in holdkeys),
    era_RH_min=min((n(orig[k]["ERA_RH_Magnus_water_pct"]) for k in holdkeys if n(orig[k]["ERA_RH_Magnus_water_pct"]) is not None),default=None),
    era_RH_max=max((n(orig[k]["ERA_RH_Magnus_water_pct"]) for k in holdkeys if n(orig[k]["ERA_RH_Magnus_water_pct"]) is not None),default=None))
  sections += [
    "### "+group+" — "+str(expected)+" HOLD half-hours",
    "Native time window "+a+" to "+b+"; original ±3h context",
    "Original RH present in HOLD: "+str(counts[group]["source_RH_nonmissing"])+"/"+str(expected),
    "ERA-derived RH min/max in HOLD: "+str(counts[group]["era_RH_min"])+"/"+str(counts[group]["era_RH_max"]),
    "",
    table(rows,COLUMNS),"",
    "**Human decision:** [ ] retain HOLD / [ ] use an independently verified weather reference / [ ] approve a specified repair source",
    "**Source provenance and exact decision interval:** __________",""
  ]
 sections += ["## Four significant Stage22 overlay boundaries (±3 h original context)",""]
 edge_rows=[]
 for i,e in enumerate(bad,1):
  site,a,b=e["site"],e["start_native"],e["end_native"]
  group="E{:02d}_{}_{}_{}".format(i,site,a,b)
  items=window(orig,site,a,b)
  ks={(site,a),(site,b)}
  if not ks.issubset(orig):raise ValueError("original boundary source points absent "+group)
  rows=[]
  for r in items:
   phase=("BOUNDARY_START" if r["time_native"]==a else
          "BOUNDARY_END" if r["time_native"]==b else "CONTEXT")
   rows.append(viewrow(r,phase,edits))
   hypRH,hypV=hypothetical(r)
   edge_rows.append(dict(
    boundary=group,site=site,native_time=r["time_native"],phase=phase,
    TA_F_C=r["TA_F_C"],TA_F_QC=r["TA_F_QC"],
    VPD_F_hPa=r["VPD_F_hPa"],VPD_F_QC=r["VPD_F_QC"],
    RH_original_pct=r["RH_original_pct"],
    TA_ERA_C=r["TA_ERA_C"],VPD_ERA_hPa=r["VPD_ERA_hPa"],
    ERA_RH_Magnus_pct=r["ERA_RH_Magnus_water_pct"],
    selected_RH_pct=(edits[site,r["time_native"]]["modified_RH_pct"]
                     if (site,r["time_native"]) in edits else r["RH_original_pct"]),
    selected_VPD_hPa=(edits[site,r["time_native"]]["modified_VPD_hPa"]
                      if (site,r["time_native"]) in edits else r["VPD_F_hPa"]),
    possible_neighbor_ERA_RH_pct=round(hypRH,6) if hypRH is not None else "",
    possible_neighbor_VPD_on_selected_T_hPa=round(hypV,6) if hypV is not None else "",
    is_approved_overlay=int((site,r["time_native"]) in edits),
    manual_decision="NOT_APPROVED_FOR_EDGE_EXPANSION"
   ))
  sections += ["### "+group,
    "Original boundary "+a+" → "+b+"; reconstructed VPD jump "+e["jump_VPD_hPa"]+" hPa",
    "Previously tagged manual: "+str(e["explicitly_held_for_manual_review"]),
    "",table(rows,COLUMNS),"",
    "**Human decision for the UNEDITED neighbor:** [ ] retain original / [ ] change to matched ERA-derived RH using selected original T / [ ] HOLD independent",
    "**Do not apply any proposed neighbor values without explicit approval.**",""]
 return "\n".join(sections),counts,edge_rows
def writetable(path,headers,rows):
 with path.open("x",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=headers);w.writeheader();w.writerows(rows)
def selftest():
 assert sum(x[4] for x in HOLDS)==46
 assert len(HOLDS)==5
 assert abs(es(-14)*(1-80/100)-0.414)<0.1
 print("STAGE23 SELF-TEST PASS | 46 holds in 5 groups, edge screen provenance; no original writes")
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--stage18-dir",type=Path)
 p.add_argument("--stage22-dir",type=Path)
 p.add_argument("--out",type=Path)
 a=p.parse_args()
 if a.self_test:selftest();return
 if any(x is None for x in (a.stage18_dir,a.stage22_dir,a.out)):
  p.error("--stage18-dir --stage22-dir --out required")
 d18=a.stage18_dir.expanduser().resolve()
 d22=a.stage22_dir.expanduser().resolve()
 out=a.out.expanduser().resolve()
 if not d18.is_dir() or not d22.is_dir() or not out.parent.is_dir() or out.exists() or any(
    out==v or out in v.parents or v in out.parents for v in (d18,d22)):
  p.error("new separate output folder and two existing original report dirs required")
 orig,edits,holds,edges,bad=load(d18,d22)
 doc,counts,edge_rows=dossier(orig,edits,holds,bad)
 out.mkdir(exist_ok=False)
 (out/"stage23_five_holds_and_four_edges_full_review.md").write_text(doc,encoding="utf-8")
 writetable(out/"stage23_four_edges_original_ERA_hypothetical.csv",EDGE_COLS,edge_rows)
 (out/"stage23_review_summary.json").write_text(json.dumps(dict(
  holds=46,hold_groups=counts,approved_overlay_unchanged=162,
  significant_boundaries=4,edge_review_rows=len(edge_rows),
  modified_original=False,modified_DATM=False,submitted_Slurm=False,
  independent_ERA5_downloaded=False),indent=2,sort_keys=True),encoding="utf-8")
 print("STAGE23 SOURCE_AND_COHORT_VERIFIED Stage18=775 HH Stage22_overlay=162 HOLD=46")
 for g,s,a,b,count in HOLDS:
  c=counts[g]
  print("STAGE23 HOLD_GROUP",g,"HOLD_HH",count,
        "RH_SOURCE_PRESENT",c["source_RH_nonmissing"],
        "ERA_RH_MIN",c["era_RH_min"],"ERA_RH_MAX",c["era_RH_max"],
        "CONTEXT_HH",c["context"],flush=True)
 for e in bad:
  print("STAGE23 EDGE",e["site"],e["start_native"],e["end_native"],
        "VPD_JUMP",e["jump_VPD_hPa"],
        "EXPLICIT_USER_REVIEW",e["explicitly_held_for_manual_review"],flush=True)
 print("STAGE23_HUMAN_REVIEW="+str(out/"stage23_five_holds_and_four_edges_full_review.md"))
 print("STAGE23 SUCCESS | FIVE HOLD WINDOW TABLES / FOUR EDGE TABLES; NO ORIGINAL / FORCING / SLURM WRITES")
if __name__=="__main__":
 main()

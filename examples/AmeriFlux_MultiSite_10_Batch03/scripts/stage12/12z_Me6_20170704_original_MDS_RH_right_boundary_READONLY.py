#!/usr/bin/env python3
"""Original US-Me6 2017-07-04 source-only MDS/VPD/RH boundary audit.
The 08:00 original VPD_F_QC=1, not observed QC0. Audit original tower T,
MDS QC, paired native ERA, 2017 whole-year nearest measured QC0 humidity,
source-native +/-6h and immutable Stage12c/d/e/g provenance. --check
writes nothing; --run writes only a separate SHA-receipted science report.
"""
import argparse,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=R/"qcv5_native_trial_20261022T024559Z_36c46e58"
Y=R/"reports/stage12y_13_G_grid_provenance_and_Me6_20170704_bridge_20261025T194355Z_461ff1e4"
STAGES={
"C":("stage12c_six_site_noleap_hold_shadows_20261024T120618Z_f369a05e","stage12c_research_shadow_SHA_receipt.json","STAGE12C_NOT_MODEL_READY_NOLEAP"),
"D":("stage12d_six_site_companion_RH_gap_recovery_20261024T121810Z_f1fa4cee","stage12d_research_shadow_SHA_receipt.json","STAGE12D_NOT_MODEL_READY_NOLEAP"),
"E":("stage12e_six_site_verified_yearly_gridRH_shadows_20261024T123527Z_1d117b97","stage12e_research_only_sha_receipt.json","STAGE12E_INCOMPLETE_NOLEAP"),
"G":("stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f","stage12g_research_only_sha_receipt.json","STAGE12G_INCOMPLETE_NOLEAP")}
KEYS=["201707040630","201707040700","201707040730","201707040800"]
VERSION="batch03-stage12z-v1-20261025-original-Me6-0800-MDS-QC1-water-RH"
def safe(p):
 p=Path(p)
 if not p.is_file() or p.is_symlink():raise ValueError("Missing/symlinked source: "+str(p))
 return p
def sha(p):
 h=hashlib.sha256()
 with safe(p).open("rb") as f:
  for x in iter(lambda:f.read(1048576),b""):h.update(x)
 return h.hexdigest()
def es(t):
 t=np.asarray(t,dtype=float)
 with np.errstate(invalid="ignore",divide="ignore",over="ignore"):
  return 6.112*np.exp(17.67*t/(t+243.5))
def selftest():
 ts=pd.to_datetime(KEYS,format="%Y%m%d%H%M").to_numpy()
 assert (np.diff(ts).astype("timedelta64[m]").astype(int)==30).all()
 assert abs(float(es(18.96))-21.9052737697)<1e-6
 print("STAGE12Z SELF-TEST PASS: 30min original native times, water saturation; NO WRITES",flush=True)
def input_data():
 yr=json.loads(safe(Y/"stage12y_grid_bridge_science_SHA_receipt.json").read_text())
 if yr.get("version")!="batch03-stage12y-v2-20261025-two-gap-and-13-G-grid-ledger-locked" or yr.get("new_repairs")!=0 or yr.get("original_86_plus_233_science_holds_preserved") is not True:
  raise ValueError("Original sealed Stage12y source science receipt changed")
 for n,d in yr["output_SHA256"].items():
  if sha(Y/n)!=d:raise ValueError("Stage12y output checksum changed "+n)
 m=json.loads(safe(S07/"exact_input_manifest.json").read_text())
 specs={r["site"]:r for r in m["sites"]}
 s=specs["US-Me6"]
 digests={str(Path(k).resolve()):v for k,v in m["input_sha256"].items()}
 for f in ("primary","era"):
  p=safe(s[f])
  if sha(p)!=digests.get(str(p.resolve())):raise ValueError("Original FLUXMET/native ERA SHA mismatch")
 raw=["TIMESTAMP_START","TA_F","TA_F_QC","TA_F_MDS","TA_F_MDS_QC","VPD_F","VPD_F_QC","VPD_F_MDS","VPD_F_MDS_QC"]
 e=["TIMESTAMP_START","TA_ERA","VPD_ERA"]
 a=pd.read_csv(s["primary"],usecols=raw,dtype={"TIMESTAMP_START":str},low_memory=False)
 b=pd.read_csv(s["era"],usecols=e,dtype={"TIMESTAMP_START":str},low_memory=False)
 a=a.loc[a.TIMESTAMP_START.str.startswith("2017")].copy()
 b=b.loc[b.TIMESTAMP_START.str.startswith("2017")].copy()
 a.sort_values("TIMESTAMP_START",inplace=True);b.sort_values("TIMESTAMP_START",inplace=True)
 a.reset_index(drop=True,inplace=True);b.reset_index(drop=True,inplace=True)
 if len(a)!=17520 or len(b)!=17520 or not a.TIMESTAMP_START.equals(b.TIMESTAMP_START):
  raise ValueError("Original 2017 source native record sequence changed")
 x=a.merge(b,on="TIMESTAMP_START",validate="one_to_one")
 for f in raw[1:]+e[1:]:x[f]=pd.to_numeric(x[f],errors="coerce")
 clocks=pd.to_datetime(x.TIMESTAMP_START,format="%Y%m%d%H%M")
 if clocks.iat[0]!=pd.Timestamp("2017-01-01") or clocks.iat[-1]!=pd.Timestamp("2017-12-31 23:30") or not (clocks.diff().iloc[1:]==pd.Timedelta(minutes=30)).all():
  raise ValueError("Original 2017 native clock not exact halfhour")
 x["native_time"]=clocks
 x["es_water_tower_hPa"]=es(x.TA_F)
 x["original_implied_RH_pct"]=100*(1-x.VPD_F/x.es_water_tower_hPa)
 x["original_QC0_T_and_VPD_physical"]=x.TA_F_QC.eq(0)&x.VPD_F_QC.eq(0)&x.VPD_F.ge(0)&x.VPD_F.lt(x.es_water_tower_hPa)
 x["ERA_RH_pct"]=100*(1-x.VPD_ERA/es(x.TA_ERA))
 x["companion_ERA_RH_at_tower_T_VPD_hPa"]=x.es_water_tower_hPa*(1-x.ERA_RH_pct/100)
 x["VPD_F_equals_MDS"]=x.VPD_F.sub(x.VPD_F_MDS).abs().le(1e-6)
 for letter,(dirname,receipt,kind) in STAGES.items():
  folder=R/"science_trials"/dirname
  r=json.loads(safe(folder/receipt).read_text())
  if any(r.get(k)!=0 for k in ("Postv5_approved","DATM_ready","spinup_authorized")) or r.get("INCOMPLETE_marker_present") is not True:
   raise ValueError("Stage12"+letter+" research gate changed")
  filename="US-Me6_"+kind+".csv"
  if sha(folder/filename)!=r.get("output_sha256",{}).get(filename):raise ValueError("Stage12"+letter+" shadow SHA changed")
  y=pd.read_csv(folder/filename,usecols=["time","VPD_USE","TA_USE","PSRF"],dtype={"time":str},low_memory=False)
  y["TIMESTAMP_START"]=y.time.str.replace(r"[^0-9]","",regex=True).str.slice(0,12)
  y=y.loc[y.TIMESTAMP_START.str.startswith("2017")].copy()
  y.sort_values("TIMESTAMP_START",inplace=True);y.reset_index(drop=True,inplace=True)
  if len(y)!=17520 or not x.TIMESTAMP_START.equals(y.TIMESTAMP_START):
   raise ValueError("Stage12"+letter+" native original clock mismatch")
  x["Stage12"+letter+"_VPD_hPa"]=pd.to_numeric(y.VPD_USE,errors="coerce")
  if not np.allclose(x.loc[x.TA_F_QC.eq(0),"TA_F"],pd.to_numeric(y.TA_USE,errors="coerce").loc[x.TA_F_QC.eq(0)],atol=1e-7,rtol=0):
   raise ValueError("Stage12"+letter+" original QC0 temperature changed")
 if sha(R/"science_trials"/STAGES["G"][0]/STAGES["G"][1])!=yr.get("stage12g_source_receipt_SHA256"):
  raise ValueError("Stage12y Stage12g lineage changed")
 return x
def audit():
 x=input_data()
 focal=x.loc[x.TIMESTAMP_START.isin(KEYS)].copy()
 focal=focal.set_index("TIMESTAMP_START").loc[KEYS].reset_index()
 if not focal.VPD_F_QC.eq(1).all() or not focal.TA_F_QC.eq(0).all() or not focal.VPD_F_equals_MDS.all() or not focal.VPD_F_MDS_QC.eq(1).all():
  raise ValueError("Original 4-point source QC1 MDS evidence changed")
 if not (focal["Stage12G_VPD_hPa"].iloc[1:3].isna().all() and abs(focal["Stage12G_VPD_hPa"].iloc[3]-21.391)<1e-6):
  raise ValueError("Two original G held and 08:00 retained VPD source changed")
 center=pd.Timestamp("2017-07-04 07:30")
 context=x.loc[(x.native_time-center).abs()<=pd.Timedelta(hours=6)].copy()
 day=x.loc[x.native_time.dt.date==center.date()].copy()
 anchors=x.loc[x.original_QC0_T_and_VPD_physical].copy()
 anchors["minutes_from_0730"]=(anchors.native_time-center).dt.total_seconds()/60
 anchors["absolute_minutes"]=anchors.minutes_from_0730.abs()
 anchors.sort_values("absolute_minutes",inplace=True)
 within24=int(anchors.absolute_minutes.le(1440).sum())
 if len(context)!=25 or len(day)!=48 or within24!=0:
  raise ValueError("Signed 25-context/48 day/zero-QC0-within24 provenance changed")
 return focal,context,day,anchors
def main():
 p=argparse.ArgumentParser()
 g=p.add_mutually_exclusive_group(required=True)
 for a in ("self-test","check","run"):g.add_argument("--"+a,action="store_true")
 args=p.parse_args()
 print("STAGE12Z — ORIGINAL 08:00 MDS QC1 RIGHT BOUNDARY, RH & QC0 SOURCE | "+VERSION,flush=True)
 selftest()
 if args.self_test:return
 focal,context,day,anchors=audit()
 cols=["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC","VPD_F_MDS","TA_F_MDS","original_implied_RH_pct","ERA_RH_pct","companion_ERA_RH_at_tower_T_VPD_hPa","Stage12C_VPD_hPa","Stage12D_VPD_hPa","Stage12E_VPD_hPa","Stage12G_VPD_hPa"]
 print("\n========== ORIGINAL FOUR NATIVE SOURCE + C/D/E/G 08:00 HISTORY ==========",flush=True)
 print(focal[cols].to_string(index=False),flush=True)
 print("\n========== NEAREST REAL ORIGINAL QC0 PHYSICAL VPD+TA REFERENCES IN 2017 ==========",flush=True)
 print(anchors[["TIMESTAMP_START","minutes_from_0730","TA_F","VPD_F"]].head(10).to_string(index=False),flush=True)
 print("\n========== ORIGINAL LOCAL 06:00–09:00 CONTEXT ==========",flush=True)
 sub=context.loc[context.native_time.between(pd.Timestamp("2017-07-04 06:00"),pd.Timestamp("2017-07-04 09:00"))]
 print(sub[["TIMESTAMP_START","TA_F","VPD_F","VPD_F_QC","original_implied_RH_pct","ERA_RH_pct","Stage12G_VPD_hPa"]].to_string(index=False),flush=True)
 print("STAGE12Z SUMMARY: measured_QC0_tower_T=TRUE source_0800_VPD_QC1_MDS=TRUE original_QC0_anchor_within24h=0 research_hold=TRUE",flush=True)
 if args.check:print("STAGE12Z CHECK: ZERO FILE WRITES",flush=True);return
 out=R/"reports"/("stage12z_0800_MDS_source_original_RH_context_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
 out.mkdir(parents=True,exist_ok=False)
 tables={"four_source_MDS_RH_G_history.csv":focal,"source_pm6h_context.csv":context,"source_full_day_20170704.csv":day,"nearest_original_QC0_VPD_2017.csv":anchors}
 for n,t in tables.items():t.to_csv(out/n,index=False)
 (out/"SCIENCE_HOLD.md").write_text("No original VPD/T/P/native clock/Stage12c-d-e-g edited. Original 86+233 science holds and 4hPa boundary guard preserved. No Post-v5/DATM/spinup release. Source 08:00 VPD QC1 MDS is not measured tower QC0.\n")
 h={n:sha(out/n) for n in [*tables,"SCIENCE_HOLD.md"]}
 (out/"stage12z_source_SHA_receipt.json").write_text(json.dumps({"version":VERSION,"source_0800_QC1_MDS":True,"original_86_plus_233_holds_preserved":True,"new_repairs":0,"Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,"output_SHA256":h},indent=2)+"\n")
 print("STAGE12Z SOURCE-ONLY REPORT DIR:",out,flush=True)
if __name__=="__main__":
 try:main()
 except Exception as exc:
  print("STAGE12Z STOP:",exc,file=sys.stderr,flush=True)
  raise SystemExit(2)

#!/usr/bin/env python3
"""Stage12aa: original US-Me6 2017-07-04 MDS QC1 -> ERA QC2 native boundary.
Read-only source, Stage12z report and signed Stage12g comparison for 06:00
to 09:00 (7 HH records, 6 exactly 30-min edges). Compare three different
sequences: original VPD_F, original Stage12g existing values (with gaps),
and a purely hypothetical same-native ERA-RH-transferred VPD at original
measured tower T (no source/clock/forcing edits). Distinguish source QC1
MDS from QC2 ERA and flag the >4hPa transitions; never auto-repair.
--self-test: only mathematical assertions, no file reads
--check: verify original SHA and report science gates; NO WRITES
--run: same and write a NEW SHA-sealed science report only
"""
import argparse,hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import numpy as np
import pandas as pd
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
S07=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
Z=ROOT/"reports/stage12z_0800_MDS_source_original_RH_context_20261025T225231Z_2b60b8d8"
G=ROOT/"science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f"
START="201707040600";END="201707040900"
VERSION="batch03-stage12aa-v1-20261025-QC1-QC2-original-native-30min-ERA-RH"
def safe(p):
 p=Path(p)
 if not p.is_file() or p.is_symlink():raise ValueError("Missing/symlinked original source "+str(p))
 return p
def sha(p):
 h=hashlib.sha256()
 with safe(p).open("rb") as f:
  for v in iter(lambda:f.read(1048576),b""):h.update(v)
 return h.hexdigest()
def es(t):
 t=np.asarray(t,dtype=float)
 with np.errstate(over="ignore",invalid="ignore",divide="ignore"):
  return 6.112*np.exp(17.67*t/(t+243.5))
def selftest():
 assert abs(float(es(18.96))-21.90527377)<1e-6
 assert abs(21.391-13.204-8.187)<1e-9
 t=pd.to_datetime(["201707040800","201707040830"],format="%Y%m%d%H%M")
 assert (t[1]-t[0])==pd.Timedelta(minutes=30)
 print("STAGE12AA SELF-TEST PASS: exact QC source boundary, 30min and humidity physics; NO WRITES",flush=True)
def verify():
 zr=json.loads(safe(Z/"stage12z_source_SHA_receipt.json").read_text())
 if zr.get("version")!="batch03-stage12z-v1-20261025-original-Me6-0800-MDS-QC1-water-RH" or zr.get("source_0800_QC1_MDS") is not True or zr.get("original_86_plus_233_holds_preserved") is not True or zr.get("new_repairs")!=0:
  raise ValueError("Stage12z original source receipt changed")
 for field in ("Postv5_approved","DATM_ready","spinup_authorized"):
  if zr.get(field)!=0:raise ValueError("Stage12z report was approved unexpectedly")
 for name,digest in zr["output_SHA256"].items():
  if sha(Z/name)!=digest:raise ValueError("Stage12z signed output SHA failed "+name)
 g=json.loads(safe(G/"stage12g_research_only_sha_receipt.json").read_text())
 if g.get("INCOMPLETE_marker_present") is not True or g.get("original_233_physics_holds_untouched") is not True:
  raise ValueError("Stage12g research science guards changed")
 for field in ("Postv5_approved","DATM_ready","spinup_authorized"):
  if g.get(field)!=0:raise ValueError("Stage12g trial approved unexpectedly")
 safe(G/"INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
 gp=G/"US-Me6_STAGE12G_INCOMPLETE_NOLEAP.csv"
 if sha(gp)!=g["output_sha256"][gp.name]:raise ValueError("Original G shadow checksum changed")
 m=json.loads(safe(S07/"exact_input_manifest.json").read_text())
 spec=next(r for r in m["sites"] if r["site"]=="US-Me6")
 pins={str(Path(k).resolve()):d for k,d in m["input_sha256"].items()}
 for field in ("primary","era"):
  f=safe(spec[field])
  if sha(f)!=pins.get(str(f.resolve())):raise ValueError("Source FLUXMET/ERA SHA mismatch")
 return spec,gp
def audit():
 spec,gfile=verify()
 cols=["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC",
       "VPD_F_MDS","VPD_F_MDS_QC","TA_F_MDS"]
 raw=pd.read_csv(spec["primary"],usecols=cols,dtype={"TIMESTAMP_START":str})
 era=pd.read_csv(spec["era"],usecols=["TIMESTAMP_START","TA_ERA","VPD_ERA"],dtype={"TIMESTAMP_START":str})
 raw=raw.loc[raw.TIMESTAMP_START.between(START,END)].copy()
 era=era.loc[era.TIMESTAMP_START.between(START,END)].copy()
 if len(raw)!=7 or len(era)!=7:raise ValueError("Original 7 exact native source rows changed")
 tab=raw.merge(era,on="TIMESTAMP_START",validate="one_to_one")
 g=pd.read_csv(gfile,usecols=["time","VPD_USE","QBOT","TA_USE","PSRF"],dtype={"time":str})
 g["TIMESTAMP_START"]=g.time.str.replace(r"[^0-9]","",regex=True).str.slice(0,12)
 g=g.loc[g.TIMESTAMP_START.between(START,END)].copy()
 tab=tab.merge(g,on="TIMESTAMP_START",validate="one_to_one").sort_values("TIMESTAMP_START").reset_index(drop=True)
 if len(tab)!=7:raise ValueError("Original 7 native Stage12g timestamps differed")
 d=pd.to_datetime(tab.TIMESTAMP_START,format="%Y%m%d%H%M")
 if not (np.diff(d.to_numpy()).astype("timedelta64[m]").astype(int)==30).all():
  raise ValueError("Original source native clock not 30min")
 for col in [*cols[1:],"TA_ERA","VPD_ERA","VPD_USE","QBOT","TA_USE","PSRF"]:
  tab[col]=pd.to_numeric(tab[col],errors="coerce")
 if not tab.TA_F_QC.eq(0).all() or not tab.TA_USE.sub(tab.TA_F).abs().le(1e-7).all():
  raise ValueError("Tower QC0 T not preserved")
 if not (tab.VPD_F_QC.iloc[:5].eq(1).all() and tab.VPD_F_QC.iloc[5:].eq(2).all()):
  raise ValueError("Original QC1->QC2 native source lineage changed")
 if not tab.VPD_F.iloc[:5].sub(tab.VPD_F_MDS.iloc[:5]).abs().le(1e-7).all():
  raise ValueError("Original QC1 MDS source changed")
 if (not np.isnan(tab.VPD_USE.iloc[2]) or not np.isnan(tab.VPD_USE.iloc[3])
     or abs(tab.VPD_USE.iloc[4]-21.391)>1e-6 or abs(tab.VPD_USE.iloc[5]-13.204)>1e-6):
  raise ValueError("Original 07:00/07:30 science holds or existing 08:00/08:30 G values changed")
 tab["tower_es_water_hPa"]=es(tab.TA_F)
 tab["original_source_implied_RH_pct"]=100*(1-tab.VPD_F/tab.tower_es_water_hPa)
 tab["source_original_VPD_physically_allowed"]=tab.VPD_F.ge(0)&tab.VPD_F.lt(tab.tower_es_water_hPa)
 tab["native_companion_ERA_RH_pct"]=100*(1-tab.VPD_ERA/es(tab.TA_ERA))
 tab["hypothetical_companion_ERA_RH_tower_T_VPD_hPa"]=tab.tower_es_water_hPa*(1-tab.native_companion_ERA_RH_pct/100)
 tab["native_companion_T_minus_original_T_C"]=tab.TA_ERA-tab.TA_F
 tab["hypothetical_companion_T_within_5C"]=tab.native_companion_T_minus_original_T_C.abs().le(5)
 tab["scenario_A_original_F_VPD_hPa"]=tab.VPD_F
 tab["scenario_B_unchanged_Stage12g_VPD_hPa"]=tab.VPD_USE
 # Purely analytical, all 7 original-native rows use their own companion ERA RH;
 # real G and original QC1/QC2 data remain unchanged.
 tab["scenario_C_all_companion_RH_referenced_VPD_hPa"]=tab.hypothetical_companion_ERA_RH_tower_T_VPD_hPa
 tab["source_or_forcing_changed"]=False
 edges=[]
 for i in range(6):
  a,b=tab.iloc[i],tab.iloc[i+1]
  record={"native_start":a.TIMESTAMP_START,"native_end":b.TIMESTAMP_START,
          "source_QC_transition":str(int(a.VPD_F_QC))+"->"+str(int(b.VPD_F_QC)),
          "native_30min_clock_exact":True,"no_stage12g_repair":True}
  for k in ("A_original_F","B_unchanged_Stage12g","C_all_companion_RH_referenced"):
   col="scenario_"+k+"_VPD_hPa"
   av,bv=float(a[col]),float(b[col])
   value=abs(bv-av) if np.isfinite(av) and np.isfinite(bv) else np.nan
   record[k+"_absolute_30min_jump_hPa"]=value
   record[k+"_over_4hPa"]=bool(np.isfinite(value) and value>4)
   record[k+"_missing_edge"]=bool(not np.isfinite(value))
  edges.append(record)
 edges=pd.DataFrame(edges)
 if (len(tab)!=7 or len(edges)!=6
    or edges.loc[edges.native_start.eq("201707040800"),
          "A_original_F_absolute_30min_jump_hPa"].iloc[0] != 8.187):
  # Float conversion from source CSV often precisely represents three decimals,
  # but use tolerance for the exact 8.187hPa expectation below.
  val=edges.loc[edges.native_start.eq("201707040800"),"A_original_F_absolute_30min_jump_hPa"].iloc[0]
  if len(tab)!=7 or len(edges)!=6 or not np.isclose(val,8.187,atol=1e-6):
   raise ValueError("Signed original QC1 to QC2 half-hour jump changed")
 return tab,edges
def main():
 p=argparse.ArgumentParser()
 s=p.add_mutually_exclusive_group(required=True)
 for op in ("self-test","check","run"):s.add_argument("--"+op,action="store_true")
 a=p.parse_args()
 print("STAGE12AA — ORIGINAL SOURCE QC1 MDS TO QC2 ERA HALF-HOUR DISCONTINUITY | "+VERSION,flush=True)
 selftest()
 if a.self_test:return
 table,edges=audit()
 print("\n========== EXACT ORIGINAL 06:00–09:00 SOURCE AND SAME-NATIVE COMPANION RH ==========",flush=True)
 print(table[["TIMESTAMP_START","TA_F","VPD_F","VPD_F_QC","original_source_implied_RH_pct","VPD_USE","hypothetical_companion_ERA_RH_tower_T_VPD_hPa","native_companion_T_minus_original_T_C"]].to_string(index=False),flush=True)
 print("\n========== SIX ACTUAL ADJACENT 30MIN EDGES; SOURCE A, EXISTING G B, HYPOTHETICAL C ==========",flush=True)
 print(edges.to_string(index=False),flush=True)
 print("\nSTAGE12AA SUMMARY: source_0800_QC1_to_0830_QC2=TRUE "
       "original_0700_and_0730_holds_unchanged=TRUE original_86_plus_233_holds=TRUE "
       "source_repairs=0 Postv5=0 DATM=0 spinup=0",flush=True)
 if a.check:
  print("STAGE12AA CHECK ONLY: ZERO SOURCE, REPORT OR MODEL WRITES.",flush=True)
  return
 out=ROOT/"reports"/("stage12aa_20170704_original_QC1_QC2_native_ERA_RH_"+
     datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
 out.mkdir(parents=True,exist_ok=False)
 tables={"seven_original_native_QC1_QC2_RH_and_three_scenarios.csv":table,
         "six_original_native_30min_stage12aa_source_edges.csv":edges}
 for n,t in tables.items():t.to_csv(out/n,index=False)
 (out/"SCIENCE_HOLD.md").write_text("Seven original native source records QC1 MDS -> QC2 ERA examined. Third scenario is a hypothetical source comparison ONLY. Original 86+233 science holds, original 08:00 Stage12g finite value, 07:00/07:30 science gaps, T/P/native clock and 4hPa halfhour threshold remain unchanged. No Postv5/DATM/spinup approvals.\n")
 dig={k:sha(out/k) for k in [*tables,"SCIENCE_HOLD.md"]}
 (out/"stage12aa_readonly_SHA_receipt.json").write_text(json.dumps({"version":VERSION,"original_stage12z_SHA256":sha(Z/"stage12z_source_SHA_receipt.json"),"original_86_plus_233_science_holds_preserved":True,"new_repairs":0,"Postv5_approved":0,"DATM_ready":0,"spinup_authorized":0,"output_SHA256":dig},indent=2)+"\n")
 print("STAGE12AA SOURCE-ONLY SCIENCE REPORT DIR:",out,flush=True)
if __name__=="__main__":
 try:main()
 except Exception as exc:
  print("STAGE12AA STOP:",exc,file=sys.stderr,flush=True)
  raise SystemExit(2)

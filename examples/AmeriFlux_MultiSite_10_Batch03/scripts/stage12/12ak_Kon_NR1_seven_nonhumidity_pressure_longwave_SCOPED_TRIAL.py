#!/usr/bin/env python3
"""Stage12ak: 7 native half-hours / 8 original bad non-humidity values.
READ + SHA verified two-site SCOPED RESEARCH TRIAL ONLY:
  US-Kon 200412032330, 200412040000, 200412040030: PSRF
  US-NR1 200412032200, 200412032230: FLDS
  US-NR1 200412032230, 200412032300, 200412032330: PSRF
Each corrupt QC2 original is restored by EXACT 30-min linear interpolation
between two immediate surrounding valid original source-QC2 analog anchors,
not by a global replacement policy. Source-native clocks unchanged.
No science approval for final forcing is implied by numeric candidate.
All old VPD/QBOT/other fields, source QC and existing science holds retained.
--self-test: pure synthetic/no writes; --check all SHA and trial physics no writes
--trial: same + separate SHA-sealed two-site research-only successors/reports.
"""
import argparse,hashlib,json,sys,traceback
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import pandas as pd
import numpy as np
sys.dont_write_bytecode=True
VERSION="batch03-stage12ak-v1-20261026-nonhumidity-KON-NR1-eight-variable-proposals"
R=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AI=R/"reports/stage12ai_ten_site_selected_sources_current_20261026T030050Z_7717ee91"
AJ=R/"reports/stage12aj_7_selected_nonhumidity_exact_native_source_QC_20261026T030647Z_344ecbba"
S=R/"qcv5_native_trial_20261022T024559Z_36c46e58"
AI_CSV="ten_site_current_source_native_selected_stage_status.csv"
AJ_CSV="seven_nonhumidity_missing_native_site_field_ids.csv"
EVENTS={
 "US-Kon":{
   "PSRF":("200412032300","200412040100",
           ("200412032330","200412040000","200412040030"),
           "PA_F","PA_F_QC",(49.156,1.768,49.139), (96.544,96.510),1000.)},
 "US-NR1":{
   "PSRF":("200412032200","200412040000",
           ("200412032230","200412032300","200412032330"),
           "PA_F","PA_F_QC",(30.871,-8.200,30.859), (69.942,69.917),1000.),
   "FLDS":("200412032130","200412032300",
           ("200412032200","200412032230"),
           "LW_IN_F","LW_IN_F_QC",(22.869,22.869),(191.629,191.440),1.)}}
SOURCE_COLS=("TA_F","TA_F_QC","VPD_F","VPD_F_QC","PA_F","PA_F_QC",
             "LW_IN_F","LW_IN_F_QC")
def safe(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file():raise ValueError("Original SHA source missing or symlink: "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()
def ts(k):
    return pd.to_datetime(k,format="%Y%m%d%H%M")
def keystr(s):
    return s.astype(str).str.replace(r"[^0-9]","",regex=True).str.slice(0,12)
def interpolate(k,lo,hi,y0,y1):
    t,st,end=ts(k),ts(lo),ts(hi)
    if not st<t<end:raise ValueError("Noninterior or altered native time")
    if not (t-st).total_seconds()%1800==0 or not (end-st).total_seconds()%1800==0:
        raise ValueError("Native 30-minute grid changed")
    return float(y0+(y1-y0)*((t-st)/(end-st)))
def selftest():
    assert sum(len(info[2]) for group in EVENTS.values() for info in group.values())==8
    assert abs((96.544+1.768)/2-49.156)<1e-12
    assert abs((-8.2+69.917)/2-30.8585)<1e-12
    known={
       ("US-Kon","PSRF"):[96535.5,96527.,96518.5],
       ("US-NR1","PSRF"):[69935.75,69929.5,69923.25],
       ("US-NR1","FLDS"):[191.566,191.503]}
    for site,fields in EVENTS.items():
        for field,(left,right,targets,_,__,old,anchors,mult) in fields.items():
            vals=[interpolate(k,left,right,anchors[0],anchors[1])*mult for k in targets]
            assert np.allclose(vals,known[(site,field)],atol=1e-9,rtol=0)
    print("STAGE12AK SELF-TEST PASS: 7 distinct native HH; 6 pressure plus 2 longwave fields; source clock preserved; NO WRITES",flush=True)
def read_sources():
    a=json.loads(safe(AI/"stage12ai_ten_site_status_SHA_receipt.json").read_text())
    j=json.loads(safe(AJ/"stage12aj_seven_nonhumidity_SHA_receipt.json").read_text())
    if not(a.get("site_count")==10 and a.get("science_only") is True
        and a.get("post_v5_approved_sites")==0 and a.get("DATM_ready_sites")==0
        and a.get("spinup_authorized_sites")==0
        and a.get("output_SHA256",{}).get(AI_CSV)==sha(AI/AI_CSV)
        and j.get("seven_missing_event_rows")==7
        and j.get("Kon_missing_rows")==3
        and j.get("NR1_missing_rows")==4
        and j.get("post_v5_approved") is False
        and j.get("model_ready") is False
        and j.get("output_SHA256",{}).get(AJ_CSV)==sha(AJ/AJ_CSV)):
        raise ValueError("Source Stage12ai/aj SHA and scientific gate mismatch")
    status=pd.read_csv(safe(AI/AI_CSV),dtype={"site":str},low_memory=False)
    missing=pd.read_csv(safe(AJ/AJ_CSV),dtype={"site":str,"native_key":str},low_memory=False)
    want={
      ("US-Kon","200412032330"):{"PSRF"},
      ("US-Kon","200412040000"):{"PSRF"},
      ("US-Kon","200412040030"):{"PSRF"},
      ("US-NR1","200412032200"):{"FLDS"},
      ("US-NR1","200412032230"):{"PSRF","FLDS"},
      ("US-NR1","200412032300"):{"PSRF"},
      ("US-NR1","200412032330"):{"PSRF"}}
    found={(x.site,str(x.native_key)):set(str(x.missing_fields).split(","))
           for x in missing.itertuples(index=False)}
    if len(missing)!=7 or found!=want:
        raise ValueError("Original Stage12aj seven missing times or original missing fields changed")
    m=json.loads(safe(S/"exact_input_manifest.json").read_text())
    specs={x["site"]:x for x in m["sites"]}
    pins={str(Path(k).resolve()):v for k,v in m["input_sha256"].items()}
    return status,specs,pins
def audit():
    status,specs,pins=read_sources()
    derived={}
    patches=[]
    for site,group in EVENTS.items():
        found=status.loc[status.site.eq(site)]
        if len(found)!=1 or str(found.iloc[0].selected_stage)!=(
               "Stage12ah" if site=="US-Kon" else "Stage12af"):
            raise ValueError("Latest selected verified source changed "+site)
        meta=found.iloc[0]
        path=safe(meta.input_path)
        if sha(path)!=str(meta.sha256):raise ValueError("Selected full-site original successor SHA mismatch "+site)
        src=safe(specs[site]["primary"])
        if sha(src)!=pins.get(str(src.resolve())):
            raise ValueError("Original tower source original Stage07 SHA changed "+site)
        base=pd.read_csv(path,dtype={"time":str},low_memory=False)
        original_columns=list(base.columns)
        keys=keystr(base.time)
        if keys.duplicated().any():raise ValueError("Duplicate native timestamps "+site)
        loc={str(k):i for i,k in enumerate(keys)}
        if not base.time.equals(base.time.sort_values(ignore_index=True)):
            raise ValueError("Unexpected selected full-site source time order "+site)
        need={k for x in group.values() for k in (x[0],x[1],*x[2])}
        if not need<=set(loc):
            raise ValueError("Missing exact site native target/anchor "+site)
        tower=pd.read_csv(src,dtype={"TIMESTAMP_START":str},
                          usecols=["TIMESTAMP_START",*SOURCE_COLS],low_memory=False)
        tower=tower.loc[tower.TIMESTAMP_START.isin(need)].copy()
        if tower.TIMESTAMP_START.duplicated().any() or set(tower.TIMESTAMP_START)!=need:
            raise ValueError("Incomplete/duplicate original signed raw site source points "+site)
        tower.set_index("TIMESTAMP_START",inplace=True)
        selected=base.copy(deep=True)
        changed=set()
        for field,(lo,hi,targets,rawcol,qccol,expected_bad,expected_anchor,mul) in group.items():
            for k,expected in zip((lo,hi),expected_anchor):
                v=float(tower.loc[k,rawcol]);qc=float(tower.loc[k,qccol])
                true=float(base.loc[loc[k],field])
                if not(qc==2 and abs(v-expected)<1e-5 and abs(true-v*mul)<.01):
                    raise ValueError("Anchor no longer original valid ERA-source value "+site+" "+field+" "+k)
                if field=="PSRF" and not(60000<=true<=105000):
                    raise ValueError("Anchor pressure unrealistic "+site+" "+k)
                if field=="FLDS" and not(100<=true<=500):
                    raise ValueError("Anchor longwave unrealistic "+site+" "+k)
            for k,bad in zip(targets,expected_bad):
                i=loc[k];x=tower.loc[k]
                if not(float(x[qccol])==2 and
                       abs(float(x[rawcol])-float(bad))<1e-5 and
                       pd.isna(base.loc[i,field])):
                    raise ValueError("Original corrupt/missing QC2 forcing differs "+site+" "+field+" "+k)
                value=interpolate(k,lo,hi,*expected_anchor)*mul
                if not((60000<=value<=105000) if field=="PSRF"
                       else (100<=value<=500)):
                    raise ValueError("Interpolated meteorology out of physical guard "+site+" "+field+" "+k)
                if field=="PSRF" and not (pd.isna(base.loc[i,"VPD_USE"]) and pd.isna(base.loc[i,"QBOT"])):
                    raise ValueError("Pressure edit would require unapproved humidity recalculation "+site+" "+k)
                if (site,k,field) in changed:raise ValueError("Duplicate scoped repair proposal")
                changed.add((site,k,field))
                selected.loc[i,field]=value
                patches.append({
                  "site":site,"native_key":k,"variable":field,
                  "original_source_QC2":int(x[qccol]),
                  "original_source_bad_native_value":float(bad),
                  "new_research_only_candidate_value":value,
                  "left_anchor_native_key":lo,"right_anchor_native_key":hi,
                  "left_source_QC2_value":float(expected_anchor[0])*mul,
                  "right_source_QC2_value":float(expected_anchor[1])*mul,
                  "numerical_proposal_only_not_production_approved":True
                })
        allowed={f:set(x[2]) for f,x in group.items()}
        for f in original_columns:
            if f not in allowed:
                if not selected[f].equals(base[f]):
                    raise ValueError("Non-target meteorological or humidity column changed "+site+" "+f)
            else:
                original=base[f].to_numpy(dtype=float)
                updated=selected[f].to_numpy(dtype=float)
                mask=keys.isin(allowed[f]).to_numpy(dtype=bool)
                if not np.array_equal(original[~mask],updated[~mask],equal_nan=True):
                    raise ValueError("Any off-target meteorological value modified "+site+" "+f)
        if not base.time.equals(selected.time):
            raise ValueError("Native source time, leap coverage or rows modified "+site)
        old_nonhumid=base[["TBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE"]].isna().any(axis=1).sum()
        new_nonhumid=selected[["TBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE"]].isna().any(axis=1).sum()
        expected_removed=3 if site=="US-Kon" else 4
        if not(old_nonhumid==expected_removed and new_nonhumid==0):
            raise ValueError("Expected exact corrected nonhumidity source rows not achieved "+site)
        if not(selected.VPD_USE.equals(base.VPD_USE) and selected.QBOT.equals(base.QBOT)):
            raise ValueError("Unapproved VPD/QBOT changed "+site)
        derived[site]={"selected":selected,"source_sha":sha(path),
                      "old_nonhumidity_missing":int(old_nonhumid),
                      "new_nonhumidity_missing":int(new_nonhumid),
                      "retained_VPD_missing":int(selected.VPD_USE.isna().sum())}
        print("SCOPED PROPOSAL",site, "source nonhumidity missing",int(old_nonhumid),"->",int(new_nonhumid),
              "VPD/QBOT missing remain",int(selected.VPD_USE.isna().sum()),flush=True)
    if len(patches)!=8 or len({(p["site"],p["native_key"]) for p in patches})!=7:
        raise ValueError("Target science 8 fields / 7 native times differ")
    return derived,pd.DataFrame(patches)
def main():
    ap=argparse.ArgumentParser()
    g=ap.add_mutually_exclusive_group(required=True)
    for arg in ("self-test","check","trial"):g.add_argument("--"+arg,action="store_true")
    mode=ap.parse_args()
    print("STAGE12AK EVIDENCE-GATED SEVEN BAD NONHUMIDITY HH / EIGHT FIELDS | "+VERSION,flush=True)
    selftest()
    if mode.self_test:return
    derived,patches=audit()
    print("\n====== EIGHT EXACT RESEARCH ONLY PROPOSALS FROM ORIGINAL VALID QC2 ANCHORS ======",flush=True)
    print(patches.to_string(index=False),flush=True)
    if mode.check:
        print("STAGE12AK CHECK ONLY: ZERO SOURCE / REPORT / MODEL WRITES.",flush=True);return
    output=R/"science_trials"/("stage12ak_7_nonhumidity_source_interpolation_PROPOSALS_ONLY_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    output.mkdir(parents=True,exist_ok=False)
    filenames=[]
    for site,info in derived.items():
        name=f"{site}_STAGE12AK_NONHUMIDITY_PROPOSAL_ONLY_INCOMPLETE_NOLEAP.csv"
        info["selected"].to_csv(output/name,index=False)
        filenames.append(name)
    name="eight_pressure_longwave_native_source_interpolation_PROPOSALS.csv"
    patches.to_csv(output/name,index=False)
    filenames.append(name)
    marker="INCOMPLETE_NOT_OPERATOR_APPROVED_DO_NOT_USE_FOR_DATM_OR_SPINUP"
    (output/marker).write_text(
       "This is a scoped NUMERIC RESEARCH CANDIDATE only; no new operator "
       "science authorization or production Post-v5. Original 6 pressure "
       "corrupt ERA-filled site rows and 2 downwelling longwave corrupt "
       "ERA-filled NR1 rows replaced with short linear interpolants between "
       "surrounding valid original source QC2 anchors. All original files "
       "and science holds, VPD/QBOT, source time and other meteorology intact.\n")
    filenames.append(marker)
    receipt={"version":VERSION,"original_Stage12ai_receipt_SHA256":sha(AI/"stage12ai_ten_site_status_SHA_receipt.json"),
             "original_Stage12aj_receipt_SHA256":sha(AJ/"stage12aj_seven_nonhumidity_SHA_receipt.json"),
             "unique_native_rows":7,"original_variable_fields":8,
             "science_user_approved_to_production":False,
             "post_v5_approved":False,"DATM_ready":False,
             "spinup_authorized":False,
             "source_sha256":{site:info["source_sha"] for site,info in derived.items()},
             "output_SHA256":{name:sha(output/name) for name in filenames}}
    (output/"stage12ak_research_proposal_SHA_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print("STAGE12AK RESEARCH ONLY EXACT SEVEN NATIVE TIME CANDIDATE DIR:",output,flush=True)
if __name__=="__main__":
    try:main()
    except Exception as ex:
        print("STAGE12AK STOP:",ex,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

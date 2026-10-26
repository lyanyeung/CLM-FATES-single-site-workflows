#!/usr/bin/env python3
"""Batch03 Stage12ai — 10-site latest SHA-sealed scientific candidate checkpoint.

READ-ONLY. Verify separate selected site research successors (NOT model-ready):
- six former Stage12g sites, with user approved isolated Kon Stage12ah,
  NR1 Stage12af, Me6 Stage12ac successors selected instead of stale G.
- three older approved-for-science-numerics-only Stage11h/11q shadows.
- US-Me2 retains four clock metadata holds, no selected full shadow.

Produces a concise current row-by-row humidity/other nonfinite status and
scientific gate report; 10/10 full physical-source approvals remain false.
Do not use research shadows to construct DATM or run CLM-FATES.
--check = SHA/audit only, NO writes
--run = same + one separate SHA-sealed report only, NO forcing writes
--self-test = isolated synthetic path, no reads/writes
"""
import argparse,hashlib,json,sys,traceback
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
import pandas as pd
import numpy as np
sys.dont_write_bytecode=True
VERSION="batch03-stage12ai-v1-20261026-ten-site-selected-science-successors"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
G=ROOT/"science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f"
AC=ROOT/"science_trials/stage12ac_USER_APPROVED_Me6_20170704_0600_0800_ERA_RH_20261025T232237Z_534eb248"
AF=ROOT/"science_trials/stage12af_NR1_20220910_user_approved_three_T_only_20261026T013349Z_34ff1cda"
AH=ROOT/"science_trials/stage12ah_USER_APPROVED_Kon_23_T_one_QC0_VPD_20261026T024732Z_8075bed8"
H=ROOT/"science_trials/stage11h_companion_ERA_RH_shadow_20261024T084110Z_78d963bd"
Q=ROOT/"science_trials/stage11q_US-NC2_auto9_RH_only_20261024T112211Z_cd95c65a"
FILES={
 "US-Kon":(AH,"US-Kon_STAGE12AH_APPROVED_23T_QC0VPD_INCOMPLETE_NOLEAP.csv","stage12ah_approved_23T_QC0_SHA_receipt.json"),
 "US-Me6":(AC,"US-Me6_STAGE12AC_USER_APPROVED_OVERLAY_INCOMPLETE_NOLEAP.csv","stage12ac_user_approved_5HH_SHA_receipt.json"),
 "US-MMS":(G,"US-MMS_STAGE12G_INCOMPLETE_NOLEAP.csv","stage12g_research_only_sha_receipt.json"),
 "US-MOz":(H,"US-MOz_shadow_companion_ERA_RH_NOLEAP.csv","sha_sealed_shadow_trial_receipt.json"),
 "US-Mpj":(H,"US-Mpj_shadow_companion_ERA_RH_NOLEAP.csv","sha_sealed_shadow_trial_receipt.json"),
 "US-MtB":(G,"US-MtB_STAGE12G_INCOMPLETE_NOLEAP.csv","stage12g_research_only_sha_receipt.json"),
 "US-NC2":(Q,"US-NC2_humidity_only_auto9_shadow_NOLEAP.csv","stage11q_sha_science_hold_receipt.json"),
 "US-NR1":(AF,"US-NR1_STAGE12AF_USER_APPROVED_T_ONLY_INCOMPLETE_NOLEAP.csv","stage12af_three_temperature_SHA_receipt.json"),
 "US-NR3":(G,"US-NR3_STAGE12G_INCOMPLETE_NOLEAP.csv","stage12g_research_only_sha_receipt.json")
}
EXPECTED_MISSING={"US-NR3":238,"US-Kon":389,"US-NR1":240,
                  "US-MMS":16,"US-MtB":2840,"US-Me6":65}
UNREPAIRED_OTHER_SOURCE_HOLD={"US-Me2":4}
COLUMNS=["TBOT","QBOT","PSRF","FSDS","FLDS","WIND","PRECTmms","TA_USE","VPD_USE"]
def safe(p):
    p=Path(p)
    if not p.is_file() or p.is_symlink():raise ValueError("Missing/symlink original immutable source "+str(p))
    return p
def sha(p):
    h=hashlib.sha256()
    with safe(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def selftest():
    assert len(FILES)==9 and len(UNREPAIRED_OTHER_SOURCE_HOLD)==1
    assert sum(EXPECTED_MISSING.values())==3788
    assert set(FILES)|set(UNREPAIRED_OTHER_SOURCE_HOLD)=={
        "US-Kon","US-Me2","US-Me6","US-MMS","US-MOz","US-Mpj",
        "US-MtB","US-NC2","US-NR1","US-NR3"}
    print("STAGE12AI SELF-TEST PASS: 10 sites, 9 latest signed science derivatives, Me2 clock unresolved, six known humidity gaps 3788; NO WRITES",flush=True)
def check():
    gout=json.loads(safe(G/"stage12g_research_only_sha_receipt.json").read_text())
    if not gout.get("original_233_physics_holds_untouched") is True:
        raise ValueError("Original Stage12g source protection missing")
    hrec=json.loads(safe(H/"sha_sealed_shadow_trial_receipt.json").read_text())
    qrec=json.loads(safe(Q/"stage11q_sha_science_hold_receipt.json").read_text())
    rows=[]
    for site,(root,name,receiptname) in sorted(FILES.items()):
        rec=json.loads(safe(root/receiptname).read_text())
        refs=rec.get("output_SHA256",rec.get("output_sha256",{}))
        if name not in refs or refs[name]!=sha(root/name):
            raise ValueError("Source science derivative SHA mismatch "+site)
        if rec.get("Postv5_approved")!=0 or rec.get("DATM_ready")!=0:
            raise ValueError("Science model-ready gate changed "+site)
        if root==H and (site not in ("US-MOz","US-Mpj") or not hrec):
            raise ValueError("Research H source mismatch "+site)
        if root==Q and (site!="US-NC2" or qrec.get("spinup_authorized")!=0):
            raise ValueError("Research Q source mismatch")
        df=pd.read_csv(root/name,low_memory=False)
        if not {"time",*COLUMNS}<=set(df):
            raise ValueError("Original forcing table columns missing "+site)
        stamp=pd.to_datetime(df.time,errors="raise")
        if stamp.duplicated().any() or not stamp.is_monotonic_increasing:
            raise ValueError("Duplicate/nonmonotonic original site time index "+site)
        if ((stamp.dt.month==2)&(stamp.dt.day==29)).any():
            raise ValueError("NOLEAP source contains leap day "+site)
        nn=df[COLUMNS].apply(pd.to_numeric,errors="coerce")
        finite=np.isfinite(nn.to_numpy(dtype=float))
        humidity_missing=int((~finite[:,COLUMNS.index("VPD_USE")]).sum())
        qbot_missing=int((~finite[:,COLUMNS.index("QBOT")]).sum())
        any_missing=int((~finite).any(axis=1).sum())
        other_missing=int((~np.delete(finite,[COLUMNS.index("QBOT"),COLUMNS.index("VPD_USE")],axis=1)).any(axis=1).sum())
        if site in EXPECTED_MISSING:
            if humidity_missing!=EXPECTED_MISSING[site] or qbot_missing!=EXPECTED_MISSING[site]:
                raise ValueError("Latest science successor missing count changed "+site+": "+str((humidity_missing,qbot_missing)))
        rows.append({
          "site":site,"selected_stage":("Stage12ah" if site=="US-Kon" else
               "Stage12af" if site=="US-NR1" else
               "Stage12ac" if site=="US-Me6" else
               "Stage12g" if root==G else "Stage11q" if root==Q else "Stage11h"),
          "source_native_rows":len(df),"selected_VPD_missing":humidity_missing,
          "selected_QBOT_missing":qbot_missing,
          "any_field_missing_rows":any_missing,
          "nonhumidity_field_missing_rows":other_missing,
          "science_status":"RESEARCH_INCOMPLETE_NOT_POSTV5_DATM_READY",
          "input_path":str(root/name),"sha256":sha(root/name)})
        print("LATEST",site,"stage",rows[-1]["selected_stage"],
              "VPD/QBOT missing",humidity_missing,qbot_missing,
              "other_fields_missing_rows",other_missing,flush=True)
    rows.append({
      "site":"US-Me2","selected_stage":"Stage11a original native clock HOLD",
      "source_native_rows":None,"selected_VPD_missing":None,
      "selected_QBOT_missing":None,"any_field_missing_rows":None,
      "nonhumidity_field_missing_rows":None,
      "science_status":"FOUR_SOURCE_CLOCK_METADATA_HOLDS_NO_VERIFIED_FULL_SHADOW",
      "input_path":"","sha256":""})
    data=pd.DataFrame(rows).sort_values("site").reset_index(drop=True)
    if sum(data.site.isin(EXPECTED_MISSING))!=6:
        raise ValueError("Expected six exact Stage12g successor sites missing")
    print("SIX SITE CURRENT SOURCE-NATIVE VPD HOLES:",int(data.selected_VPD_missing.sum(skipna=True)),
          "across 9 selected sources; 3788 is the six-site subtotal, NOT all ten, unless other three also zero",flush=True)
    print("ALL TEN: 0 model-ready flags, US-Me2 4 clock holds; source-year and old physics science holds not released",flush=True)
    return data
def main():
    pa=argparse.ArgumentParser()
    opt=pa.add_mutually_exclusive_group(required=True)
    for flag in ("self-test","check","run"):opt.add_argument("--"+flag,action="store_true")
    args=pa.parse_args()
    print("STAGE12AI TEN-SITE SELECTED SCIENCE SUCCESSOR STATUS | "+VERSION,flush=True)
    selftest()
    if args.self_test:return
    df=check()
    print("\n====== TEN-SITE CURRENT VERIFIED SOURCE COUNTS ======\n",df.drop(columns=["input_path","sha256"]).to_string(index=False),flush=True)
    if args.check:
        print("STAGE12AI CHECK ONLY: ZERO NEW REPORT OR MODEL WRITES.",flush=True)
        return
    out=ROOT/"reports"/("stage12ai_ten_site_selected_sources_current_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    name="ten_site_current_source_native_selected_stage_status.csv"
    df.to_csv(out/name,index=False)
    (out/"RESEARCH_ONLY_ALL_TEN_NOT_POSTV5_DATM_READY").write_text(
      "This is an immutable snapshot of 9 separately SHA-verified research-only "
      "candidate sources plus one unverified US-Me2 four clock metadata HOLD. "
      "Selected site files were NOT joined into model forcing; remaining "
      "physics/source year/clock/PFT/science gates remain; no model permission.\n")
    receipt={file:sha(out/file) for file in (name,"RESEARCH_ONLY_ALL_TEN_NOT_POSTV5_DATM_READY")}
    (out/"stage12ai_ten_site_status_SHA_receipt.json").write_text(
       json.dumps({"version":VERSION,"site_count":10,
                   "science_only":True,"post_v5_approved_sites":0,
                   "DATM_ready_sites":0,"spinup_authorized_sites":0,
                   "output_SHA256":receipt},indent=2)+"\n")
    print("STAGE12AI TEN-SITE SHA VERIFIED STATUS REPORT DIR:",out,flush=True)
if __name__=="__main__":
    try:main()
    except Exception as e:
        print("STAGE12AI STOP:",e,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

#!/usr/bin/env python3
"""Stage12aq: independent QC0-vs-ERA context for Stage12ap's 31 Kon QC1/MDS rows.

For each affected native half-hour, identify its EXACT contiguous original
QC1 VPD_F flag run and review local +/-14-day genuinely measured QC0 tower
TA_F and VPD_F against same-time original companion ERA TA_ERA/VPD_ERA.
Compute humidity disagreement distributions; do not make a replacement
recommendation by interpolation, by nearest QC0 or by a single threshold.
No source clock shift, no reanalysis downloads and NO forcing/model edits.

--self-test: synthetic no file access or writes
--check: input signed receipt+source SHA check and in-memory audit, no writes
--run: same + new isolated SHA signed science report only
"""
import argparse, hashlib, json, sys, traceback
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
import numpy as np
import pandas as pd
sys.dont_write_bytecode=True

VER="batch03-stage12aq-v1-20261026-Kon-QC1-run-nearby-QC0-ERA-RH-skill"
ROOT=Path("/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03")
AP=ROOT/"reports/stage12ap_Kon_QC1_MDS_ERA_RH_QC0_anchor_review_20261026T112048Z_9560483c"
SOURCE=ROOT/"qcv5_native_trial_20261022T024559Z_36c46e58"
ROWS="31_original_QC1_MDS_ERA_RH_QC0_anchor_diagnostics.csv"
GROUPS="26_event_MDS_dryness_scope_QC0_anchor_summary.csv"
MARKER="SCIENCE_ONLY_NO_HUMIDITY_APPROVAL_NO_DATM"
EXCEPTIONS={"201102220900","201109291830"}
WINDOW=pd.Timedelta(days=14)
STEP=pd.Timedelta(minutes=30)
WINDOW_HOUR=120

def file(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing or symlink source: "+str(p))
    return p

def sha(path):
    h=hashlib.sha256()
    with file(path).open("rb") as s:
        for block in iter(lambda:s.read(1<<20),b""):h.update(block)
    return h.hexdigest()

def numbers(s):
    x=pd.to_numeric(s,errors="coerce")
    return x.mask(x<=-9990)

def satw(t):
    a=np.asarray(t,dtype=float)
    with np.errstate(over="ignore",divide="ignore",invalid="ignore"):
        y=6.112*np.exp(17.67*a/(a+243.5))
    return np.where((a>-85)&(a<55),y,np.nan)

def rh(t,v):
    return 100*(1-np.asarray(v,dtype=float)/satw(t))

def synthetic():
    a=pd.date_range("2011-10-17 23:00",periods=4,freq="30min")
    assert list(a.strftime("%Y%m%d%H%M"))==[
        "201110172300","201110172330","201110180000","201110180030"]
    assert abs(float(rh(20,0))-100)<1e-10
    assert abs(float(rh(20,satw(20)*.5))-50)<1e-10
    assert len(EXCEPTIONS)==2
    print("STAGE12AQ SELF-TEST PASS | original 30-min continuity and QC0 ERA RH; NO WRITES",flush=True)

def signed():
    r=json.loads(file(AP/"stage12ap_QC1_MDS_ERA_science_SHA_receipt.json").read_text())
    if not (r.get("version")=="batch03-stage12ap-v1-20261026-Kon-QC1-MDS-ERA-independent-boundary-audit"
        and r.get("QC1_MDS_original_neighbors_verified")==31
        and r.get("Stage12an_research_missing_centers_unapproved")==48
        and r.get("seven_blocked_events_remain") is True
        and r.get("two_source_temperature_holds_remain") is True
        and r.get("original_source_QC0_unchanged") is True
        and r.get("operator_approved") is False
        and r.get("Postv5_approved") is False
        and r.get("DATM_ready") is False
        and r.get("spinup_authorized") is False):
        raise ValueError("Upstream Stage12ap original science/approval gate changed")
    for n in (ROWS,GROUPS,MARKER):
        if r.get("output_SHA256",{}).get(n)!=sha(AP/n):
            raise ValueError("Stage12ap source SHA mismatch: "+n)
    mf=json.loads(file(SOURCE/"exact_input_manifest.json").read_text())
    site=next((x for x in mf["sites"] if x["site"]=="US-Kon"),None)
    if site is None:raise ValueError("US-Kon missing original source")
    pins={str(Path(p).resolve()):digest for p,digest in mf["input_sha256"].items()}
    for kind in ("primary","era"):
        p=file(site[kind])
        if sha(p)!=pins.get(str(p.resolve())):
            raise ValueError("Original "+kind+" source SHA changed")
    return site

def load_source(site):
    tower=pd.read_csv(file(site["primary"]),
                      usecols=["TIMESTAMP_START","TA_F","TA_F_QC","VPD_F","VPD_F_QC","VPD_F_MDS"],
                      dtype={"TIMESTAMP_START":str},low_memory=False)
    era=pd.read_csv(file(site["era"]),
                    usecols=["TIMESTAMP_START","TA_ERA","VPD_ERA"],
                    dtype={"TIMESTAMP_START":str},low_memory=False)
    for frame in (tower,era):
        frame["TIME"]=pd.to_datetime(frame.TIMESTAMP_START,format="%Y%m%d%H%M",errors="raise")
        if frame.TIME.duplicated().any():
            raise ValueError("Original native source duplicate time")
        frame.drop(columns=["TIMESTAMP_START"],inplace=True)
        frame.set_index("TIME",inplace=True)
        for col in frame:frame[col]=numbers(frame[col])
    merged=tower.join(era,how="left",validate="one_to_one").sort_index()
    if len(merged)!=len(tower):
        raise ValueError("Tower source native row count changed in join")
    return merged

def qc1_span(src,stamp):
    pos=src.index.get_loc(stamp)
    if not isinstance(pos,(int,np.integer)):
        raise ValueError("Original native row not unique")
    q=src.VPD_F_QC.to_numpy()
    times=src.index
    if not np.isfinite(q[pos]) or q[pos]!=1:
        raise ValueError("Research neighbor no longer original QC1")
    lo=hi=pos
    while lo>0 and times[lo]-times[lo-1]==STEP and q[lo-1]==1:lo-=1
    while hi+1<len(q) and times[hi+1]-times[hi]==STEP and q[hi+1]==1:hi+=1
    return times[lo],times[hi],hi-lo+1

def qc0_reference(src,t):
    m=src.loc[(src.index>=t-WINDOW)&(src.index<=t+WINDOW)].copy()
    tc=m.TA_F.to_numpy(dtype=float)
    v=m.VPD_F.to_numpy(dtype=float)
    te=m.TA_ERA.to_numpy(dtype=float)
    ve=m.VPD_ERA.to_numpy(dtype=float)
    obs=rh(tc,v)
    reference=rh(te,ve)
    matched=(m.TA_F_QC.eq(0).to_numpy()&m.VPD_F_QC.eq(0).to_numpy()
        &np.isfinite(tc)&np.isfinite(v)&np.isfinite(te)&np.isfinite(ve)
        &np.isfinite(obs)&np.isfinite(reference)
        &(obs>=0)&(obs<=100)&(reference>=0)&(reference<=100))
    dt=np.abs((m.index-t).total_seconds())/3600
    good=np.flatnonzero(matched)
    # Additional like-temperature and same-local-hour QC0 comparator sets;
    # these are diagnostics, not proof of conditions during the missing period.
    same_time=np.abs((m.index.hour*60+m.index.minute)-(t.hour*60+t.minute))
    same_time=np.minimum(same_time,1440-same_time)<=WINDOW_HOUR
    similar=np.abs(tc-te)<=5
    q0_same=matched & same_time
    q0_similar=q0_same & similar
    bias=obs[q0_similar]-reference[q0_similar]
    prev=(dt<=24)&matched&(m.index<t)
    following=(dt<=24)&matched&(m.index>t)
    return {
      "QC0_both_original_T_and_VPD_same_native_valid_14d_N":int(matched.sum()),
      "QC0_valid_same_local_hour_pm2h_14d_N":int(q0_same.sum()),
      "QC0_valid_same_hour_ERA_Twithin5C_14d_N":int(q0_similar.sum()),
      "QC0_original_minus_ERA_RH_median_pp":float(np.median(bias)) if len(bias) else np.nan,
      "QC0_original_minus_ERA_RH_MAE_pp":float(np.mean(np.abs(bias))) if len(bias) else np.nan,
      "QC0_original_minus_ERA_RH_abs_P90_pp":float(np.quantile(np.abs(bias),0.9)) if len(bias) else np.nan,
      "QC0_valid_within_prev_24h_N":int(prev.sum()),
      "QC0_valid_within_next_24h_N":int(following.sum()),
      "nearest_valid_QC0_before_hours":float(np.min(dt[good[m.index[good]<t]])) if np.any(m.index[good]<t) else np.nan,
      "nearest_valid_QC0_after_hours":float(np.min(dt[good[m.index[good]>t]])) if np.any(m.index[good]>t) else np.nan,
    }

def audit():
    site=signed()
    earlier=pd.read_csv(file(AP/ROWS),dtype={"native_key":str},low_memory=False)
    if len(earlier)!=31 or earlier.native_key.duplicated().any() or \
            set(earlier.native_key)&EXCEPTIONS or \
            not (earlier.original_VPD_F_QC.eq(1).all() and
                 earlier.original_VPD_F_equals_MDS.astype(str).str.lower().eq("true").all()):
        raise ValueError("31 signed original QC1/MDS trial identities changed")
    src=load_source(site)
    out=[]
    for row in earlier.itertuples(index=False):
        stamp=pd.to_datetime(row.native_key,format="%Y%m%d%H%M")
        if stamp not in src.index:raise ValueError("Missing original native time "+row.native_key)
        cur=src.loc[stamp]
        if not (cur.VPD_F_QC==1 and np.isfinite([cur.VPD_F,cur.VPD_F_MDS,
                cur.TA_F,cur.TA_ERA,cur.VPD_ERA]).all()
            and np.isclose(cur.VPD_F,cur.VPD_F_MDS,rtol=0,atol=1e-6)
            and np.isclose(cur.VPD_F,float(row.source_original_VPD_F_hPa),rtol=0,atol=1e-6)
            and np.isclose(float(rh(cur.TA_F,cur.VPD_F)),float(row.original_source_RH_pct),rtol=0,atol=1e-4)
            and np.isclose(float(rh(cur.TA_ERA,cur.VPD_ERA)),float(row.companion_ERA_RH_pct),rtol=0,atol=1e-4)):
            raise ValueError("Original tower versus signed Stage12ap humidity changed "+row.native_key)
        first,last,count=qc1_span(src,stamp)
        context=qc0_reference(src,stamp)
        out.append({
            "episode":int(row.episode),"native_key":row.native_key,
            "original_QC1_MDS_RH_pct":float(row.original_source_RH_pct),
            "native_ERA_RH_pct":float(row.companion_ERA_RH_pct),
            "candidate_minus_MDS_RH_percentage_points":float(row.candidate_minus_original_RH_pct_points),
            "original_TA_QC":int(cur.TA_F_QC),
            "tower_minus_ERA_T_C":float(cur.TA_F-cur.TA_ERA),
            "source_VPD_F_equals_MDS":True,
            "full_native_QC1_run_start":first.strftime("%Y%m%d%H%M"),
            "full_native_QC1_run_end":last.strftime("%Y%m%d%H%M"),
            "full_native_QC1_run_halfhours":int(count),
            "full_native_QC1_run_hours":float(count/2),
            **context,
            "original_HOLD_and_unapproved":True
        })
    rows=pd.DataFrame(out).sort_values(["episode","native_key"])
    groups=[]
    for number,g in rows.groupby("episode",sort=True):
        groups.append({
            "episode":int(number),"proposed_finite_neighbors":len(g),
            "original_RH_below5_count":int((g.original_QC1_MDS_RH_pct<5).sum()),
            "median_original_MDS_RH_pct":float(g.original_QC1_MDS_RH_pct.median()),
            "median_native_ERA_RH_pct":float(g.native_ERA_RH_pct.median()),
            "QC1_full_native_run_max_halfhours":int(g.full_native_QC1_run_halfhours.max()),
            "QC0_same_hour_comparators_14d_min":int(g.QC0_valid_same_hour_ERA_Twithin5C_14d_N.min()),
            "QC0_same_hour_comparators_14d_median":float(g.QC0_valid_same_hour_ERA_Twithin5C_14d_N.median()),
            "QC0_same_hour_ERA_RH_MAE_14d_median_pp":float(g.QC0_original_minus_ERA_RH_MAE_pp.median()) if g.QC0_original_minus_ERA_RH_MAE_pp.notna().any() else np.nan,
            "QC0_both_sides_within_24h_rows":int(((g.QC0_valid_within_prev_24h_N>0)&(g.QC0_valid_within_next_24h_N>0)).sum()),
            "operator_approval":False,
        })
    summary=pd.DataFrame(groups)
    if len(rows)!=31 or int(summary.proposed_finite_neighbors.sum())!=31 or \
            int(summary.loc[summary.episode.isin([15,17]),"proposed_finite_neighbors"].sum())!=24:
        raise ValueError("Stage12aq exact 31 signed source-neighbor rows altered")
    return rows,summary

def main():
    parser=argparse.ArgumentParser()
    switches=parser.add_mutually_exclusive_group(required=True)
    for opt in ("self-test","check","run"):
        switches.add_argument("--"+opt,action="store_true")
    args=parser.parse_args()
    print("STAGE12AQ Kon QC1-MDS FULL SOURCE RUN & NEARBY QC0 ERA SKILL | "+VER,flush=True)
    synthetic()
    if args.self_test:return
    rows,summary=audit()
    print("\n===== 31 FINITE ORIGINAL MDS SOURCES WITH 14-DAY QC0 CONTEXT =====",flush=True)
    print(rows.round(5).to_string(index=False),flush=True)
    print("\n===== AFFECTED EPISODE QC0 vs ERA REFERENCE SUMMARY =====",flush=True)
    print(summary.round(5).to_string(index=False),flush=True)
    print("STAGE12AQ 31/31 source-QC1 MDS references | original 48 centre repairs",
          "remain UNAPPROVED | 7 blocked episodes / 2 special T holds protected",flush=True)
    if args.check:
        print("STAGE12AQ CHECK ONLY | ZERO WRITES, ZERO APPROVALS",flush=True)
        return
    dest=ROOT/"reports"/("stage12aq_Kon_full_QC1_run_and_14day_QC0_ERA_RH_review_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    out={
      "31_original_QC1_MDS_full_run_and_nearby_QC0_ERA_RH.csv":rows,
      "affected_episodes_QC0_native_ERA_RH_skill_summary.csv":summary}
    for name,df in out.items():df.to_csv(dest/name,index=False)
    hold="SCIENCE_HOLD_NO_OPERATOR_APPROVAL_NO_MODEL_INPUT"
    (dest/hold).write_text(
      "All 31 finite original QC1/MDS source records remain protected from production changes. "
      "A QC1 fill can be biased, but paired original ERA is not independent proof. "
      "Native QC0 reference comparisons +/-14 days at the same source timestamp and same "
      "local clock time test ERA site skill, not the truth at missing times. "
      "The 48 original missing centers, seven blocked episodes and two special T source "
      "holds remain scientifically and operationally unapproved. No clock, original tower, "
      "previous trial, post-v5, DATM, model or Slurm modifications.\n")
    checks={p:sha(dest/p) for p in [*out,hold]}
    (dest/"stage12aq_QC1_QC0_ERA_skill_SHA_receipt.json").write_text(
       json.dumps({"version":VER,
           "upstream_stage12ap_receipt_SHA256":sha(AP/"stage12ap_QC1_MDS_ERA_science_SHA_receipt.json"),
           "original_QC1_MDS_rows":31,
           "original_48_center_research_only":True,
           "seven_failed_events_unchanged":True,
           "special_two_temperature_holds_preserved":True,
           "operator_approved":False,"DATM_ready":False,"spinup_authorized":False,
           "output_SHA256":checks},indent=2)+"\n")
    print("STAGE12AQ SIGNED SCIENCE REPORT DIR:",dest,flush=True)
    print("NO ORIGINAL SOURCE, SOURCE CLOCK, OTHER SCIENCE TRIAL, DATM OR MODEL WRITES",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("STAGE12AQ STOP:",exc,file=sys.stderr,flush=True)
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(2)

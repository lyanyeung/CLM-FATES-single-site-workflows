#!/usr/bin/env python3
"""Stage28: ONE-PASS seven-site MET closure experiment.

- Parent: Stage26 selected 13-site manifest (inherits Stage22, retains FI-Hyy 1-HH VPD trial)
- Targets: ES-LJu, DE-Gri, FI-Let, FR-Pue, GF-Guy, IT-MBo, IT-Col
- Reuse Stage26 conservative full-short-fill-run QC0-bracketed T/VPD repairs.
- Additional strictly isolated QC1/2 single-HH temperature spike test with local
  neighbours + matching source ERA reference + RH continuity. ERA is corroborating
  evidence, NOT independent truth, and no QC0 observations are changed.
- Stage22 remaining DE-Gri/FI-Let MDS blocks are preserved as decisions with reasons;
  Stage22 already used the cached ERA5/ERA5-Land products for whole-envelope trials.
- Rainfall remains UNCHANGED: ES-LJu 23:00 daily-total suspicion is NOT sufficient
  proof to redistribute or adjust P_F/PRECTmms.
- All 13 site files are independently SHA-verified and full Stage20 numeric-audited.
- Writes a new immutable candidate directory; NEVER grants science approval.

Usage on IRIDIS:
    conda activate clm_fates_env
    python ~/28_onepass_remaining7_MET_finalize.py --mode run --out \
        /iridisfs/scratch/ly3n24/CLM_FATES/experiments/FLUXNET_13_STAGE28_<unique>

This script operates on previously stored site FLUXNET/ICOS licensed data only;
no new external ERA download is needed.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

HOME=Path.home()
BASE=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments')
DEFAULT_26=BASE/'FLUXNET_MultiSite_13_MET_stage26_20261018_050050_967884'/'reports'
DEFAULT_22=BASE/'FLUXNET_MultiSite_13_stage22_retry_20261018_041156_893243'/'reports'
DEFAULT_RAW=HOME/'FLUXNET_13_input_audit/site_input_summary.csv'
ALL=['DE-Lnf','DE-Obe','ES-Agu','ES-LJu','IT-Col','DE-Gri','DE-RuR',
     'FI-Hyy','FI-Let','FR-Pue','GF-Guy','IT-MBo','IT-Tor']
TARGETS=['ES-LJu','DE-Gri','FI-Let','FR-Pue','GF-Guy','IT-MBo','IT-Col']
MET=['TA_USE','VPD_USE','TBOT','QBOT']
REQUIRED={'time','TA_USE','VPD_USE','TBOT','QBOT','PSRF','FSDS','FLDS','WIND','PRECTmms'}
MDS_PENDING={'NO_STAGE22_EDIT_STILL_PENDING','STAGE22_PARTIAL_FLAGGED_BLOCK_STILL_PENDING'}


def ensure(x,msg):
    if not x: raise RuntimeError(msg)


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def load(path,name):
    ensure(Path(path).is_file(),f'Missing reusable validated script: {path}')
    s=importlib.util.spec_from_file_location(name,str(path))
    m=importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def scalar(x):
    try:
        z=float(x)
        return z if np.isfinite(z) else float('nan')
    except (TypeError,ValueError):return float('nan')


def isolated_spike_trials(site,d,src,ix,mod,occupied):
    """A conservative alternative for isolated 1-HH impulses within *long* fills.

    Doesn't edit a whole long QC1/QC2 run. Only a single TEMP outlier with near-
    agreeing neighbours, reanalysis temperature and two humidity endpoints can
    be considered. Check both original jumps improve; do not cross noleap seam.
    """
    t=d.TA_USE.to_numpy(float);v=d.VPD_USE.to_numpy(float)
    pa=d.PSRF.to_numpy(float)
    qct=src.TA_F_QC.to_numpy(float);qcv=src.VPD_F_QC.to_numpy(float)
    era=src.TA_ERA.to_numpy(float);era_v=src.VPD_ERA.to_numpy(float)
    rh,_=mod.therm(t,v,pa)
    adjacent=(ix[1:]-ix[:-1])==pd.Timedelta(minutes=30)
    flagged=np.flatnonzero(adjacent&(np.abs(np.diff(t))>12))+1
    candidates=sorted({int(z) for i in flagged for z in (i-1,i) if 2<=z<len(t)-2})
    proposals={};holds=[]
    for i in candidates:
        if i in occupied:continue
        if qct[i] not in (1,2) or qcv[i] not in (1,2):continue
        # 2 neighbouring half-hours on each side must all be consecutive.
        if not all(ix[j]-ix[j-1]==pd.Timedelta(minutes=30) for j in range(i-1,i+3)):
            continue
        x=t[i-2:i+3]
        if not np.isfinite(x).all():continue
        if np.max(np.abs(np.diff(x)))<=12:continue
        # Two left and two right values must be smoothly stable and in agreement.
        if max(abs(t[i-2]-t[i-1]),abs(t[i+1]-t[i+2]))>2.5:continue
        if abs(t[i-1]-t[i+1])>3.0:continue
        nt=float((t[i-1]+t[i+1])/2)
        if abs(t[i]-nt)<9:continue
        reason=''
        # Source downscaled ERA is not independent, but can veto unsafe changes.
        if not np.isfinite(era[i]) or abs(nt-era[i])>3.0:
            reason='NO_ERA_T_CORROBORATION'
        elif abs(t[i]-era[i])<8.0:
            reason='PARENT_NOT_ABNORMALLY_FAR_FROM_ERA'
        elif not np.isfinite(era_v[i]):
            reason='NO_ERA_VPD_REFERENCE'
        elif not np.isfinite(rh[i-1]) or not np.isfinite(rh[i+1]):
            reason='INVALID_NEIGHBOUR_RH'
        elif not (5<=rh[i-1]<=100 and 5<=rh[i+1]<=100 and abs(rh[i-1]-rh[i+1])<=20):
            reason='NEIGHBOUR_RH_INCONSISTENT'
        else:
            nrh=float((rh[i-1]+rh[i+1])/2)
            nv=float(mod.sat(nt)*(1-nrh/100))
            era_rh=float(100*(1-era_v[i]/mod.sat(era[i])))
            if not np.isfinite(era_rh) or abs(nrh-era_rh)>18:
                reason='INTERPOLATED_RH_DISAGREES_WITH_SOURCE_ERA'
            elif not np.isfinite(pa[i]):
                reason='PSRF_MISSING'
            elif not (np.isfinite(nv) and nv>=0):
                reason='VPD_INVALID'
            elif (abs(t[i-1]-nt)>=abs(t[i-1]-t[i]) or
                  abs(t[i+1]-nt)>=abs(t[i+1]-t[i])):
                reason='NO_IMPROVEMENT_OF_BOTH_TEMP_EDGES'
            else:
                after_q=mod.therm(nt,nv,pa[i])[1]
                if not np.isfinite(after_q) or not 0<=after_q<=.08:
                    reason='QBOT_INVALID'
                else:
                    reason='ACCEPTED_ISOLATED_QC1_2_T_VPD_TRIAL'
        holds.append(dict(site=site,event_type='ISOLATED_T_SPIKE',time=str(ix[i]),
                          interval_start=str(ix[i]),interval_end=str(ix[i]),
                          trial_halfhours=1,action='TRIAL_ACCEPTED' if reason.startswith('ACCEPTED') else 'HOLD',
                          reason=reason,old_T_C=t[i],proposed_T_C=nt,
                          source_T_QC=qct[i],source_VPD_QC=qcv[i],source_ERA_T_C=scalar(era[i])))
        if reason.startswith('ACCEPTED') and i not in proposals:
            proposals[i]=(nt,nv,'SINGLE_HH_QC1_2_SPIKE_T_VPD_ERA_SCREENED')
    return proposals,holds


def flag_rain(site,d,src,ix):
    """Strictly diagnostic: rainfall edits are always 0."""
    amount=d.PRECTmms.to_numpy(float)*1800
    raw=src['P_F'].to_numpy(float) if 'P_F' in src else np.full(len(d),np.nan)
    qc=src['P_F_QC'].to_numpy(float) if 'P_F_QC' in src else np.full(len(d),np.nan)
    sites=[]
    ix_2300=(ix.hour==23)&(ix.minute==0)
    for i in np.flatnonzero(amount>18):
        p=amount[i]
        before=amount[i-1] if i and ix[i]-ix[i-1]==pd.Timedelta(minutes=30) else np.nan
        after=amount[i+1] if i+1<len(amount) and ix[i+1]-ix[i]==pd.Timedelta(minutes=30) else np.nan
        # Same-date source match is provenance only, never validation of temporal accumulation.
        sites.append(dict(site=site,time=str(ix[i]),rain_mm_per_HH=float(p),
             source_P_F_mm=scalar(raw[i]),source_P_F_QC=scalar(qc[i]),
             original_equals_candidate=bool(np.isfinite(raw[i]) and abs(raw[i]-p)<1e-4),
             previous_HH_mm=scalar(before),next_HH_mm=scalar(after),
             at_23h00=bool(ix_2300[i]),
             decision=('HOLD_POSSIBLE_DAILY_ACCUMULATION_TIMING_NO_AUTO_CHANGE'
                       if site=='ES-LJu' and ix_2300[i] else
                       'RETAIN_UNCHANGED_INTENSE_RAIN_SOURCE_REVIEW_REQUIRED'),
             scientifically_approved=False))
    return sites


def preflight(args):
    files={
       'stage26_manifest':args.stage26/'01_selected_13site_stage26_provisional_manifest.csv',
       'stage26_qc':args.stage26/'02_all13_numeric_QC_after_trial.csv',
       'stage26_ledger':args.stage26/'05_exact_stage26_trial_ledger.csv',
       'stage22_blocks':args.stage22/'07_82_MDS_blocks_after_stage22.csv',
       'stage22_envelopes':args.stage22/'02_full_QC1_envelope_decisions.csv',
       'source_manifest':args.raw
    }
    for k,p in files.items():ensure(p.is_file(),f'{k} not found: {p}')
    m=pd.read_csv(files['stage26_manifest'])
    q=pd.read_csv(files['stage26_qc'])
    raw=pd.read_csv(files['source_manifest'])
    blocks=pd.read_csv(files['stage22_blocks'])
    envelopes=pd.read_csv(files['stage22_envelopes'])
    ensure(len(m)==13 and set(m.site)==set(ALL) and not m.site.duplicated().any(),
           'Invalid Stage26 selected manifest')
    ensure(len(q)==13 and set(q.site)==set(ALL) and not q.site.duplicated().any(),
           'Invalid Stage26 QC')
    ensure(set(raw.site)>=set(ALL) and not raw.site.duplicated().any(),
           'Invalid original FLUXNET source manifest')
    ensure(len(blocks)==82 and set(blocks.site)=={'DE-Gri','FI-Let'},
           'Stage22 82 MDS block report missing/mismatched')
    ensure(set(envelopes.site)<={'DE-Gri','FI-Let'},'Wrong Stage22 envelopes')
    ensure(int(pd.to_numeric(q.numeric_hard_failures).sum())==0,'Stage26 numeric failure')
    for row in m.itertuples(index=False):
        f=Path(row.forcing_path)
        ensure(f.is_file() and sha(f)==str(row.sha256),f'{row.site}: selected candidate missing or SHA mismatch {f}')
        h=set(pd.read_csv(f,nrows=0).columns)
        ensure(REQUIRED<=h,f'{row.site}: required forcing variables missing: {REQUIRED-h}')
    for row in raw.itertuples(index=False):
        if row.site in TARGETS:
            ensure(Path(row.primary_file).is_file(),f'{row.site}: source file missing')
    print('PREFLIGHT OK: 13 Stage26 selected forcing SHA256, all 7 licensed source files, Stage22 MDS reports',flush=True)
    return files,m,q,raw,blocks,envelopes


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mode',choices=['run','check'],default='run')
    ap.add_argument('--stage26',type=Path,default=DEFAULT_26)
    ap.add_argument('--stage22',type=Path,default=DEFAULT_22)
    ap.add_argument('--raw',type=Path,default=DEFAULT_RAW)
    ap.add_argument('--stage26-script',type=Path,default=HOME/'26_three_site_MET_conservative_trial.py')
    ap.add_argument('--stage20-script',type=Path,default=HOME/'20_onepass_13site_meteorology_preBIF.py')
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    files,m,oldqc,raw,blocks,envelopes=preflight(args)
    if args.mode=='check':
        print('CHECK ONLY: did not write forcing or reports');return 0
    ensure(not args.out.exists(),f'Output exists; refusing overwrite: {args.out}')
    mod=load(args.stage26_script,'stage28_reuse_stage26')
    auditmod=load(args.stage20_script,'stage28_reuse_stage20')
    ensure(all(callable(getattr(mod,z,None)) for z in ('original_data','event_evidence','trial_candidates','build_trial','therm','sat')),
           'Stage26 reuse module has changed')
    ensure(callable(getattr(auditmod,'full_audit',None)),'Stage20 audit module missing full_audit')
    rawidx=raw.set_index('site')
    source_digests={}
    for site in TARGETS:
        row=rawidx.loc[site]
        primary=Path(str(row.primary_file))
        source_digests[str(primary)]=sha(primary)
        if 'companion_file' in row.index and pd.notna(row.companion_file):
            companion=Path(str(row.companion_file))
            if companion.is_file(): source_digests[str(companion)]=sha(companion)
    selected=m.copy().set_index('site')
    # Historical Stage26 selected manifest may already include these metadata fields.
    for field in ['stage28_new_trial_HH','stage28_review_scope','stage28_site_science_status']:
        if field not in selected:selected[field]=0 if field=='stage28_new_trial_HH' else ''
    selected['stage28_site_science_status']='NOT_APPROVED_PROVISIONAL_SCIENCE_PENDING'
    decisions=[];ledger=[];eventevidence=[];rain_rows=[]
    # Process one site at a time to avoid retaining seven full multiyear
    # DataFrames in memory on IRIDIS login nodes.
    args.out.mkdir(parents=True,exist_ok=False)
    rp=args.out/'reports';rp.mkdir()
    for site in TARGETS:
        parent=selected.loc[site]
        d=pd.read_csv(parent.forcing_path,low_memory=False)
        ix=pd.DatetimeIndex(pd.to_datetime(d.time,errors='raise'))
        ensure(ix.is_monotonic_increasing and not ix.has_duplicates,f'{site}: invalid forcing time')
        src=mod.original_data(site,rawidx,ix)
        events,_,_=mod.event_evidence(site,d,src,ix)
        chosen,site_dec=mod.trial_candidates(site,d,src,ix,events,4,4)
        extra,extra_dec=isolated_spike_trials(site,d,src,ix,mod,set(chosen))
        for i,(t,v,meth) in extra.items():
            if i not in chosen:chosen[i]=(t,v,meth)
        trial,new_ledger=mod.build_trial(site,d,src,chosen,ix)
        decisions.extend(site_dec);decisions.extend(extra_dec)
        ledger.extend(new_ledger);eventevidence.extend(events)
        site_rain=flag_rain(site,d,src,ix)
        rain_rows.extend(site_rain)
        print(f'{site:<7} ORIGINAL T>12={sum(e["event_type"]=="T_STEP_GT_12C" for e in events):2} '
              f'RH<1={sum(e["event_type"]=="RH_LT_1PCT" for e in events):2} '
              f'NEW_TRIAL_HH={len(new_ledger):3} HELD={sum(z["action"]=="HOLD" for z in [*site_dec,*extra_dec]):3} '
              f'RAIN>18={len(site_rain):3}',flush=True)
        target=Path(parent.forcing_path)
        if new_ledger:
            outdir=args.out/site/'forcing';outdir.mkdir(parents=True)
            target=outdir/f'{site}_stage28_ERA_screened_short_trial.csv'
            tmp=target.with_suffix('.partial')
            trial.to_csv(tmp,index=False)
            chk=pd.read_csv(tmp,low_memory=False)
            ensure(len(chk)==len(d),f'{site}: roundtrip row count changed')
            # Verify non-MET channels unchanged and all columns outside edited HH unchanged.
            unaffected=[c for c in d.columns if c not in MET]
            for c in unaffected:
                if pd.api.types.is_numeric_dtype(d[c]):
                    eq=np.allclose(pd.to_numeric(d[c],errors='coerce').to_numpy(float),
                                   pd.to_numeric(chk[c],errors='coerce').to_numpy(float),
                                   rtol=1e-10,atol=1e-10,equal_nan=True)
                else:eq=d[c].fillna('__NA__').astype(str).equals(chk[c].fillna('__NA__').astype(str))
                ensure(eq,f'{site}: unexpected change to {c}')
            changed={pd.Timestamp(x['time']) for x in new_ledger}
            keep=~ix.isin(changed)
            for c in MET:
                eq=np.allclose(d[c].to_numpy(float)[keep],chk[c].to_numpy(float)[keep],
                               rtol=1e-10,atol=1e-10,equal_nan=True)
                ensure(eq,f'{site}: changes outside ledger to {c}')
            tmp.rename(target)
            del chk
        selected.loc[site,'forcing_path']=str(target)
        selected.loc[site,'sha256']=sha(target)
        selected.loc[site,'stage28_new_trial_HH']=len(new_ledger)
        selected.loc[site,'stage28_review_scope']='7SITE_TEMPERATURE_VPD_RAIN_MDS_TRIAGE'
        if new_ledger:selected.loc[site,'version']='stage28_bounded_QC1_2_trial'
        del d,trial,src,ix
    # Independently rerun the same audited numeric QC on ALL 13 selected versions.
    # Unlike reusing Stage26 QC for unedited sites, this truly recomputes them all.
    full=[];newflags=[]
    for site in ALL:
        row=selected.loc[site]
        detail,flags=auditmod.full_audit(site,Path(row.forcing_path),raw)
        ensure(detail['numeric_hard_failures']==0,f'{site}: numeric hard QC FAIL')
        ensure(sha(row.forcing_path)==str(row.sha256),f'{site}: SHA mismatch after audit')
        full.append(detail)
        newflags.extend(flags)
        print(f'FINAL AUDIT {site:<7} NUMERIC_PASS T>12={detail["TA_step_gt_12C"]} '
              f'RH<1={detail["RH_below_1pct"]} P>40={detail["rain_gt40mm_per_HH"]}',flush=True)
    qc=pd.DataFrame(full).set_index('site')
    pending=blocks[blocks.stage22_action.isin(MDS_PENDING)].groupby('site').size().to_dict()
    # Report all unchanged Stage22 decisions with original evidence; no fake resolved flags.
    mds=blocks.copy()
    mds['stage28_action']='INHERITED_STAGE22_AS_IS_NO_UNVERIFIED_MODEL_REPLACEMENT'
    mds['scientific_approval']='PENDING'
    summaries=[]
    for site in ALL:
        r=qc.loc[site];p=selected.loc[site]
        suspect23=site=='ES-LJu' and sum(z['site']==site and z['at_23h00'] for z in rain_rows)>=5
        remaining=int(pending.get(site,0))
        mode=('MDS_HIGH_UNCERTAINTY' if remaining else
              'RAIN_ACCUMULATION_TIMING_HIGH_UNCERTAINTY' if suspect23 else
              'SOURCE_BOUNDARY_OR_LOW_RH_REVIEW' if r.TA_step_gt_12C>0 or r.RH_below_1pct>0 else
              'EXTREME_RAIN_PROVENANCE_REVIEW' if r.rain_gt18mm_per_HH>0 else
              'NO_FLAGGED_EXTREMES_IN_AUDITED_THRESHOLDS')
        summaries.append(dict(site=site,scientific_status='PROVISIONAL_NOT_SCIENCE_APPROVED',
            numeric_status='PASS',forcing_path=p.forcing_path,sha256=p.sha256,
            stage28_new_trial_HH=int(p.stage28_new_trial_HH),
            stage22_MDS_flagged_blocks_still_pending_review=remaining,
            T_step_gt12C=int(r.TA_step_gt_12C),RH_lt1pct=int(r.RH_below_1pct),
            rain_gt18mm_perHH=int(r.rain_gt18mm_per_HH),
            rain_gt40mm_perHH=int(r.rain_gt40mm_per_HH),
            heavy_rain_at23h00=int(r.rain_gt18mm_at_2300),
            action_class=mode,
            explicit_retain_and_note=('Do not treat QC2 ERA as independent; full MDS event review remains' if remaining
               else '23:00 precipitation concentration: source aggregation period unverified; no redistribution' if suspect23
               else 'Original QC0 and rainfall preserved; isolated QC1/2 edits are numerical trials only' if site in TARGETS
               else 'Inherited Stage26 candidate unchanged; prior science caveats remain')))
    outputs={
      '01_selected_13site_STAGE28_provisional_manifest.csv':selected.reset_index(),
      '02_all13_full_numeric_QC_after_stage28.csv':qc.reset_index(),
      '03_13site_science_risk_and_decisions.csv':pd.DataFrame(summaries),
      '04_exact_STAGE28_new_edits.csv':pd.DataFrame(ledger,columns=['site','time','method','old_T_C','new_T_C','old_VPD_hPa',
         'new_VPD_hPa','old_RH_pct','new_RH_pct','old_QBOT','new_QBOT','source_TA_QC','source_VPD_QC',
         'source_ERA_T_C','source_ERA_VPD_hPa','scientific_approval']),
      '05_7site_temperature_RH_original_evidence.csv':pd.DataFrame(eventevidence),
      '06_7site_change_decisions_and_holds.csv':pd.DataFrame(decisions),
      '07_7site_heavy_rain_PROVENANCE_NO_EDITS.csv':pd.DataFrame(rain_rows),
      '08_DEGri_FILet_82_MDS_original_blocks_science_pending.csv':mds,
      '09_DEGri_FILet_stage22_whole_envelope_decisions.csv':envelopes,
      '10_all13_remaining_temperature_pressure_rain_RH_flags.csv':pd.DataFrame(newflags),
    }
    for name,df in outputs.items():
        df.to_csv(rp/name,index=False)
    prov={
        'created_utc':datetime.now(timezone.utc).isoformat(),
        'experiment':'FLUXNET_MultiSite_13',
        'stage':'28_onepass_remaining7_MET_finalize',
        'status':'PROVISIONAL_NUMERIC_PASS_ALL_13_SCIENCE_OPEN',
        'input_sha256':{k:sha(v) for k,v in files.items()},
        'source_script_sha256':{'stage26':sha(args.stage26_script),'stage20':sha(args.stage20_script)},
        'original_source_products_sha256':source_digests,
        'input_parent':'Stage26 13-site selected manifest, itself inherits Stage22',
        'reanalysis':'Stage22 cached ERA5/ERA5-Land trials inherited for DE-Gri/FI-Let; '
                    'source downscaled ERA5_HH or legacy ERAI_HH used as weak veto for other seven; '
                    'NOT independent ground truth',
        'approved_for_production_DATM_or_spinup':False,
        'QC0_automatic_edits':0,'precipitation_automatic_edits':0,
        'new_trial_halfhours':len(ledger),
        'notes':['69 Stage22 pending MDS blocks are NOT necessarily 69 errors',
                 'Only short full QC1/2 runs with QC0 endpoints or strict isolated spikes can be trialled',
                 'ES-LJu strong 23:00 rainfall pattern must be checked for source time accumulation',
                 'All original raw source files and Stage22/26 candidates were retained intact']
    }
    (rp/'11_provenance_and_science_gates.json').write_text(json.dumps(prov,indent=2,ensure_ascii=False)+'\n')
    (rp/'README_FINAL_SCOPE_AND_LIMITATIONS.md').write_text(
        '# Stage28 — 13-site selected MET trial after seven-site batch\n\n'
        '## Scope\nAll 13 forcing parents SHA256 verified and fully re-audited using Stage20 '
        'numeric physics screens. Seven targets were reviewed; the other six '
        'inherit their Stage26 selected version. The previously successful '
        'Stage22 ERA5/ERA5-Land MDS full-envelope trials are inherited.\n\n'
        f'New stage28 candidate edits: {len(ledger)} half-hour rows. '
        f'Numerical hard failures: {int(qc.numeric_hard_failures.sum())}. '
        'No automatic changes to original QC0 temperature, pressure, precipitation, '
        'radiation or wind. All changes are candidate trials only.\n\n'
        '## Never silently correct rainfall time accumulation\n'
        'ES-LJu has a distinctive 23:00 heaping of strong rain; P_F may refer to '
        'a reporting/accumulation interval different from 30 minutes. '
        'Until original site metadata confirms period semantics, do NOT '
        'divide daily totals by 48 or redistribute. Flag the site as high risk '
        'for precipitation-driven simulations.\n\n'
        '## Why leftover MDS blocks are held\n'
        'Stage22 screened DE-Gri/FI-Let against cached ERA5 and ERA5-Land, '
        'but its rejection reasons remain scientifically meaningful. The '
        '69 pending flagged blocks are not automatically defined as errors. '
        'Do not lower numerical criteria solely to clear flags.\n\n'
        '## Data approval gates\n'
        '**PROVISIONAL; SCIENCE REVIEW OPEN; NOT AUTHORIZED FOR PRODUCTION DATM/SPIN-UP.**\n'
        'New annual forcing NetCDFs and BIF/ZBOT calibration need separate review.\n'
        'Raw licensed FLUXNET/ICOS, derived met forcing, reanalysis caches, and '
        'original record-level observations should not be placed on public GitHub.\n'
    )
    print('\n=== STAGE28 ONE-PASS COMPLETE ===',flush=True)
    print('Reviewed targets:',','.join(TARGETS),flush=True)
    print('New bounded QC1/2 trial halfhours:',len(ledger),flush=True)
    print('13/13 full numeric QC: PASS',flush=True)
    print('Still pending original MDS flagged blocks:',sum(pending.values()),'(DE-Gri',pending.get('DE-Gri',0),
          'FI-Let',pending.get('FI-Let',0),')',flush=True)
    print('Automatic precipitation edits: ZERO (risk documented)',flush=True)
    print('Scientific MET approval: NONE; all selected versions provisional',flush=True)
    print('REPORTS:',rp,flush=True)
    print('MANIFEST:',rp/'01_selected_13site_STAGE28_provisional_manifest.csv',flush=True)
    return 0


if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:
        print('STAGE28 ERROR:',type(e).__name__,str(e),file=sys.stderr)
        sys.exit(1)

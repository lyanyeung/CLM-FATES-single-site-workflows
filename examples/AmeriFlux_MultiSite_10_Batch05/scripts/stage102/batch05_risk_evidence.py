#!/usr/bin/env python3
"""Batch05 source-risk evidence and out-of-year ERA proxy comparison.

Research diagnostic only: no source, existing overlay or model forcing is edited.
QC0 source comparisons do not validate individual target values or prove that
the processed ERA product is independent of the tower observations.
"""
import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

RAW_SHA = {
 'US-UiD':'130142a3b19b11115a058b45129c3ffbeec685b3e5a4e30232701cc149daf318',
 'US-UMB':'ff2d5144e270e3a629d449e26a7796440d91c780c5c6f29ef4d74d84cea24bd6',
 'US-UMd':'e84f61649a1da11b29799d5ad066898d513c0a93da964cd23bb2b48a676ab2f2',
 'US-Var':'664ffeb53419d5ea7f618b0a4d3bebbd767c2b8406e1d167a7881a256287eed2',
 'US-Vcm':'c12437170ddb54630f87859bb33398994d9eb3f1c84686336e18a26d457e841c',
 'US-Vcp':'eece5582523be1f875799751cef9d6b55a4635bfde2ebb008afba31a9a208a42',
 'US-WCr':'f20fbb064ff68668693f8dc04eb72034d98fc4e6e25d4dfb64c7f201a30bb506',
 'US-Whs':'653f757b7037aa3a6a125ab1160430366b9ffc8c84c8cf0e1eca60652b079cca',
 'US-Wjs':'9b23ab803b719dcb55d2525e4c084c53659e9dea42164fe2382507c97f28bdd6',
 'US-Wkg':'f0359fe0a40a413c15e79a30d1e6264e6e2d36717d7d394db40e818c4e684829'}
OVERLAY_SHA='63809716e8ad452af53b23e38222475d84804e434fa5070e9a02d1eecfaabbce'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError('bad header: '+str(p))
        return list(reader)

def num(x):
    try: v=float(x)
    except (TypeError,ValueError): return None
    return v if math.isfinite(v) and v != -9999 else None

def rh(t,v):
    t=num(t); v=num(v)
    if t is None or v is None or not -80 < t < 70 or v < 0: return None
    return 100*(1-v/(6.112*math.exp(17.67*t/(t+243.5))))

def stamp(s): return datetime.strptime(s,'%Y%m%d%H%M')
def key(r): return (r['site'],r['native_time'])
def write(path,data,fields):
    with path.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(data)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage101',type=Path,required=True)
    ap.add_argument('--stage84',type=Path,required=True)
    ap.add_argument('--stage97',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args(); d=a.stage101.resolve(); out=a.out.resolve()
    if out.exists() or not out.parent.is_dir(): raise ValueError('output must be a new directory')
    manifest=json.loads((d/'stage101_DATM_SCIENCE_SOURCE_SELECTION_PREPARED_NOT_RELEASED_MANIFEST.json').read_text())
    for name,digest in manifest['outputs_SHA256'].items():
        if sha(d/name)!=digest: raise ValueError('Stage101 output hash mismatch: '+name)
    recipe=rows(d/'stage101_BATCH05_TEN_SITE_ACTUAL_FLUXNET_SOURCE_TO_DATM_RECIPES.csv')
    selection=rows(d/'stage101_BATCH05_1782_HH_VERSIONED_SPARSE_SELECTION_AND_HOLD_MATRIX_NOT_DATM.csv')
    risk=rows(d/'stage101_BATCH05_63_ORIGINAL_RELEASE_RISKS_DO_NOT_AUTO_FILL.csv')
    holdfile=a.stage97/'stage97_56_ORIGINAL_HOLD_HH_SCIENCE_DECISION_MATRIX.csv'
    hm=json.loads((a.stage97/'stage97_SOURCE_PROTECTED_HOLDS_CLOSURE_GATE_MANIFEST.json').read_text())
    if hm['output_SHA256'][holdfile.name]!=sha(holdfile): raise ValueError('Stage97 hash mismatch')
    holds=rows(holdfile)
    overlay=a.stage84/'stage84_VERSIONED_1675_USER_APPROVED_RH_VPD_TA_native_overlay.csv'
    if sha(overlay)!=OVERLAY_SHA: raise ValueError('Stage84 overlay hash mismatch')
    ov=rows(overlay); proxies=[r for r in ov if 'ERA' in r['replacement_RH_provenance'].upper()]
    protected={key(r) for r in selection}; held={key(r):r for r in holds}
    tkeys={key(r) for r in risk}&{key(r) for r in ov}
    if (len(recipe)!=10 or {r['site'] for r in recipe}!=set(RAW_SHA) or
        len(selection)!=1782 or len(protected)!=1782 or len(risk)!=63 or
        len(held)!=56 or len(tkeys)!=7 or len(proxies)!=1281 or len({key(r) for r in ov})!=1675):
        raise ValueError('cohort counts or uniqueness do not match prior evidence')
    if any(out==p.resolve() or p.resolve() in out.parents or out in p.resolve().parents
           for p in [d,a.stage84,a.stage97]+[Path(r['original_FLUXNET_source_path']) for r in recipe]):
        raise ValueError('output overlaps input')
    targets=set(held)|tkeys
    wanted=defaultdict(set)
    for site,ts in targets:
        dt=stamp(ts)
        for n in range(-6,7): wanted[site].add((dt+timedelta(minutes=30*n)).strftime('%Y%m%d%H%M'))
    # Each target is scored only against other years, same site/calendar month
    # and same native time of day. Keep sums by year to exclude target year.
    grouped=defaultdict(lambda:[0,0.,0.]); byyear=defaultdict(lambda:[0,0.,0.])
    context={}; source_hash={}; selected_columns={}; missing_comparison_columns={}
    for rec in recipe:
        site=rec['site']; path=Path(rec['original_FLUXNET_source_path'])
        if not path.is_file() or path.is_symlink() or sha(path)!=RAW_SHA[site]:
            raise ValueError('original source missing or SHA mismatch: '+site)
        source_hash[site]=RAW_SHA[site]
        with path.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f); hdr=reader.fieldnames or []
            req={'TIMESTAMP_START','TA_F','VPD_F'}
            comparison={'TA_F_QC','VPD_F_QC','TA_ERA','VPD_ERA'}
            if not req.issubset(hdr) or len(set(hdr))!=len(hdr):
                raise ValueError('required columns missing/duplicate for '+site+': '+str(sorted(req-set(hdr))))
            missing_comparison_columns[site]=sorted(comparison-set(hdr))
            cols=[c for c in hdr if c in req|comparison or c in ('TIMESTAMP_END','RH','RH_F','RH_ERA','PA_F','P_F','P_F_QC','SW_IN_F','SW_IN_F_QC','TA','VPD')]
            selected_columns[site]=cols
            for r in reader:
                ts=r['TIMESTAMP_START']
                if len(ts)!=12 or not ts.isdigit(): raise ValueError('bad source timestamp '+site+' '+ts)
                k=(site,ts)
                if ts in wanted[site]:
                    if k in context: raise ValueError('duplicate target context '+str(k))
                    context[k]={c:r[c] for c in cols}
                if k in protected or num(r.get('TA_F_QC'))!=0 or num(r.get('VPD_F_QC'))!=0: continue
                obs=rh(r['TA_F'],r['VPD_F']); era=rh(r.get('TA_ERA'),r.get('VPD_ERA'))
                if obs is None or era is None or not (0<=obs<=100 and 0<=era<=100): continue
                group=(site,ts[4:6],ts[8:12]); yr=ts[:4]; err=era-obs
                for s in (grouped[group],byyear[group+(yr,)]):
                    s[0]+=1;s[1]+=err;s[2]+=err*err
    if any(k not in context for k in targets): raise ValueError('target not found in original raw source')
    out.mkdir()
    context_rows=[]
    for (site,ts),r in sorted(context.items()):
        z={'site':site,'native_time':ts,'is_hold':str((site,ts) in held),'is_temperature_risk':str((site,ts) in tkeys),
           'derived_source_RH_pct':rh(r.get('TA_F'),r.get('VPD_F')),
           'derived_processed_ERA_RH_pct':rh(r.get('TA_ERA'),r.get('VPD_ERA'))}
        z.update(r);context_rows.append(z)
    fields=['site','native_time','is_hold','is_temperature_risk','derived_source_RH_pct','derived_processed_ERA_RH_pct']
    fields+=sorted(set().union(*(set(r) for r in context_rows))-set(fields))
    write(out/'context_56_holds_and_7_T.csv',context_rows,fields)
    # Linear interpolation is only a counterfactual using two source QC0
    # donors within 3 hours, not a validated replacement or release.
    humidity=[]
    for (site,ts),heldrow in sorted(held.items()):
        dt=stamp(ts); donors=[]
        for direction in (-1,1):
            donor=None
            for n in range(1,7):
                at=(dt+timedelta(minutes=30*n*direction)).strftime('%Y%m%d%H%M'); k=(site,at); r=context.get(k)
                val=rh(r.get('TA_F'),r.get('VPD_F')) if r else None
                if (r and k not in protected and num(r.get('TA_F_QC'))==0 and
                    num(r.get('VPD_F_QC'))==0 and val is not None and 0<=val<=100):
                    donor=(n,val);break
            donors.append(donor)
        left,right=donors; raw=context[(site,ts)]; t=num(raw.get('TA_F')); trial=None; vpd=None
        if left and right and t is not None and -80<t<70:
            trial=(left[1]*right[0]+right[1]*left[0])/(left[0]+right[0])
            vpd=6.112*math.exp(17.67*t/(t+243.5))*(1-trial/100)
        humidity.append(dict(site=site,native_time=ts,review_group=heldrow['review_group'],
            source_T_C=raw.get('TA_F'),source_T_QC=raw.get('TA_F_QC'),source_VPD_hPa=raw.get('VPD_F'),
            source_VPD_QC=raw.get('VPD_F_QC'),source_RH_pct=rh(raw.get('TA_F'),raw.get('VPD_F')),
            source_ERA_RH_pct=rh(raw.get('TA_ERA'),raw.get('VPD_ERA')),
            left_minutes=left[0]*30 if left else '',left_RH_pct=round(left[1],4) if left else '',
            right_minutes=right[0]*30 if right else '',right_RH_pct=round(right[1],4) if right else '',
            interpolated_RH_pct=round(trial,4) if trial is not None else '',
            interpolated_VPD_hPa=round(vpd,4) if vpd is not None else '',
            status='HOLD_SENSITIVITY_ONLY_NOT_APPROVED'))
    write(out/'humidity_56_anchor_sensitivity.csv',humidity,list(humidity[0]))
    oidx={key(r):r for r in ov}; temps=[]
    for site,ts in sorted(tkeys):
        dt=stamp(ts); candidates=[]
        for direction in (-1,1):
            anchor=None
            for n in range(1,7):
                at=(dt+timedelta(minutes=30*n*direction)).strftime('%Y%m%d%H%M'); k=(site,at); r=context.get(k)
                if r and k not in protected and num(r.get('TA_F_QC'))==0 and num(r.get('TA_F')) is not None:
                    anchor=(n,r);break
            candidates.append(anchor)
        left,right=candidates; value=None
        if left and right: value=(num(left[1]['TA_F'])*right[0]+num(right[1]['TA_F'])*left[0])/(left[0]+right[0])
        raw=context[(site,ts)]; old=oidx[(site,ts)]
        temps.append(dict(site=site,native_time=ts,source_T_C=raw['TA_F'],source_T_QC=raw.get('TA_F_QC',''),
          overlay_T_C=old['modified_TA_C'],overlay_RH_pct=old['modified_RH_pct'],
          left_minutes=left[0]*30 if left else '',left_T_C=left[1]['TA_F'] if left else '',
          right_minutes=right[0]*30 if right else '',right_T_C=right[1]['TA_F'] if right else '',
          interpolated_T_C=round(value,6) if value is not None else '',
          status='SENSITIVITY_ONLY_NOT_APPROVED'))
    write(out/'temperature_7_anchor_sensitivity.csv',temps,list(temps[0]))
    validation=[]
    for r in proxies:
        site,ts=key(r); group=(site,ts[4:6],ts[8:12]); allv=grouped[group]; yr=byyear[group+(ts[:4],)]
        n=allv[0]-yr[0]; total=allv[1]-yr[1]; sq=allv[2]-yr[2]
        validation.append(dict(site=site,native_time=ts,method=r['replacement_RH_provenance'],
          target_year_excluded=ts[:4],reference_QC0_same_month_and_clock_other_years=n,
          ERA_minus_tower_RH_bias_pp=round(total/n,4) if n else '',
          ERA_minus_tower_RH_RMSE_pp=round(math.sqrt(max(0,sq/n)),4) if n else '',
          status='COMPARISON_ONLY_NOT_TARGET_VALIDATION'))
    write(out/'era_proxy_1281_other_year_QC0_comparison.csv',validation,list(validation[0]))
    summary=[]
    for site in sorted(RAW_SHA):
        v=[r for r in validation if r['site']==site]; ns=[r['reference_QC0_same_month_and_clock_other_years'] for r in v]
        biases=sorted(r['ERA_minus_tower_RH_bias_pp'] for r in v if r['ERA_minus_tower_RH_bias_pp']!='')
        rmses=sorted(r['ERA_minus_tower_RH_RMSE_pp'] for r in v if r['ERA_minus_tower_RH_RMSE_pp']!='')
        summary.append(dict(site=site,proxy_targets=len(v),targets_no_reference=sum(n==0 for n in ns),
          targets_under_30_reference=sum(n<30 for n in ns),reference_n_min=min(ns) if ns else '',
          reference_n_median=sorted(ns)[len(ns)//2] if ns else '',reference_n_max=max(ns) if ns else '',
          median_target_stratum_bias_pp=biases[len(biases)//2] if biases else '',
          median_target_stratum_RMSE_pp=rmses[len(rmses)//2] if rmses else '',
          max_target_stratum_RMSE_pp=max(rmses) if rmses else ''))
    write(out/'proxy_comparison_site_summary.csv',summary,list(summary[0]))
    report=dict(stage=102,status='EVIDENCE_ONLY_NOT_RELEASED',holds=56,temperature_risks=7,proxy_targets=1281,
        comparison='same site, calendar month, native time, other years; original TA_F_QC=VPD_F_QC=0; valid physical RH; exclude all Stage101 sparse keys',
        comparison_caveat='Not pointwise validation. Reference may be dependent on source ERA processing; provenance must be checked. No threshold implies approval.',
        source_sha256=source_hash,source_columns=selected_columns,missing_comparison_columns=missing_comparison_columns,stage101_manifest_sha256=sha(d/'stage101_DATM_SCIENCE_SOURCE_SELECTION_PREPARED_NOT_RELEASED_MANIFEST.json'),
        output_sha256={p.name:sha(p) for p in out.iterdir() if p.is_file()})
    (out/'manifest.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('STAGE102 SUCCESS: 56 HOLD + 7 T evidence; 1281 proxy comparisons; NOT RELEASED')
    print('STAGE102 HOLD GROUPS',json.dumps(dict(Counter(r['review_group'] for r in holds)),sort_keys=True))
    print('STAGE102 MISSING COMPARISON COLUMNS',json.dumps(missing_comparison_columns,sort_keys=True))
    print('STAGE102 HOLD SENSITIVITY',json.dumps(humidity,sort_keys=True))
    print('STAGE102 TEMPERATURE',json.dumps(temps,sort_keys=True))
    print('STAGE102 PROXY SUMMARY',json.dumps(summary,sort_keys=True))
    print('STAGE102 REPORTS='+str(out))
    print('STAGE102: original sources and research overlays unchanged; no DATM or Slurm')

if __name__=='__main__': main()


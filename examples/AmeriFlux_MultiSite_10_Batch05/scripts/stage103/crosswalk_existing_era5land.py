#!/usr/bin/env python3
"""Join Stage102 risk evidence to actual Stage31 and Stage34 ERA5-Land.

The resulting candidates are sensitivity scenarios, not validated forcing.
ERA5-Land is gridded and may share lineage with the processed ERA product.
"""
import argparse,csv,hashlib,json,math,statistics
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:
        d=csv.DictReader(f)
        if not d.fieldnames or len(d.fieldnames)!=len(set(d.fieldnames)): raise ValueError('invalid CSV '+str(path))
        data=list(d)
        if any(None in row for row in data): raise ValueError('malformed CSV '+str(path))
        return data
def num(s):
    try: x=float(s)
    except (TypeError,ValueError): return None
    return x if math.isfinite(x) and x not in (-9999,-6999) else None
def key(r): return (r['site'],r['native_time'])
def index(data):
    result={}
    for r in data:
        k=key(r)
        if k in result: raise ValueError('duplicate key '+str(k))
        result[k]=r
    return result
def write(p,data):
    with p.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
def near(a,b,tol=.003):
    a=num(a); b=num(b)
    return a is not None and b is not None and abs(a-b)<=tol
def dt(s): return datetime.strptime(s,'%Y%m%d%H%M')
def ts(d): return d.strftime('%Y%m%d%H%M')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('stage102','stage31','stage34','out'): p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args(); d102=a.stage102.resolve(); d31=a.stage31.resolve(); d34=a.stage34.resolve(); out=a.out.resolve()
    if out.exists() or not out.parent.is_dir() or any(out==d or out in d.parents or d in out.parents for d in (d102,d31,d34)):
        raise ValueError('output must be new and disjoint from inputs')
    m102=json.loads((d102/'manifest.json').read_text())
    if (m102.get('stage'),m102.get('holds'),m102.get('temperature_risks'),m102.get('proxy_targets'))!=(102,56,7,1281): raise ValueError('Stage102 manifest mismatch')
    for name,sha in m102['output_sha256'].items():
        if digest(d102/name)!=sha: raise ValueError('Stage102 hash mismatch '+name)
    m31=json.loads((d31/'stage31_summary.json').read_text())
    m34=json.loads((d34/'stage34_manifest.json').read_text())
    if (m31.get('verified_source_H01_original_HOLD_half_hours')!=19 or m31.get('original_CDS_file_sha256')!='abda0a706aef79dc0eb7a8b50db1b66ed427c8a756b81965d9bb3dba2e315646' or
        m34.get('source_downloads_verified')!=10 or m34.get('downloaded_reference_joined_unique_native_HH')!=429 or m34.get('P1_nonH01_HOLD_27_external_ref_matched')!=27):
        raise ValueError('Stage31/34 manifest counts or payload provenance mismatch')
    f31=d31/'stage31_H01_19_HH_EXTERNAL_ERA5L_T_TD_RH_VPD_RESEARCH_ONLY.csv'
    f34=d34/'stage34_ALL_MATCHED_EXTERNAL_ERA5LAND_REFERENCE_SCIENCE_REVIEW_ONLY.csv'
    r31=index(read(f31));r34=index(read(f34))
    if len(r31)!=19 or len(r34)!=429: raise ValueError('Stage31/34 row count mismatch')
    h=index(read(d102/'humidity_56_anchor_sensitivity.csv'))
    ctx=index(read(d102/'context_56_holds_and_7_T.csv'))
    proxy=index(read(d102/'era_proxy_1281_other_year_QC0_comparison.csv'))
    if (len(h),len(proxy))!=(56,1281): raise ValueError('Stage102 key count mismatch')
    result=[]
    for k,row in sorted(h.items()):
        if (k in r31)==(k in r34): raise ValueError('HOLD must match exactly one reference '+str(k))
        ref=r31[k] if k in r31 else r34[k]; is31=k in r31
        torig=ref['original_tower_T_C'] if is31 else ref['source_original_T_C']
        vorig=ref['original_tower_VPD_hPa'] if is31 else ref['source_original_VPD_hPa']
        if not near(row['source_T_C'],torig) or not near(row['source_VPD_hPa'],vorig): raise ValueError('source values do not match Stage102 '+str(k))
        rh=ref['ERA5L_RH_water_pct'] if is31 else ref['ERA5Land_reference_RH_water_pct']
        tg=ref['ERA5L_interpolated_T_C'] if is31 else ref['ERA5Land_reference_T_C']
        vr=ref['VPD_if_ERA5L_RH_carried_to_tower_T_hPa'] if is31 else ref['candidate_VPD_original_T_preserve_ref_RH_water_hPa']
        ve=ref['VPD_if_ERA5L_actual_vapour_pressure_carried_to_tower_T_hPa'] if is31 else ref['candidate_VPD_original_T_preserve_ref_actual_e_hPa']
        if any(num(x) is None for x in (rh,tg,vr,ve)) or not 0<=num(rh)<=100: raise ValueError('invalid grid trial '+str(k))
        if not is31 and ref['source_population'] not in ('P1_MANUAL_HOLD','RH_SATURATION_PLATFORM_UNAPPROVED'): raise ValueError('reference population mismatch '+str(k))
        result.append(dict(site=k[0],native_time=k[1],group=row['review_group'],reference_stage='31' if is31 else '34',
          original_T_C=row['source_T_C'],original_T_QC=row['source_T_QC'],original_VPD_hPa=row['source_VPD_hPa'],original_VPD_QC=row['source_VPD_QC'],
          original_RH_pct=row['source_RH_pct'],reference_T_C=tg,reference_RH_water_pct=rh,
          reference_minus_original_T_C=round(num(tg)-num(torig),4),trial_keep_grid_RH_VPD_hPa=vr,trial_keep_grid_vapor_pressure_VPD_hPa=ve,
          transport_difference_hPa=round(num(vr)-num(ve),6),negative_vapor_pressure_transfer_VPD=num(ve)<0,
          candidate_local_anchor_RH_pct=row['interpolated_RH_pct'],status='HOLD_RESEARCH_SCENARIOS_ONLY'))
    ri=index(result); episodes=[]
    for site in sorted({k[0] for k in h}):
        times=sorted(dt(k[1]) for k in h if k[0]==site); runs=[]
        for t in times:
            if not runs or t-runs[-1][-1]!=timedelta(minutes=30): runs.append([t])
            else: runs[-1].append(t)
        for run in runs:
            first,last=run[0],run[-1]; group=[ri[(site,ts(t))] for t in run]; edges=[]
            for when,nearrow in ((first-timedelta(minutes=30),group[0]),(last+timedelta(minutes=30),group[-1])):
                adj=ctx.get((site,ts(when)),{}); av=num(adj.get('VPD_F')); q=adj.get('VPD_F_QC','')
                edges.append(dict(time=ts(when),source_vpd=av if av is not None else '',source_qc=q,
                  delta_rh=round(num(nearrow['trial_keep_grid_RH_VPD_hPa'])-av,4) if av is not None else '',
                  delta_e=round(num(nearrow['trial_keep_grid_vapor_pressure_VPD_hPa'])-av,4) if av is not None else ''))
            episodes.append(dict(site=site,start=ts(first),end=ts(last),count=len(run),groups=';'.join(sorted({x['group'] for x in group})),
              left_time=edges[0]['time'],left_original_VPD=edges[0]['source_vpd'],left_QC=edges[0]['source_qc'],left_jump_RH=edges[0]['delta_rh'],left_jump_e=edges[0]['delta_e'],
              right_time=edges[1]['time'],right_original_VPD=edges[1]['source_vpd'],right_QC=edges[1]['source_qc'],right_jump_RH=edges[1]['delta_rh'],right_jump_e=edges[1]['delta_e'],
              max_abs_temperature_difference_C=round(max(abs(x['reference_minus_original_T_C']) for x in group),4),
              max_abs_transport_difference_hPa=round(max(abs(x['transport_difference_hPa']) for x in group),4),
              negative_e_transfer_count=sum(x['negative_vapor_pressure_transfer_VPD'] for x in group),status='HOLD_BOUNDARY_AND_CLOCK_REVIEW'))
    comparison=[]
    for k in sorted(set(proxy)&set(r34)):
        r=r34[k]; er=num(r['source_processed_ERA_RH_pct']); gr=num(r['ERA5Land_reference_RH_water_pct'])
        comparison.append(dict(site=k[0],native_time=k[1],source_ERA_RH_pct=er if er is not None else '',grid_RH_pct=gr if gr is not None else '',
          grid_minus_source_ERA_RH_pp=round(gr-er,4) if er is not None and gr is not None else '',
          source_grid_T_difference_C=r['ERA5Land_T_minus_source_T_C'],caveat='RELATED_REANALYSES_NOT_INDEPENDENT_IN_SITU'))
    counts=Counter(x['site'] for x in comparison); proxy_sites=Counter(k[0] for k in proxy)
    summary=[]
    for site in sorted(proxy_sites):
        diffs=[x['grid_minus_source_ERA_RH_pp'] for x in comparison if x['site']==site and x['grid_minus_source_ERA_RH_pp']!='']
        summary.append(dict(site=site,all_proxy_HH=proxy_sites[site],matching_ERA5Land_HH=counts[site],valid_RH_pair_HH=len(diffs),
          median_abs_RH_difference_pp=round(statistics.median(abs(v) for v in diffs),4) if diffs else '',
          difference_gt10pp=sum(abs(v)>10 for v in diffs),difference_gt20pp=sum(abs(v)>20 for v in diffs)))
    out.mkdir();write(out/'hold_56_era5land_sensitivity.csv',result);write(out/'hold_episodes_boundary_review.csv',episodes)
    if comparison:write(out/'proxy_era5land_exact_matches.csv',comparison)
    write(out/'proxy_exact_match_summary.csv',summary)
    inputs=[f31,d31/'stage31_summary.json',f34,d34/'stage34_manifest.json',d102/'manifest.json']
    report=dict(stage=103,hold_count=len(result),episodes=len(episodes),proxy_count=len(proxy),proxy_ERA5Land_matches=len(comparison),
      note='Stage31/34 report CSV hashes recorded here, not independently pinned in their original manifests. Source T/VPD and key joins cross-checked against SHA-verified Stage102. Review original CDS provenance and clock before decisions.',
      related_reanalyses_not_independent_in_situ=True,original_hold_released=False,production_forcing_written=False,
      input_sha256={str(x):digest(x) for x in inputs},outputs_sha256={x.name:digest(x) for x in out.iterdir()})
    (out/'manifest.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('STAGE103 SUCCESS | existing ERA5-Land matched to 56 HOLDs; scenarios only')
    print('STAGE103 EPISODES',json.dumps(episodes,sort_keys=True))
    print('STAGE103 HOLD_COLUMNS site time source_T source_VPD reference_T reference_RH trial_VPD_RH trial_VPD_e')
    for r in result:
        print('STAGE103 HOLD',r['site'],r['native_time'],r['original_T_C'],r['original_VPD_hPa'],r['reference_T_C'],r['reference_RH_water_pct'],r['trial_keep_grid_RH_VPD_hPa'],r['trial_keep_grid_vapor_pressure_VPD_hPa'])
    print('STAGE103 PROXY MATCH SUMMARY',json.dumps(summary,sort_keys=True))
    print('STAGE103 INPUT SHA256',json.dumps(report['input_sha256'],sort_keys=True))
    print('STAGE103 REPORTS='+str(out))
    print('STAGE103 HOLDs retained; no original, research overlay, production DATM or Slurm modifications')
if __name__=='__main__': main()


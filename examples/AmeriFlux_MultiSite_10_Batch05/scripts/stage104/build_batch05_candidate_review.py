#!/usr/bin/env python3
"""Stage104: isolated Batch05 repair alternatives and proxy audit, NOT DATM.

No original/Stage84/Stage89 values are modified; all proposed values retain
unreleased status. ERA5-Land references are gridded, not tower observations.
"""
import argparse,csv,hashlib,json,math
from collections import Counter
from pathlib import Path

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:
        d=csv.DictReader(f)
        if not d.fieldnames or len(set(d.fieldnames))!=len(d.fieldnames):raise ValueError('invalid CSV '+str(p))
        rows=list(d)
        if any(None in r for r in rows):raise ValueError('malformed CSV '+str(p))
        return rows
def index(rows):
    x={}
    for r in rows:
        k=(r['site'],r['native_time'])
        if k in x:raise ValueError('duplicate key '+str(k))
        x[k]=r
    return x
def num(v):
    try:x=float(v)
    except (TypeError,ValueError):return None
    return x if math.isfinite(x) and x not in (-9999,-6999) else None
def write(p,rows):
    with p.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def check_manifest(d,stage,countfields):
    f=d/'manifest.json';m=json.loads(f.read_text())
    if m.get('stage')!=stage or any(m.get(k)!=v for k,v in countfields.items()):raise ValueError('manifest counts mismatch '+str(f))
    key='output_sha256' if stage==102 else 'outputs_sha256'
    for name,digest in m[key].items():
        if Path(name).name!=name or sha(d/name)!=digest:raise ValueError('output hash mismatch '+name)
    return m
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ('stage102','stage103','out'):ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();d102=a.stage102.resolve();d103=a.stage103.resolve();out=a.out.resolve()
    if out.exists() or not out.parent.is_dir() or any(out==d or out in d.parents or d in out.parents for d in (d102,d103)):
        raise ValueError('output must be new and disjoint')
    check_manifest(d102,102,dict(holds=56,temperature_risks=7,proxy_targets=1281))
    m103=check_manifest(d103,103,dict(hold_count=56,proxy_count=1281))
    # Ensure Stage103 was made from exactly these Stage102 outputs, not a
    # similarly named earlier run. Stage103 records the actual manifest hash.
    if sha(d102/'manifest.json') not in m103['input_sha256'].values():raise ValueError('Stage103 and Stage102 provenance mismatch')
    h=index(read(d103/'hold_56_era5land_sensitivity.csv'));p=index(read(d102/'era_proxy_1281_other_year_QC0_comparison.csv'))
    matching=index(read(d103/'proxy_era5land_exact_matches.csv'));temp=read(d102/'temperature_7_anchor_sensitivity.csv')
    if len(h)!=56 or len(p)!=1281 or len(matching)!=m103['proxy_ERA5Land_matches'] or len(temp)!=7 or not set(matching)<=set(p):raise ValueError('source join count mismatch')
    candidates=[]
    for k,r in sorted(h.items()):
        qc_t=num(r['original_T_QC']);qc_v=num(r['original_VPD_QC']);rh=num(r['reference_RH_water_pct']);vpd=num(r['trial_keep_grid_RH_VPD_hPa']);e=num(r['trial_keep_grid_vapor_pressure_VPD_hPa'])
        if any(x is None for x in (qc_t,qc_v,rh,vpd,e)) or not 0<=rh<=100 or vpd<0:raise ValueError('invalid candidate '+str(k))
        if qc_t==2 and qc_v==2: lane='QC2_ERA5LAND_MOISTURE_ALTERNATIVES_REVIEW'
        elif qc_t==0 and qc_v==0: lane='QC0_RETAIN_ORIGINAL_PENDING_SENSOR_CONTEXT'
        else:lane='OTHER_QC_MANUAL_REVIEW'
        candidates.append(dict(site=k[0],native_time=k[1],review_group=r['group'],original_T_C=r['original_T_C'],original_T_QC=r['original_T_QC'],
          original_VPD_hPa=r['original_VPD_hPa'],original_VPD_QC=r['original_VPD_QC'],original_RH_pct=r['original_RH_pct'],
          ERA5Land_reference_T_C=r['reference_T_C'],ERA5Land_reference_RH_pct=r['reference_RH_water_pct'],
          scenario_A_VPD_preserve_grid_RH_hPa=round(vpd,8),scenario_B_VPD_preserve_grid_vapor_pressure_hPa=round(e,8),
          scenario_B_negative_vpd=e<0,scenario_B_usable_for_standard_nonnegative_vpd=e>=0,
          lane=lane,selected_repair='NONE',model_DATM_allowed='NO',notes='Source T retained for sensitivity; grid is not in-situ; UTC and height uncertainty remain'))
    lanes=Counter(r['lane'] for r in candidates)
    if sum(lanes.values())!=56:raise ValueError('QC source cohort changed '+str(lanes))
    repairs=[]
    for r in temp:
        k=(r['site'],r['native_time']); original=num(r['source_T_C']); candidate=num(r['interpolated_T_C'])
        if original is None:raise ValueError('invalid temperature source '+str(k))
        if candidate is None:decision='NO_TWO_SIDED_QC0_BRACKET_IN_3H_HOLD'
        elif abs(original-candidate)<=0.1:decision='SOURCE_T_CLOSE_TO_BRACKET_REVIEW_RETAIN'
        else:decision='BRACKET_SENSITIVITY_REQUIRES_EVENT_REVIEW'
        repairs.append(dict(site=k[0],native_time=k[1],source_T_C=original,source_QC=r['source_T_QC'],
          bracket_T_C=candidate if candidate is not None else '',source_minus_bracket_C=round(original-candidate,4) if candidate is not None else '',
          overlay_RH_pct=r['overlay_RH_pct'],left_minutes=r['left_minutes'],right_minutes=r['right_minutes'],
          disposition=decision,selected_T_change='NONE',model_DATM_allowed='NO'))
    proxy=[]
    for k,r in sorted(p.items()):
        ref=matching.get(k);diff=num(ref['grid_minus_source_ERA_RH_pp']) if ref else None
        proxy.append(dict(site=k[0],native_time=k[1],method=r['method'],reference_other_year_QC0_count=r['reference_QC0_same_month_and_clock_other_years'],
          reference_bias_pp=r['ERA_minus_tower_RH_bias_pp'],reference_RMSE_pp=r['ERA_minus_tower_RH_RMSE_pp'],
          ERA5Land_exact_match='YES' if ref else 'NO',ERA5Land_minus_processed_ERA_RH_pp=diff if diff is not None else '',
          agreement_larger_than_10pp=(abs(diff)>10) if diff is not None else '',
          status='RESEARCH_ONLY_NOT_POINT_VALIDATED'))
    print('STAGE104 SELF CHECK',len(candidates),'held records',len(repairs),'T records',len(proxy),'proxy records')
    out.mkdir();write(out/'humidity_56_alternative_scenarios_NOT_DATM.csv',candidates);write(out/'temperature_7_disposition_NOT_DATM.csv',repairs);write(out/'proxy_1281_evidence_NOT_VALIDATED.csv',proxy)
    meta=dict(stage=104,humidity_HH=len(candidates),temperature_HH=len(repairs),ERA_proxy_HH=len(proxy),
      source_QC_lanes=dict(lanes),negative_vpd_vapor_pressure_scenario=sum(r['scenario_B_negative_vpd'] for r in candidates),
      exact_grid_proxy_matches=len(matching),grid_proxy_abs_RH_difference_gt10pp=sum(r['agreement_larger_than_10pp'] is True for r in proxy),
      input_sha256={str(d102/'manifest.json'):sha(d102/'manifest.json'),str(d103/'manifest.json'):sha(d103/'manifest.json')},
      actual_candidate_selection='NONE',all_holds_retained=True,all_source_QC_unchanged=True,production_DATM_written=False,Slurm_submitted=False,
      caution='ERA5-Land is gridded and potentially related to source ERA. QC2 source temperatures and time mapping remain uncertain; isolated scenarios are not final repairs.',
      output_sha256={x.name:sha(x) for x in out.iterdir()})
    (out/'manifest.json').write_text(json.dumps(meta,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('STAGE104 SUMMARY',json.dumps(meta,sort_keys=True))
    print('STAGE104 TEMPERATURE',json.dumps(repairs,sort_keys=True))
    print('STAGE104 REPORTS='+str(out))
    print('STAGE104 SCENARIOS ONLY: no change to source, previous research overlay, DATM, or Slurm')
if __name__=='__main__':main()


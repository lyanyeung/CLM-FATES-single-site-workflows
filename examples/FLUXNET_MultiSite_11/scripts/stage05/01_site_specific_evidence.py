#!/usr/bin/env python3
"""Read-only, site-specific evidence audit for unresolved stage03 meteorology.
Reuses the *actual* stage03 raw parser, thresholds, and event-index, but applies NO corrections.
Output reports preserve every source's values and official FLUXNET _F_QC codes.
"""
from pathlib import Path
import argparse
import importlib.util
import sys
import numpy as np
import pandas as pd

CHECK = ('CH-Aws','CH-Fru','CH-Lae','CZ-Stn')
MET = ('TA','VPD','PA','SW_IN','LW_IN','WS','P')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE'))
    p.add_argument('--stage03',type=Path,default=Path.home()/'FLUXNET_MultiSite_11_stage03/01_merge_11_source_aware.py')
    p.add_argument('--event-root',type=Path,default=Path.home()/'FLUXNET_MultiSite_11/stage03_merge_qc')
    p.add_argument('--out',type=Path,default=Path.home()/'FLUXNET_MultiSite_11/stage05_site_specific_evidence')
    p.add_argument('--sites',nargs='+',default=list(CHECK))
    args=p.parse_args()
    spec=importlib.util.spec_from_file_location('stage03_module',args.stage03)
    if not spec or not spec.loader:raise SystemExit(f'Cannot import {args.stage03}')
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    args.out.mkdir(parents=True,exist_ok=True)
    evidence=[]; events_out=[]; near=[]; summary=[]; errors=[]
    for site in args.sites:
        print(f'\n=== {site} ===',flush=True)
        try:
            first,last,_=m.SITES[site]
            path=args.event_root/f'{site}_humidity_review.csv'
            e=pd.read_csv(path,dtype={'time':'string'})
            if e.empty:
                print('No unresolved stage03 events')
                continue
            e['time']=pd.to_datetime(e['time'],errors='raise')
            files=m.selected_files(args.root/site/'forcing')
            raw={k:m.parse_one(f,first,last) for k,f in files.items()}
            # Collect each original source independently; never silently cross-fill.
            for event in e.itertuples(index=False):
                tm=event.time
                record={'site':site,'time':str(tm),'year':tm.year,'stage03_reason':event.reason,
                        'selected_stage03_source':getattr(event,'pair_source','')}
                events_out.append(record)
                for key,d in raw.items():
                    row={'site':site,'time':str(tm),'year':tm.year,'stage03_reason':event.reason,
                         'source':key,'source_filename':files[key].name}
                    suffix='_ERA' if 'ERA5' in key else '_F'
                    source_row=d.loc[tm] if tm in d.index else None
                    for v in MET:
                        col=v+suffix
                        row[v]=float(source_row[col]) if source_row is not None and col in d and pd.notna(source_row[col]) else np.nan
                        qc=v+'_F_QC'
                        row[v+'_QC']=float(source_row[qc]) if source_row is not None and 'ERA' not in key and qc in d and pd.notna(source_row[qc]) else np.nan
                    t,v,pa=row['TA'],row['VPD'],row['PA']
                    valid,q,rh,ea=m.humidity_status(np.array([t]),np.array([v]),np.array([pa]))
                    row.update({'physical_pair_pass':bool(valid[0]),'RH_pct':float(rh[0]),
                                'actual_vapour_hPa':float(ea[0]),'QBOT_kgkg':float(q[0]),
                                'saturation_vapour_hPa':float(m.es_hpa(np.array([t]))[0]) if np.isfinite(t) else np.nan})
                    evidence.append(row)
                    if key.endswith('_F'):
                        for offset in (-2,-1,0,1,2):
                            nt=tm+pd.Timedelta(minutes=30*offset)
                            nr=d.loc[nt] if nt in d.index else None
                            near.append({'site':site,'event_time':str(tm),'source':key,'offset_halfhours':offset,
                                         'neighbor_time':str(nt),
                                         **{v:float(nr[v+'_F']) if nr is not None and v+'_F' in d and pd.notna(nr[v+'_F']) else np.nan for v in MET}})
            print(f'Unresolved event times: {len(e)}; sources: {list(raw)}',flush=True)
            obs=pd.DataFrame([r for r in evidence if r['site']==site])
            piv=obs.pivot(index='time',columns='source',values=['TA','VPD','PA'])
            fsrc=next((k for k in raw if k.endswith('_F')),None)
            era=next((k for k in raw if k.endswith('_ERA5')),None)
            both=identical=0
            if fsrc and era and ('TA',fsrc) in piv and ('TA',era) in piv:
                a=piv.xs(fsrc,level=1,axis=1)[['TA','VPD','PA']].to_numpy(float)
                b=piv.xs(era,level=1,axis=1)[['TA','VPD','PA']].to_numpy(float)
                available=np.isfinite(a).all(axis=1)&np.isfinite(b).all(axis=1)
                identical=int(np.sum(available&np.all(np.isclose(a,b,rtol=0,atol=1e-6),axis=1)))
                both=int(available.sum())
            f=obs[obs.source==fsrc] if fsrc else pd.DataFrame()
            fe=obs[obs.source==era] if era else pd.DataFrame()
            bad_f=int((~f.physical_pair_pass).sum()) if len(f) else 0
            bad_era=int((~fe.physical_pair_pass).sum()) if len(fe) else 0
            pattern=int(((f.TA.abs()<.0005)&((f.VPD-6.110).abs()<.008)).sum()) if len(f) else 0
            qcf=f[[v+'_QC' for v in ('TA','VPD','PA')]].fillna(-99).astype(int).astype(str).agg('/'.join,axis=1).value_counts().head(12).to_dict() if len(f) else {}
            print(f'F invalid={bad_f}; ERA invalid={bad_era}; exact F=ERA TA/VPD/PA={identical}/{both}')
            print(f'F TA=0,VPD~6.110 motif={pattern}; F official QC triples={qcf}')
            print('F first sample rows (not corrected):')
            if len(f):print(f[['time','TA','VPD','PA','RH_pct','QBOT_kgkg','TA_QC','VPD_QC','PA_QC']].head(8).round(5).to_string(index=False))
            summary.append({'site':site,'event_count':len(e),'F_invalid_at_events':bad_f,
                            'ERA_invalid_at_events':bad_era,'F_and_ERA_triplets_identical':identical,
                            'F_ERA_both_present':both,'F_zeroTA_6p110VPD':pattern,
                            'F_QC_triplet_distribution':str(qcf)})
        except Exception as exc:
            errors.append({'site':site,'error':repr(exc)})
            print('ERROR:',repr(exc),flush=True)
    pd.DataFrame(evidence).to_csv(args.out/'01_source_event_values_and_official_QC.csv',index=False)
    pd.DataFrame(near).to_csv(args.out/'02_event_neighbors_F.csv',index=False)
    pd.DataFrame(events_out).to_csv(args.out/'03_event_index.csv',index=False)
    pd.DataFrame(summary).to_csv(args.out/'04_site_summary.csv',index=False)
    pd.DataFrame(errors,columns=['site','error']).to_csv(args.out/'05_errors.csv',index=False)
    print('\n=== SITE SUMMARY ===',flush=True)
    print(pd.DataFrame(summary).to_string(index=False),flush=True)
    print('Reports:',args.out,flush=True)
    print('READ ONLY: no source, merged, surface, or DATM changes.',flush=True)
    if errors:sys.exit(2)

if __name__=='__main__':main()

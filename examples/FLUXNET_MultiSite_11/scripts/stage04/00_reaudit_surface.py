#!/usr/bin/env python3
"""Read-only, shape-aware Surface/PFT audit for 11-site experiment.
Does NOT assume 16 PFT slots. Reports original stage03 errors and actual NetCDF dimensions.
"""
from pathlib import Path
import csv
import json
import numpy as np
import pandas as pd
from netCDF4 import Dataset

ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
OUT=Path.home()/'FLUXNET_MultiSite_11/stage04_diagnostics'
OUT.mkdir(parents=True, exist_ok=True)
SITES=['BE-Bra','FR-Fon','GL-ZaH','IT-Noe','AT-Neu','FI-Sod','CH-Aws','CH-Cha','CH-Fru','CH-Lae','CZ-Stn']

previous={}
p=Path.home()/'FLUXNET_MultiSite_11/stage03_surface_pft_audit/11_surface_summary.csv'
if p.exists():
    df=pd.read_csv(p).fillna('')
    previous={str(r.site):str(getattr(r,'error','')) for r in df.itertuples()}

summary=[]; long=[]
for site in SITES:
    paths=sorted((ROOT/site/'subset_data').rglob('surfdata*.nc'))
    row={'site':site,'surface_files':len(paths),'previous_audit_error':previous.get(site,''),
         'status':'UNRESOLVED','PFT_count':None,'PFT_sum':None,'PFT_dimensions':'','PFT_shape':''}
    problems=[];warnings=[]
    if len(paths)!=1:
        row['status']='STRUCTURE_FAIL';problems.append(f'Expected exactly one surfdata*.nc, found {len(paths)}')
    else:
        row['surface_path']=str(paths[0])
        try:
            with Dataset(paths[0]) as nc:
                row['surface_dimensions']=json.dumps({k:len(v) for k,v in nc.dimensions.items()})
                for var in ['PCT_NATVEG','PCT_CROP','PCT_WETLAND','PCT_LAKE','PCT_GLACIER','PCT_URBAN']:
                    if var in nc.variables:
                        x=np.ma.asarray(nc[var][:], dtype=np.float64).filled(np.nan).ravel()
                        if not len(x) or not np.isfinite(x).any():
                            problems.append(f'{var} not finite')
                        else:
                            row[var]=float(np.nansum(x)) if var=='PCT_URBAN' else float(x[0])
                            if len(x)!=1 and var!='PCT_URBAN':warnings.append(f'{var} length={len(x)}; using first site grid cell')
                    elif var in ('PCT_NATVEG','PCT_CROP'):
                        problems.append(f'{var} missing')
                if 'PCT_NAT_PFT' not in nc.variables:
                    problems.append('PCT_NAT_PFT missing')
                else:
                    var=nc['PCT_NAT_PFT']
                    row['PFT_dimensions']=','.join(var.dimensions)
                    row['PFT_shape']=str(var.shape)
                    # Site surface should have one spatial cell: any non-PFT axes
                    # are singleton. Do not flatten arbitrary grid cells into PFTs.
                    dims=list(var.dimensions)
                    axes=[i for i,d in enumerate(dims) if 'pft' in d.lower()]
                    if len(axes)!=1:
                        problems.append(f'PFT dimension ambiguous: {dims}')
                    else:
                        ax=axes[0]
                        arr=np.ma.asarray(var[:],dtype=np.float64).filled(np.nan)
                        n_pft=arr.shape[ax]
                        other_dims=[arr.shape[i] for i in range(arr.ndim) if i!=ax]
                        if any(x!=1 for x in other_dims):
                            problems.append(f'Expected singleton non-PFT dims, got {var.shape} {dims}')
                        else:
                            a=np.moveaxis(arr,ax,0).reshape(n_pft)
                            row['PFT_count']=int(n_pft)
                            row['PFT_sum']=float(np.nansum(a))
                            if not np.isfinite(a).all():problems.append('PFT nonfinite')
                            if (a < -1e-5).any():problems.append('Negative PFT fraction')
                            if abs(float(np.nansum(a))-100)>2:
                                warnings.append('PFT fractions not close to 100%, inspect landunit conventions')
                            row['dominant_pft_index']=int(np.nanargmax(a)) if np.isfinite(a).any() else None
                            row['dominant_pft_pct']=float(np.nanmax(a)) if np.isfinite(a).any() else None
                            if n_pft!=16:
                                warnings.append(f'{n_pft} PFT slots: do NOT apply a hard-coded 16-PFT index-to-name map')
                            for i,val in enumerate(a):
                                if np.isfinite(val) and val>0:
                                    long.append({'site':site,'pft_index':i,'PFT_fraction_pct':float(val),
                                                 'interpretation':'Index only; confirm surface PFT convention'})
                lc=[row.get(x) for x in ('PCT_NATVEG','PCT_CROP','PCT_WETLAND','PCT_LAKE','PCT_GLACIER','PCT_URBAN')]
                if all(x is not None for x in lc):
                    total=sum(float(x) for x in lc)
                    row['landunit_sum']=round(total,4)
                    if not 98<=total<=102:warnings.append(f'landunit sum={total:.3f}%, not near 100')
                if float(row.get('PCT_CROP',0) or 0)>10:
                    warnings.append(f"Crop fraction {row['PCT_CROP']:.1f}%: site-cover scientific review required")
                row['status']='STRUCTURE_FAIL' if problems else 'STRUCTURE_OK_SCIENCE_REVIEW'
        except Exception as exc:
            problems.append(f'{type(exc).__name__}: {exc}')
            row['status']='READ_ERROR'
    row['problems']=' | '.join(problems)
    row['warnings']=' | '.join(warnings)
    summary.append(row)
    print(f"{site:7s} {row['status']:28s} PFT_count={row['PFT_count']} "
          f"old_error={row['previous_audit_error']!r} new_problem={row['problems']}",flush=True)

pd.DataFrame(summary).to_csv(OUT/'surface_reaudit.csv',index=False)
pd.DataFrame(long,columns=['site','pft_index','PFT_fraction_pct','interpretation']).to_csv(OUT/'surface_PFT_indices.csv',index=False)
print('\nReport:',OUT/'surface_reaudit.csv')
print('No surface file was modified; STRUCTURE_OK_SCIENCE_REVIEW does NOT approve landcover or PFT mapping.')

#!/usr/bin/env python3
"""Independent non-destructive surface/PFT metadata review for 11 sites."""
from pathlib import Path
import csv
import numpy as np
import pandas as pd
from netCDF4 import Dataset

ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
SITES=['BE-Bra','FR-Fon','GL-ZaH','IT-Noe','AT-Neu','FI-Sod','CH-Aws','CH-Cha','CH-Fru','CH-Lae','CZ-Stn']
PFT=['bare_ground','needleleaf_evergreen_temperate_tree','needleleaf_evergreen_boreal_tree',
     'needleleaf_deciduous_boreal_tree','broadleaf_evergreen_tropical_tree',
     'broadleaf_evergreen_temperate_tree','broadleaf_deciduous_tropical_tree',
     'broadleaf_deciduous_temperate_tree','broadleaf_deciduous_boreal_tree',
     'broadleaf_evergreen_temperate_shrub','broadleaf_deciduous_temperate_shrub',
     'broadleaf_deciduous_boreal_shrub','c3_arctic_grass','c3_non_arctic_grass','c4_grass','crop_pft']
OUT=Path.home()/'FLUXNET_MultiSite_11'/'stage03_surface_pft_audit'
OUT.mkdir(parents=True,exist_ok=True)
rows=[];pftrows=[]
for site in SITES:
    base=ROOT/site
    paths=list((base/'subset_data').glob('surfdata*.nc'))
    rec={'site':site,'surface_count':len(paths),'status':'REVIEW','bif_igbp':'','top_pft':'','top_pft_pct':np.nan}
    raw=base/'forcing'
    if raw.exists():
        for b in sorted(p for p in raw.rglob('*.csv') if '_FLUXNET_BIF_' in p.name.upper()):
            try:
                with b.open(encoding='utf-8-sig',errors='replace',newline='') as f:
                    terms=[r.get('DATAVALUE','') for r in csv.DictReader(f) if (r.get('VARIABLE') or '').strip().upper()=='IGBP']
                rec['bif_igbp']=';'.join(sorted(set((rec['bif_igbp']+';'.join(terms)).split(';'))))
            except Exception as e:rec['bif_metadata_error']=str(e)
    if len(paths)!=1:
        rec['status']='ERROR_SURFACE_NOT_UNIQUE';rows.append(rec);continue
    rec['surface_file']=str(paths[0])
    try:
        with Dataset(paths[0]) as d:
            for v in ['PCT_NATVEG','PCT_CROP','PCT_WETLAND','PCT_LAKE','PCT_URBAN','PCT_GLACIER']:
                if v in d.variables:
                    a=np.asarray(np.ma.filled(d[v][:],np.nan),dtype=float).ravel()
                    rec[v]=float(np.nansum(a)) if v=='PCT_URBAN' else float(a[0]) if a.size else np.nan
            if 'PCT_NAT_PFT' not in d.variables:raise ValueError('PCT_NAT_PFT missing')
            a=np.asarray(np.ma.filled(d['PCT_NAT_PFT'][:],np.nan),dtype=float).ravel()
            if a.size!=16:raise ValueError(f'Expected 16 PCT_NAT_PFT categories, got {a.size}')
            if (~np.isfinite(a)).any() or abs(float(a.sum())-100)>2:
                rec['PFT_fraction_warning']='natural PFT fraction does not sum close to 100'
            idx=np.argsort(np.nan_to_num(a,nan=-1))[::-1]
            rec['top_pft']=PFT[int(idx[0])]
            rec['top_pft_pct']=float(a[idx[0]])
            rec['status']='STRUCTURE_OK_SCIENCE_REVIEW'
            for i in idx:
                if a[i]>0:
                    pftrows.append({'site':site,'pft_index':int(i),'name':PFT[int(i)],'pct_of_natural':float(a[i])})
    except Exception as e:rec['status']='ERROR';rec['error']=str(e)
    rows.append(rec)
result=pd.DataFrame(rows)
result.to_csv(OUT/'11_surface_summary.csv',index=False)
pd.DataFrame(pftrows).to_csv(OUT/'11_surface_natural_PFT.csv',index=False)
print(result.reindex(columns=['site','bif_igbp','PCT_NATVEG','PCT_CROP','PCT_WETLAND','top_pft','top_pft_pct','status']).to_string(index=False))
print('Output:',OUT)
print('STRUCTURE_OK_SCIENCE_REVIEW is not a forest/grassland/wetland suitability approval.')

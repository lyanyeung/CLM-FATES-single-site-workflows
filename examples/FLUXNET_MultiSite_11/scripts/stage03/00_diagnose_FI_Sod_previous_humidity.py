#!/usr/bin/env python3
"""Read-only diagnosis of old FI-Sod bad-pressure conversion on flagged rows."""
from pathlib import Path
import numpy as np
import pandas as pd
p=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/FI-Sod/forcing/audit_multisource_v1/FI-Sod_humidity_review.csv')
if not p.is_file():raise SystemExit(f'Missing {p}')
d=pd.read_csv(p,low_memory=False)
for col in ['TA_F','VPD_F','PA_F']:
    if col not in d:raise SystemExit('Missing '+col)
t=d.TA_F.to_numpy(dtype=float);v=d.VPD_F.to_numpy(dtype=float);pa=d.PA_F.to_numpy(dtype=float)
es=6.112*np.exp(np.clip(17.67*t/(t+243.5),-100,100));ea=es-v
with np.errstate(divide='ignore',invalid='ignore'):
    q_old=.622*ea*100/(pa*100-.378*ea*100)
    q_new=.622*ea*100/(pa*1000-.378*ea*100)
    rh=100*ea/es
bad_new=(~np.isfinite(q_new))|(ea<=0)|(rh>100.05)|(q_new<0)|(q_new>.08)
print('Old flagged records:',len(d))
print('Still physically invalid with correct PA conversion:',int(bad_new.sum()))
print('Old Q median:',np.nanmedian(q_old),'Corrected Q median:',np.nanmedian(q_new))
if {'TA_source','VPD_source'}<=set(d.columns):
    print('\n=== TA/VPD source combinations ===')
    print(d.groupby(['TA_source','VPD_source']).size().sort_values(ascending=False).head(20).to_string())
print('\nDIAGNOSTIC ONLY: old merged file not modified; rerun source-aware 11-site QC.')

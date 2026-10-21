#!/usr/bin/env python3
"""IT-Noe full-cycle ERA5 candidate builder. UNAPPROVED; no CIME writes."""
import argparse,hashlib,json,shutil
from pathlib import Path
import numpy as np,pandas as pd
from netCDF4 import Dataset
B=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/IT-Noe/forcing')
H=Path.home()/'IT-Noe_source_diagnosis'
def hashfile(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--joined',type=Path,default=H/'full_2004_2025_20261021_213316/selected_years_joined_readonly.csv')
 ap.add_argument('--brackets',type=Path,default=H/'correction_candidates_20261021_220229/candidate_review_brackets_UNAPPROVED.csv')
 ap.add_argument('--out',type=Path,required=True)
 ap.add_argument('--write-candidate',action='store_true')
 a=ap.parse_args()
 orig=B/'datm_11_provisional_dynamic_zbot_v1'
 if a.out.exists() or not orig.is_dir():ap.error('Output exists or original missing')
 d=pd.read_csv(a.joined,parse_dates=['time'])
 e=pd.read_csv(a.brackets,parse_dates=['review_bracket_start_inclusive','review_bracket_end_exclusive'])
 if len(d)!=385440 or len(e)!=208 or d.time.duplicated().any():ap.error('QC input mismatch')
 if set(e.candidate_status)!= {'UNAPPROVED_REVIEW_BRACKET'}:ap.error('Unexpected status')
 flag=d.ANY_REVIEW_FLAG.astype(str).str.lower().isin(['true','1'])
 if int(flag.sum())!=922:ap.error('Flag count mismatch')
 results={};rows=[];records=[]
 for year in range(2004,2026):
  chunk=d[d.time.dt.year==year].reset_index(drop=True)
  stamp=pd.DatetimeIndex(chunk.time)
  expect=pd.date_range(f'{year}-01-01',f'{year+1}-01-01',freq='30min',inclusive='left')
  expect=expect[~((expect.month==2)&(expect.day==29))]
  if not stamp.equals(expect):ap.error(f'{year}: 30-min time misalignment')
  src=orig/f'IT-Noe_DATM_{year}.nc'
  with Dataset(src) as nc:
   axes=np.asarray(nc.variables['time'][:])
   old={k:np.asarray(nc.variables[k][:,0,0],float) for k in ('TBOT','QBOT','PSRF')}
  if len(axes)!=17520 or not np.allclose(axes,np.arange(17520)/48):ap.error(f'{year}: bad NC time axis')
  if np.quantile(np.abs(old['TBOT']-273.15-chunk.TA_F),.99)>.5:ap.error(f'{year}: source/NC TA mismatch')
  t=chunk.TA_ERA.to_numpy(float);v=chunk.VPD_ERA.to_numpy(float);p=chunk.PA_ERA.to_numpy(float)
  es=6.112*np.exp(17.67*t/(t+243.5));ea=es-v
  q=.622*(ea*100)/(p*1000-.378*ea*100)
  repl={'TBOT':t+273.15,'QBOT':q,'PSRF':p*1000}
  valid=np.isfinite(t)&np.isfinite(q)&np.isfinite(p)&(q>0)&(q<.08)&(p>50)&(p<110)&(ea>0)
  w=np.zeros(17520,float)
  for ev in e[e.year==year].itertuples(index=False):
   s=pd.Timestamp(ev.review_bracket_start_inclusive);z=pd.Timestamp(ev.review_bracket_end_exclusive)
   core=(stamp>=s)&(stamp<z);w[core]=1
   for j in range(1,8):
    taper=(1+np.cos(np.pi*j/8))/2
    left=stamp.get_indexer([s-pd.Timedelta(minutes=30*j)])[0]
    right=stamp.get_indexer([z+pd.Timedelta(minutes=30*(j-1))])[0]
    if left>=0:w[left]=max(w[left],taper)
    if right>=0:w[right]=max(w[right],taper)
  flags=flag[d.time.dt.year==year].to_numpy()
  if np.any(w[flags]!=1):ap.error(f'{year}: uncovered flags')
  ix=np.flatnonzero(w>0)
  if not valid[ix].all():ap.error(f'{year}: ERA invalid in modification region')
  new={k:old[k].copy() for k in old}
  for k in old:new[k][ix]=(1-w[ix])*old[k][ix]+w[ix]*repl[k][ix]
  tc=new['TBOT']-273.15
  sat=611.2*np.exp(17.67*tc/(tc+243.5))
  vapor=new['QBOT']*new['PSRF']/(.622+.378*new['QBOT'])
  rh=100*vapor/sat
  if not np.isfinite(rh).all() or rh.min()<=0:ap.error(f'{year}: invalid RH')
  jumps=int(np.sum(np.abs(np.diff(new['TBOT']))>8))
  rows.append({'year':year,'modified':len(ix),'min_rh':rh.min(),'jump_over8':jumps,'max_jump':np.max(np.abs(np.diff(new['TBOT'])))})
  records.extend({'year':year,'time':str(stamp[i]),'weight':w[i],'TA_before':old['TBOT'][i]-273.15,'TA_after':new['TBOT'][i]-273.15} for i in ix)
  results[year]=new
  print(f'{year}: modified={len(ix)} RHmin={rh.min():.2f}% jumps>8={jumps}')
 print(f'REVIEW=UNAPPROVED EPISODES=208 MODIFIED={len(records)}')
 if not a.write_candidate:
  print('PREFLIGHT ONLY: no files written');return
 stage=Path(str(a.out)+'.building')
 if stage.exists():ap.error('staging already exists')
 stage.mkdir(parents=True)
 hashes={}
 for year in range(2004,2026):
  src=orig/f'IT-Noe_DATM_{year}.nc';dst=stage/src.name
  shutil.copy2(src,dst)
  with Dataset(dst,'r+') as nc:
   for k,x in results[year].items():nc.variables[k][:,0,0]=x.astype('f4')
   nc.provenance_status='UNAPPROVED_QC_SENSITIVITY'
  with Dataset(dst) as nc:
   for k,x in results[year].items():
    if not np.allclose(nc.variables[k][:,0,0],x,rtol=1e-5,atol=1e-5):raise RuntimeError(f'{year} postwrite {k}')
  hashes[str(year)]=hashfile(dst)
 pd.DataFrame(rows).to_csv(stage/'annual_qc.csv',index=False)
 pd.DataFrame(records).to_csv(stage/'edited_rows.csv',index=False)
 receipt={'site':'IT-Noe','status':'UNAPPROVED_QC_SENSITIVITY','forcing_directory':str(a.out),
 'year_sha256':hashes,'source_review_complete':False,'boundary_review_complete':False,
 'full_cycle_qc_complete':False,'joined_sha256':hashfile(a.joined),'brackets_sha256':hashfile(a.brackets)}
 (stage/'CANDIDATE_PROVENANCE.json').write_text(json.dumps(receipt,indent=2)+'\n')
 stage.rename(a.out)
 print('CANDIDATE_CREATED='+str(a.out))
 print('NOT APPROVED. NO CIME, restart or Slurm changed.')
if __name__=='__main__':main()

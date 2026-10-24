#!/usr/bin/env python3
"""Stage82 READ ONLY: validate finished Stage81 ten-site DATM NetCDF and inspect
a REAL CIME/DATM case (if supplied) before attempting integration.

This is NOT a CIME stream writer or model submitter. It never rewrites any
NetCDF or model case, assigns a dummy ZBOT, alters solar timing, or submits
Slurm jobs. --report may create only a new timestamped report directory.

Stage80: 18 original RH<1 joint ERA5 corrections; 1091 RH1-5 preserved.
Stage81: 10 sites / 213 annual NETCDF4_CLASSIC, and 10 UNACTIVATED stream
templates. Every exported source year has 17520 half-hour NOLEAP samples.

Pass --reference-case /FULL/PATH/TO/AN_EXISTING_CIME_CASE if available.
Inspect existing case ONLY as a template: never transplant ICOS case
configuration/land surface files directly to an AmeriFlux simulation.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,os,xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

EXPERIMENT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10')
STAGE80=EXPERIMENT/'reports/stage80_RH_lt1_final_20261024T123353Z'
STAGE81=EXPERIMENT/'reports/stage81_DATM_technical_20261024T162235Z'
SITES={'BR-Ma2':18,'CA-Ca3':24,'CA-Cbo':29,'CA-LP1':18,'CA-Man':15,
       'CA-TP1':22,'CA-TP3':22,'CA-TP4':22,'US-Aud':23,'US-Bar':20}
REQUIRED=('time','lat','lon','LONGXY','LATIXY','FLDS','FSDS',
          'PRECTmms','PSRF','TBOT','WIND','SHUM')
N_STEPS=365*48
IMPORTANT_XML=('DATM_MODE','DATM_YR_START','DATM_YR_END','DATM_YR_ALIGN',
               'CALENDAR','RUN_STARTDATE','RUN_REFDATE','ATM_GRID',
               'CLM_USRDAT_NAME','DIN_LOC_ROOT','COMPSET','GRID','COMP_DATM')
CASE_FILES=('env_run.xml','env_case.xml','env_mach_pes.xml',
            'CaseDocs/datm_in','CaseDocs/datm.streams.xml',
            'user_nl_datm','user_nl_datm_streams','CaseDocs/lnd_in')
TSV_KEYS=('site','expected_nc','validated_years','NETCDF_readback',
          'SHA256_files','ZBOT_status','time_interval_status',
          'legacy_template_status','case_coupling_status')
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

def need_imports():
 try:
  import numpy as np
  import netCDF4 as nc
 except ImportError as e:raise RuntimeError(
   'Activate clm_fates_env with numpy and netCDF4 to inspect Stage81 outputs') from e
 return np,nc

def read_stage81():
 p=STAGE81/'manifest.json'
 if not p.is_file():raise RuntimeError('Stage81 manifest missing '+str(p))
 m=json.loads(p.read_text(encoding='utf-8'))
 if (m.get('stage')!=81 or m.get('all_sites')!=10 or
     m.get('all_annual_netcdf_files')!=213 or
     m.get('operator_RH_lt1_native_ERA5_replacements')!=18 or
     m.get('operator_RH1to5_original_retained')!=1091):
  raise RuntimeError('Stage81 provenance or 213/10/18/1091 census mismatch')
 source=STAGE80/'10_site_selected_forcing_sources.tsv'
 if sha(source)!=m.get('stage80_manifest_sha256'):
  raise RuntimeError('Stage80 selected forcing input drift')
 orig_receipt=STAGE80/'manifest.json'
 if sha(orig_receipt)!=m.get('stage80_receipt_sha256'):
  raise RuntimeError('Stage80 original receipt drift')
 records=m.get('sites')
 if not isinstance(records,list) or len(records)!=10 or {s.get('site') for s in records}!=set(SITES):
  raise RuntimeError('Stage81 per-site annual files malformed')
 return m,records

def safe_list_site(record):
 site=record['site'];expected=SITES[site]
 files=record.get('annual_files')
 if not isinstance(files,list) or len(files)!=expected or record.get('years_written')!=expected:
  raise RuntimeError('Incorrect year count '+site)
 if record.get('ZBOT')!='NOT_WRITTEN':
  raise RuntimeError('Stage81 ZBOT provenance status unexpected '+site)
 # Do not allow manifest to redirect the read to a different folder.
 actual=[]
 for f in files:
  p=Path(f['file'])
  if p.parent!=STAGE81/site/'yearly' or p.suffix!='.nc':
   raise RuntimeError('Unexpected site/year file path '+site+' '+str(p))
  y=int(f['year'])
  if p.name!=f'{y:04d}.nc':
   raise RuntimeError('Year and filename mismatch '+site)
  if not p.is_file() or p.stat().st_size==0:
   raise RuntimeError('NetCDF missing or empty '+site+' '+str(y))
  actual.append((y,p,f['sha256']))
 actual.sort()
 if len({y for y,_,_ in actual})!=expected or actual[-1][0]-actual[0][0]!=expected-1:
  raise RuntimeError('Incomplete year span '+site)
 templ=Path(record['stream_template'])
 if templ!=STAGE81/site/('datm.streams.'+site+'.TEMPLATE_NOT_ACTIVATED.txt'):
  raise RuntimeError('Unexpected template path '+site)
 if not templ.is_file() or sha(templ)!=record['stream_template_sha256']:
  raise RuntimeError('DATM stream template checksum drift '+site)
 t=templ.read_text(encoding='utf-8')
 if 'REPLACE_WITH_VERIFIED_SITE_DOMAIN' not in t or 'TEMPLATE_NOT_ACTIVATED' not in str(templ):
  raise RuntimeError('Expected unactivated domain template warnings missing '+site)
 try:ET.fromstring(t)
 except ET.ParseError as e:raise RuntimeError('XML template invalid '+site) from e
 return actual,templ

def verify_nc_one(path,year,source_sha,np,nc,site):
 with nc.Dataset(path) as ds:
  names=set(ds.variables)
  if not set(REQUIRED).issubset(names):
   raise RuntimeError('NetCDF missing DATM variables '+site+' '+str(year))
  v=ds.variables['time']
  if (v.calendar!='noleap' or len(ds.dimensions['time'])!=N_STEPS
      or 'days since '+str(year)+'-01-01 00:00:00'!=v.units):
   raise RuntimeError('NetCDF NOLEAP time metadata mismatch '+site+' '+str(year))
  times=v[[0,1,N_STEPS//2,N_STEPS-1]]
  ref=np.asarray([0,1/48,(N_STEPS//2)/48,(N_STEPS-1)/48],dtype='f8')
  if not np.allclose(times,ref,atol=1e-10,rtol=0):
   raise RuntimeError('NetCDF 30-min time indexing error '+site+' '+str(year))
  if getattr(ds,'source_stage80_forcing_sha256',None)!=source_sha:
   raise RuntimeError('Original Stage80 forcing source SHA provenance drift '+site)
  for k in ('FLDS','FSDS','PRECTmms','PSRF','TBOT','WIND','SHUM'):
   arr=ds.variables[k][[0,1,100,N_STEPS//2,N_STEPS-1],0,0]
   if not np.isfinite(arr).all():
    raise RuntimeError(site+' missing/nonfinite '+k+' at '+str(year))
  if 'ZBOT' in names:raise RuntimeError('Unexpected unverified ZBOT '+site)
  q=ds.variables['SHUM'][[0,1,N_STEPS-1],0,0]
  if not (np.all(q>0) and np.all(q<0.08)):
   raise RuntimeError('SHUM physical range invalid '+site)
 return True

def inspect_case(case):
 if case is None:return {'status':'NO_REFERENCE_CASE_PROVIDED','case_path':None,
                         'case_files':[], 'runtime_xml':{},'stream_mode':'UNKNOWN'}
 c=case.expanduser().resolve(strict=True)
 if not c.is_dir():raise RuntimeError('Case path must be directory '+str(c))
 files=[]
 vars={}
 for rel in CASE_FILES:
  p=c/rel
  if p.is_file():
   files.append({'path':str(p),'sha256':sha(p),'size_bytes':p.stat().st_size})
   if rel.startswith('env_') and p.suffix=='.xml':
    try:
     root=ET.parse(p).getroot()
     for ent in root.iter('entry'):
      key=ent.attrib.get('id','')
      if key in IMPORTANT_XML:vars[key]=ent.attrib.get('value','')
    except ET.ParseError:
     files[-1]['warning']='XML_NOT_PARSEABLE'
 # inspect generated CIME case docs without modifying any.
 docs=c/'CaseDocs'
 derived=[]
 if docs.is_dir():
  for pat in ('datm.streams*','datm_in*','atm.streams*','stream*datm*'):
   for p in sorted(docs.glob(pat)):
    if p.is_file() and str(p) not in derived:derived.append(str(p))
 if any('datm.streams.xml' in p for p in derived):kind='XML_CDEPS_OR_DATM'
 elif any('datm.streams.txt.' in p for p in derived):kind='LEGACY_DATM_TXT'
 elif any('datm_in' in p for p in derived):kind='DATM_NAMELIST_ONLY'
 else:kind='NOT_IDENTIFIED'
 return {'status':'REFERENCE_CASE_READ_ONLY','case_path':str(c),
         'case_files':files,'CaseDocs_datm_files':derived[:30],
         'runtime_xml':vars,'stream_mode':kind,
         'warning':'Reference case may be an unrelated ICOS site; do not copy site surfaces or model forcing configuration directly.'}

def selftest():
 assert sum(SITES.values())==213 and len(SITES)==10
 assert N_STEPS==17520
 assert set(('SHUM','TBOT','WIND','PRECTmms')).issubset(REQUIRED)
 assert 'CA-Cbo' in SITES and 'CA-Man' in SITES
 print('SELF-TEST PASS: exact 10 site/213 annual files, noleap 17520 records/year, SHUM and ZBOT hold')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 g=p.add_mutually_exclusive_group(required=True)
 g.add_argument('--self-test',action='store_true')
 g.add_argument('--check',action='store_true')
 g.add_argument('--report',action='store_true')
 p.add_argument('--reference-case',type=Path,help='Optional existing case path; inspect READ ONLY')
 p.add_argument('--hash-all',action='store_true',help='Read SHA256 of all 213 NetCDF files, not merely first/last per site')
 args=p.parse_args()
 if args.self_test:selftest();return
 np,nc=need_imports()
 m,sites=read_stage81()
 case=inspect_case(args.reference_case)
 result=[]
 total=0;full_hashed=0
 for s in sorted(sites,key=lambda r:r['site']):
  site=s['site'];files,template=safe_list_site(s);total+=len(files)
  # Sample first and last year at minimum. All years checked for file existence.
  # --hash-all provides a complete integrity audit for every annual NC file.
  sha_targets=files if args.hash_all else [files[0],files[-1]]
  for y,path,stored in sha_targets:
   if sha(path)!=stored:raise RuntimeError('Stage81 annual file SHA changed '+site+' '+str(y))
   full_hashed+=1
  for y,path,_ in (files[0],files[-1]):
   verify_nc_one(path,y,s['forcing_sha256'],np,nc,site)
  status={'site':site,'expected_nc':SITES[site],'validated_years':f'{files[0][0]}-{files[-1][0]}',
      'NETCDF_readback':'PASS_FIRST_AND_LAST_YEAR',
      'SHA256_files':'ALL_'+str(len(files)) if args.hash_all else 'FIRST_AND_LAST_ONLY',
      'ZBOT_status':'MISSING_SENSOR_HEIGHT_PROVENANCE',
      'time_interval_status':'UNVERIFIED_SOURCE_INTERVAL_CENTER_AND_LOCAL_TIME',
      'legacy_template_status':'UNACTIVATED_DOMAIN_PLACEHOLDER',
      'case_coupling_status':'NOT_CONFIGURED'}
  print(site,'YEARS',status['validated_years'],
        'NETCDF_N',len(files),'SAMPLED_NC_PASS',
        'ZBOT_HOLD','STREAM_NOT_ACTIVATED')
  result.append(status)
 if total!=213:raise RuntimeError('Unexpected NetCDF file total '+str(total))
 print('STAGE82 CHECK PASS: 10/10 sites; 213 files exist; SHA256 verified',full_hashed,'of 213.')
 print('REFERENCE CASE:',case['status'],case.get('stream_mode'),case.get('case_path'))
 print('PRODUCTION HOLD: unresolved ZBOT, source time centering/LST-UTC, domain and site-specific CIME/DATM streams.')
 if args.check:
  print('READ-ONLY: no report or model changes')
  return
 out=EXPERIMENT/'reports'/('stage82_DATM_case_integration_preflight_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
 out.mkdir(exist_ok=False)
 cols=list(TSV_KEYS)
 with (out/'10_site_DATM_integration_gates.tsv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=cols,delimiter='\t',extrasaction='raise')
  w.writeheader();w.writerows(result)
 payload={'stage':82,'creation_time_utc':datetime.now(timezone.utc).isoformat(),
          'input_stage81_manifest_sha256':sha(STAGE81/'manifest.json'),
          'verified_annual_files_sha256':full_hashed,
          'all_213_files_existence_verified':True,
          'annual_files':213,'sites':10,'stage80_operator_ERA5_RH_lt1_edits':18,
          'selected_candidate_science_release':False,
          'reference_case':case,'site_checks':result,
          'recommended_next_action':'USE_A_REAL_CIME_CASE_TEMPLATE_FOR_THE_CORRECT_DATM_STREAM_FORMAT, VERIFY_SITE_TIME_AND_SENSOR_ZBOT, THEN_SINGLE_SITE_5DAY_SMOKE_TEST',
          'no_active_CIME_DATM_or_Slurm_changes':True}
 (out/'manifest.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
 print('REPORT:',out)
 print('READ-ONLY to existing case/data; only new report files created.')

if __name__=='__main__':main()

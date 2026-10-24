#!/usr/bin/env python3
"""Stage81: build all ten site CLM1PT/DATM technical-preview NetCDF series
from the already-selected Stage80 18-RH<1% operator forcing manifest.

Inputs: only Stage80 10_site_selected_forcing_sources.tsv and its manifest,
pinned SHA256 selected complete CSV forcing, and the matching site point
surface LONGXY/LATIXY coordinates (NOT invented tower positions).

--self-test  no IRIDIS data required
--check      read-only ten-site pinned manifest, surface location and libraries
--build      write new timestamped 10-site, YEAR.nc NETCDF4_CLASSIC forcing
             with noleap half-hourly time, variables, source audit, and DATM
             STREAM TEMPLATE per site. No input/source overwrite or jobs.

Surface data and station sensor heights can differ. ZBOT is intentionally NOT
fabricated: legacy DATM may assume 30m when omitted, which is scientifically
unapproved. Domain files, DATM stream XML and time-centering need verification
against the actual CIME/CDEPS configuration before spin-up. The generated
stream files are TEMPLATES, not automatically wired into running cases.
"""
from __future__ import annotations

import argparse,csv,hashlib,json,math
from datetime import datetime,timedelta,timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10')
STAGE80=ROOT/'reports/stage80_RH_lt1_final_20261024T123353Z'
MANIFEST=STAGE80/'10_site_selected_forcing_sources.tsv'
SITES_ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
EXPECTED_SITES={'BR-Ma2','CA-Ca3','CA-Cbo','CA-LP1','CA-Man','CA-TP1','CA-TP3','CA-TP4','US-Aud','US-Bar'}
RAW_FIELDS=('time','TBOT','QBOT','PSRF','FSDS','FLDS','WIND','PRECTmms')
NC_FIELDS=('FLDS','FSDS','PRECTmms','PSRF','TBOT','WIND','SHUM','RH','QBOT')
UNITS={'FLDS':'W m-2','FSDS':'W m-2','PRECTmms':'mm s-1','PSRF':'Pa',
       'TBOT':'K','WIND':'m s-1','SHUM':'kg kg-1','RH':'percent','QBOT':'kg kg-1'}
RUN_FLAGS={'DATM_TIME_CENTERING_VERIFIED':False,'ZBOT_HEIGHT_VERIFIED':False,
           'DOMAIN_FILE_VERIFIED':False,'ACTIVE_CASE_STREAMS_CONFIGURED':False,
           'SCIENTIFIC_PRODUCTION_RELEASE':False}
DAYS=365;ROWS_PER_YEAR=365*48

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def module_imports():
 try:
  import numpy as np
  import netCDF4
 except ImportError as exc:
  raise RuntimeError("Stage81 requires numpy and netCDF4 in clm_fates_env; "
                     "activate that environment (no source data need be downloaded)") from exc
 return np,netCDF4

def noleap_times(year):
 d=datetime(year,1,1)
 for day in range(366 if (year%4==0 and (year%100!=0 or year%400==0)) else 365):
  date=d+timedelta(days=day)
  if date.month==2 and date.day==29:continue
  for sub in range(48):yield date+timedelta(minutes=sub*30)

def load_stage80():
 if not MANIFEST.is_file():raise RuntimeError('Final Stage80 manifest missing: '+str(MANIFEST))
 receipt_path=STAGE80/'manifest.json'
 if not receipt_path.is_file():raise RuntimeError('Stage80 SHA receipt missing')
 receipt=json.loads(receipt_path.read_text(encoding='utf-8'))
 if (receipt.get('stage')!=80 or receipt.get('native_ERA5_joint_replaced_rows')!=18
      or receipt.get('original_RH_1to5_restored_and_retained')!=1091):
  raise RuntimeError('Stage80 decision/scope changed: require precisely 18 and 1091')
 if sha(MANIFEST)!=receipt.get('selected_sources_receipt_sha256'):
  raise RuntimeError('Stage80 ten-site source manifest SHA mismatch')
 with MANIFEST.open(newline='',encoding='utf-8-sig') as f:
  rd=csv.DictReader(f,delimiter='\t')
  required={'site','site_years','selected_source','selected_sha256','source_version',
            'native_ERA5_replaced_original_RH_below1'}
  if not required.issubset(rd.fieldnames or []):
   raise RuntimeError('Stage80 selected source schema changed')
  data=list(rd)
 if len(data)!=10 or {r['site'] for r in data}!=EXPECTED_SITES:
  raise RuntimeError('Stage80 must contain 10 unique expected sites')
 if sum(int(r['native_ERA5_replaced_original_RH_below1']) for r in data)!=18:
  raise RuntimeError('Stage80 ten-site selected counts must be 18')
 for row in data:
  site=row['site']
  path=Path(row['selected_source']).resolve(strict=True)
  if sha(path)!=row['selected_sha256']:
   raise RuntimeError(site+' selected forcing checksum drift')
  row['_source']=path
  try:
   first,last=[int(v) for v in row['site_years'].split('-')]
  except Exception as exc:raise RuntimeError('Invalid source years '+site) from exc
  if first>last or first<1900 or last>2100:
   raise RuntimeError('Unreasonable source years '+site)
  row['_first']=first;row['_last']=last
 return sorted(data,key=lambda x:x['site']),receipt

def site_surface(site,NC):
 folder=SITES_ROOT/site/'subset_data'
 files=sorted(folder.glob('surfdata*.nc'))
 if len(files)!=1:raise RuntimeError(site+' requires exactly one existing site point surface in '+str(folder)+'; found '+str(len(files)))
 p=files[0]
 with NC.Dataset(p) as ds:
  for k in ('LONGXY','LATIXY'):
   if k not in ds.variables:raise RuntimeError(site+' surface missing '+k)
  import numpy as np
  lons=np.ma.filled(ds.variables['LONGXY'][:],np.nan).astype(float).ravel()
  lats=np.ma.filled(ds.variables['LATIXY'][:],np.nan).astype(float).ravel()
  if lons.size!=1 or lats.size!=1:raise RuntimeError(site+' point surface not 1x1')
  lon=float(lons[0]);lat=float(lats[0])
  if not(math.isfinite(lon) and math.isfinite(lat) and -90<=lat<=90 and -180<=lon<=360):
   raise RuntimeError(site+' surface has invalid grid position')
 return p,lat,lon

def validate_row(row,site):
 vals={}
 for k in RAW_FIELDS[1:]:
  try:v=float(row[k])
  except (TypeError,ValueError,KeyError) as exc:
   raise RuntimeError(site+' nonnumeric forcing '+k+' at '+str(row.get('time'))) from exc
  if not math.isfinite(v):raise RuntimeError(site+' nonfinite '+k)
  vals[k]=v
 if not (180<vals['TBOT']<340 and 49000<vals['PSRF']<111000 and
         0<vals['QBOT']<.08 and vals['WIND']>=0 and
         vals['FLDS']>=0 and vals['FSDS']>=0 and vals['PRECTmms']>=0):
  raise RuntimeError(site+' forcing physical bound failure '+str(row['time']))
 T=vals['TBOT']-273.15
 P=vals['PSRF']/100.0
 e=vals['QBOT']*P/(.622+.378*vals['QBOT'])
 es=6.112*math.exp(17.67*T/(T+243.5))
 RH=100.0*e/es
 if not 0<=RH<=100.5:raise RuntimeError(site+' reconstructed RH invalid at '+str(row['time']))
 return {'FLDS':vals['FLDS'],'FSDS':vals['FSDS'],
         'PRECTmms':vals['PRECTmms'],'PSRF':vals['PSRF'],
         'TBOT':vals['TBOT'],'WIND':vals['WIND'],
         'SHUM':vals['QBOT'],'QBOT':vals['QBOT'],'RH':RH}

def iterate_years(source,site,first,last):
 with source.open(newline='',encoding='utf-8-sig') as f:
  rdr=csv.DictReader(f)
  if len(rdr.fieldnames or [])!=len(set(rdr.fieldnames or [])) or not set(RAW_FIELDS).issubset(rdr.fieldnames or []):
   raise RuntimeError(site+' selected forcing incomplete/malformed columns')
  stream=iter(rdr)
  rows_total=0
  for year in range(first,last+1):
   refs=iter(noleap_times(year))
   rows=[]
   for i in range(ROWS_PER_YEAR):
    row=next(stream,None)
    if row is None:raise RuntimeError(site+' truncated time record '+str(year)+' index '+str(i))
    stamp=next(refs)
    if row['time']!=stamp.strftime('%Y-%m-%d %H:%M:%S'):
     raise RuntimeError(site+' NOLEAP 30min misalignment: expected '+str(stamp)+' got '+repr(row['time']))
    values=validate_row(row,site)
    rows.append(values);rows_total+=1
   yield year,rows
  if next(stream,None) is not None:raise RuntimeError(site+' extra records after expected last year')
  if rows_total!=(last-first+1)*ROWS_PER_YEAR:
   raise RuntimeError('Site record census wrong')

def annual_nc(path,site,year,rows,lat,lon,source,source_sha,surface_sha,NP,NC):
 if len(rows)!=ROWS_PER_YEAR:raise RuntimeError('Incomplete annual rows')
 with NC.Dataset(path,'w',format='NETCDF4_CLASSIC') as ds:
  ds.createDimension('time',None);ds.createDimension('lat',1);ds.createDimension('lon',1)
  time=ds.createVariable('time','f8',('time',))
  time.units=f'days since {year:04d}-01-01 00:00:00'
  time.calendar='noleap'
  time.long_name='site-native half-hour index; source interval centering not independently verified'
  time[:]=NP.arange(ROWS_PER_YEAR,dtype='f8')/48.0
  latv=ds.createVariable('lat','f8',('lat',));latv.units='degrees_north';latv[:]=[lat]
  lonv=ds.createVariable('lon','f8',('lon',));lonv.units='degrees_east';lonv[:]=[lon]
  lxy=ds.createVariable('LONGXY','f8',('lat','lon'));lxy[:]=[[lon]]
  lxy.units='degrees_east'
  axy=ds.createVariable('LATIXY','f8',('lat','lon'));axy[:]=[[lat]]
  axy.units='degrees_north'
  for k in NC_FIELDS:
   v=ds.createVariable(k,'f8',('time','lat','lon'),zlib=True,complevel=2,
                       chunksizes=(min(1440,ROWS_PER_YEAR),1,1))
   v.units=UNITS[k]
   v[:,0,0]=NP.array([row[k] for row in rows],dtype='f8')
   if k=='SHUM':v.long_name='specific humidity; exact Stage80 QBOT'
   if k=='QBOT':v.long_name='source forcing QBOT alias (not DATM mapped)'
   if k=='RH':v.long_name='RH derived from Stage80 TBOT,QBOT,PSRF for crosscheck'
  ds.Conventions='CF-1.8'
  ds.title=f'{site} Stage80 selected CLM1PT 30min DATM technical preview {year}'
  ds.source_stage80_forcing_path=str(source)
  ds.source_stage80_forcing_sha256=source_sha
  ds.point_surface_sha256=surface_sha
  ds.precip_units_unchanged='PRECTmms retained as mm/s (numerically kg m-2 s-1)'
  ds.TA_USE_VPD_USE_omitted='Original TA_USE/VPD_USE remain in Stage80 CSV; DATM uses thermodynamic SHUM instead'
  ds.ZBOT_status='OMITTED: sensor height NOT independently verified; DATM fallback 30m must NOT be accepted without review'
  ds.time_label_status='UNCERTAIN: Stage80 timestamps retained verbatim; local-to-UTC and interval midpoint/left-end unresolved'
  ds.experiment_use='TECHNICAL_PREVIEW_ONLY_NOT_PRODUCTION_APPROVED'

def stream_template(out,site,years):
 # Legacy DATM CLM1PT XML-style template. An actual CIME/CDEPS case will
 # differ: DO NOT auto-install. Domain must be sourced from actual site case.
 site_dir=out/site/'yearly'
 names='\n'.join('          '+str(y)+'.nc' for y in years)
 fields='\\n'.join(['                '+key+' '+key for key in
                     ('FLDS','FSDS','PRECTmms','PSRF','TBOT','WIND','SHUM')])
 # Undo the Python backslash for real XML line breaks.
 fields=fields.replace('\\n','\n')
 template=f"""<streamstemplate>
  <stream>
    <dataSource>CLMNCEP</dataSource>
    <domainInfo>
      <variableNames>
        time time
        xc xc
        yc yc
        area area
        mask mask
      </variableNames>
      <filePath>REPLACE_WITH_VERIFIED_SITE_DOMAIN_DIRECTORY</filePath>
      <fileNames>REPLACE_WITH_VERIFIED_SITE_DOMAIN_FILENAME.nc</fileNames>
    </domainInfo>
    <fieldInfo>
      <variableNames>
{fields}
      </variableNames>
      <offset>0</offset>
      <filePath>{escape(str(site_dir))}</filePath>
      <fileNames>
{names}
      </fileNames>
    </fieldInfo>
  </stream>
</streamstemplate>
"""
 path=out/site/('datm.streams.'+site+'.TEMPLATE_NOT_ACTIVATED.txt')
 path.write_text(template,encoding='utf-8')
 return path

def inspect_site(src,NC):
 surface,lat,lon=site_surface(src['site'],NC)
 return {'site':src['site'],'years':src['site_years'],
         'forcing_path':str(src['_source']),'forcing_sha256':src['selected_sha256'],
         'surface_path':str(surface),'surface_sha256':sha(surface),
         'point_grid_lat':lat,'point_grid_lon':lon,
         'yearly_netcdf_count':src['_last']-src['_first']+1,
         'ZBOT':'NOT_WRITTEN','domain':'REQUIRES_VERIFIED_CASE_DOMAIN',
         'time_centering':'SOURCE_TIMESTAMPS_UNCHANGED_UNVERIFIED'}

def selftest():
 assert len(list(noleap_times(2004)))==ROWS_PER_YEAR
 stamps=list(noleap_times(2004))
 assert stamps[0]==datetime(2004,1,1,0,0)
 assert datetime(2004,2,29,0,0) not in stamps
 assert stamps[-1]==datetime(2004,12,31,23,30)
 assert len(list(noleap_times(2003)))==ROWS_PER_YEAR
 ex={'time':'2004-01-01 00:00:00','TBOT':'298.15',
     'QBOT':'0.01','PSRF':'100000','FSDS':'300','FLDS':'350',
     'WIND':'2','PRECTmms':'0.00001'}
 state=validate_row(ex,'TEST')
 assert abs(state['SHUM']-0.01)<1e-12 and state['RH']>0
 try:
  validate_row({**ex,'TBOT':'-40'},'TEST')
 except RuntimeError:pass
 else:raise AssertionError('Invalid TBOT bound not detected')
 print('SELF-TEST PASS: 365d NOLEAP leap-year skip, 48 half hours/day, all 7 DATM variables and SHUM/RH closure')

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 mode=ap.add_mutually_exclusive_group(required=True)
 mode.add_argument('--self-test',action='store_true')
 mode.add_argument('--check',action='store_true')
 mode.add_argument('--build',action='store_true')
 ap.add_argument('--outdir',type=Path)
 args=ap.parse_args()
 if args.self_test:selftest();return
 if args.check and args.outdir:p.error('--check is read-only, omit --outdir')
 if args.build and not args.outdir:p.error('--build requires --outdir NEW_DIRECTORY')
 NP,NC=module_imports()
 sources,receipt=load_stage80()
 meta=[inspect_site(s,NC) for s in sources]
 num=sum(x['yearly_netcdf_count'] for x in meta)
 print('STAGE81 FROM PINNED STAGE80: 10 sites; 18 RH<1 repairs; 1091 RH1-5 kept.')
 print('Yearly NetCDF expected:',num)
 for x in meta:
  print(x['site'],x['years'],'yearly NetCDF',x['yearly_netcdf_count'],
        'point surface',x['point_grid_lat'],x['point_grid_lon'],
        'ZBOT=UNRESOLVED')
 if args.check:
  print('CHECK PASS: exact Stage80 source SHA, 10 point surfaces, numpy/netCDF4. No reports/forcing modified.')
  return
 out=args.outdir.resolve()
 if out.exists():raise RuntimeError('Refusing to overwrite existing output directory '+str(out))
 out.mkdir(parents=True)
 written=[]
 for src,description in zip(sources,meta):
  site=src['site'];root=out/site/'yearly';root.mkdir(parents=True)
  yearfiles=[]
  for year,rows in iterate_years(src['_source'],site,src['_first'],src['_last']):
   target=root/f'{year:04d}.nc'
   annual_nc(target,site,year,rows,description['point_grid_lat'],description['point_grid_lon'],
             src['_source'],src['selected_sha256'],description['surface_sha256'],NP,NC)
   with NC.Dataset(target) as ds:
    if (len(ds.dimensions['time'])!=ROWS_PER_YEAR or
        any(k not in ds.variables for k in NC_FIELDS) or
        ds.variables['time'].calendar!='noleap'):
     raise RuntimeError(site+' NetCDF readback verification failure '+str(year))
    if not NP.isfinite(ds.variables['SHUM'][:]).all():
     raise RuntimeError(site+' NetCDF invalid SHUM '+str(year))
   yearfiles.append({'year':year,'file':str(target),'sha256':sha(target)})
  templ=stream_template(out,site,range(src['_first'],src['_last']+1))
  if len(yearfiles)!=description['yearly_netcdf_count']:
   raise RuntimeError('Incomplete station NetCDF output '+site)
  summary={**description,'years_written':len(yearfiles),
           'stream_template':str(templ),'stream_template_sha256':sha(templ),
           'annual_files':yearfiles}
  written.append(summary)
  print('NETCDF BUILD PASS',site,'files',len(yearfiles),'STREAM TEMPLATE CREATED (NOT ACTIVATED)',flush=True)
 if sum(x['years_written'] for x in written)!=num:
  raise RuntimeError('Incomplete ten-site output')
 receipt_out={'stage':81,'stage80_manifest_sha256':sha(MANIFEST),
              'stage80_receipt_sha256':sha(STAGE80/'manifest.json'),
              'model_activation':False,'legacy_DATM_stream_templates_only':True,
              'all_sites':10,'all_annual_netcdf_files':num,
              'operator_RH_lt1_native_ERA5_replacements':18,
              'operator_RH1to5_original_retained':1091,
              'clm_datm_mode_candidate':'CLM1PT',
              'time_axis':'30-minute timestamp source; NOLEAP; annual time units days since YYYY-01-01',
              'input_units':UNITS,
              'physics_conditions':RUN_FLAGS,
              'warnings':['ZBOT deliberately absent; old DATM may default to 30m; no production use before real height source determined',
                          'No independent confirmation whether FLUXNET half-hour TIMESTAMP_START or midpoint appropriate',
                          'Point surface lon/lat reflect selected model grid, not independently verified tower coordinates',
                          'Legacy XML stream templates require real domain file and CIME/DATM version validation',
                          'Stage80 source forcing paths/checksums are immutable; no modifications of original files or running cases'],
              'sites':written}
 (out/'manifest.json').write_text(json.dumps(receipt_out,indent=2)+'\n',encoding='utf-8')
 print('STAGE81 DATM NETCDF TECHNICAL PREVIEW COMPLETE:',out)
 print('YEARLY NC FILES:',num,'SITES: 10')
 print('STREAM TEMPLATES: 10 (NOT ACTIVATED; domain and ZBOT review pending)')
 print('ORIGINAL CSV/CIME/DATM/SLURM UNCHANGED')

if __name__=='__main__':main()

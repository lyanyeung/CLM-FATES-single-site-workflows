#!/usr/bin/env python3
"""Stage31: 13-site / 1000-year EXPLORATORY CLM-FATES startup spin-up.

IRIDIS6, source: proven GF-Guy Intel/OpenMPI case; selected Stage30 DATM.

--mode check: verify all 271 stage30 DATM files and 13 existing point surfaces.
--mode prepare: create 13 keepexe clones, configure and preflight ALL; no submission.
--mode run: check, prepare all, THEN submit all 13 via CIME using --exclusive
            (one exclusive Slurm allocation per job; queued by scheduler).

WARNING: 13 cases CAN run at the same time on distinct exclusive nodes. This
prevents CPU-core sharing but is NOT 'only one site running in the cluster'.
Only provisional scientific forcing: do not claim convergence or approval.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
import fcntl

import numpy as np
import pandas as pd
from netCDF4 import Dataset

UID='ly3n24'
BASE=Path('/iridisfs/scratch')/UID/'CLM_FATES'
SITEBASE=BASE/'sites/MY_EC_SITE'
CASES=BASE/'cases'
CTSM=BASE/'CTSM'
OUT=Path('/scratch')/UID/'CTSM_FATES_OUTPUTS'
INPUT=BASE/'inputdata'
SOURCE=CASES/'GF-Guy_FATES_SURF2000_CO2405_1PT'
MANIFEST=BASE/'experiments/FLUXNET_13_ZBOT_DATM_STAGE30_20261018_055940_1008203/reports/04_consolidated_13site_271_DATM_SHA256_manifest.csv'
SITES=['DE-Lnf','DE-Obe','ES-Agu','ES-LJu','IT-Col','DE-Gri','DE-RuR','FI-Hyy','FI-Let','FR-Pue','GF-Guy','IT-MBo','IT-Tor']
YEARS={
 'DE-Lnf':(2002,2024),'DE-Obe':(2008,2025),'ES-Agu':(2006,2024),
 'ES-LJu':(2004,2024),'IT-Col':(1996,2014),'DE-Gri':(2004,2025),
 'DE-RuR':(2011,2025),'FI-Hyy':(1997,2025),'FI-Let':(2010,2025),
 'FR-Pue':(2000,2025),'GF-Guy':(2004,2025),'IT-MBo':(2003,2025),
 'IT-Tor':(2008,2025)}
# NOAA GML global annual CO2 means, June 2026 annual release; original
# reference: https://gml.noaa.gov/ccgg/trends/gl_data.html
# Fixed for each site's entire spinup, NOT actual CO2 at the EC tower.
CO2={1996:361.93,1997:363.04,2000:368.96,2002:372.58,
     2003:375.14,2004:376.95,2006:381.15,2008:385.02,
     2010:388.75,2011:390.62}
TOTAL_YEARS=1000
YEARS_PER_JOB=5
RESUBMIT=TOTAL_YEARS//YEARS_PER_JOB-1
SUFFIX='_FATES_SPINUP1000_S30EXCL'
VARS=('TBOT','QBOT','PSRF','FSDS','FLDS','WIND','PRECTmms','ZBOT')

def require(cond, message):
    if not cond: raise RuntimeError(message)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

def cmd(args, cwd=None, log=None, check=True):
    args=[str(a) for a in args]
    print('$ '+' '.join(args)+'  @ '+str(cwd or Path.cwd()),flush=True)
    p=subprocess.run(args,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if log is not None:
        with Path(log).open('a',encoding='utf-8') as f:
            f.write('\n$ '+' '.join(args)+'\n'+p.stdout+'\n')
    if p.returncode and check:
        raise RuntimeError(f'Command failed rc={p.returncode}: {" ".join(args)}\n{p.stdout[-3800:]}')
    if p.stdout.strip(): print(p.stdout[-700:].rstrip(),flush=True)
    return p

def xml(case,key):
    p=cmd(['./xmlquery',key,'--value'],cwd=case)
    return p.stdout.strip().splitlines()[-1].strip()

def datm_integrity(path,site,year):
    with Dataset(str(path)) as n:
        require(len(n.dimensions['time'])==17520,f'{path}: time count')
        require(n['time'].calendar.lower() in ('noleap','365_day'),f'{path}: calendar')
        require(np.allclose(np.asarray(n['time'][:]),np.arange(17520)/48),f'{path}: time values')
        for v in VARS:
            require(v in n.variables and n[v].shape==(17520,1,1),f'{path}: missing/dimensions {v}')
        z=np.asarray(n['ZBOT'][:,0,0])
        require(np.isfinite(z).all() and (z>=.5).all() and (z<=150).all(),f'{path}: ZBOT invalid')
        lat=float(np.asarray(n['LATIXY'][:]).ravel()[0]);lon=float(np.asarray(n['LONGXY'][:]).ravel()[0])
        require(-90<=lat<=90 and -180<=lon<=360,f'{path}: coordinates invalid')
        return lat,lon

def get_inputs(manifest,check_sha=True):
    require(manifest.is_file(),f'Missing Stage30 manifest: {manifest}')
    d=pd.read_csv(manifest,dtype={'site':str})
    require({'site','year','datm_nc','sha256'}.issubset(d.columns),'Stage30 manifest columns do not match expected')
    require(len(d)==271 and set(d.site)==set(SITES),'Stage30 expected 271 DATM entries / exact 13 sites')
    require(not d[['site','year']].duplicated().any(),'Duplicate stage30 site/year')
    found={}; seen=set();tot=0
    for site in SITES:
        first,last=YEARS[site]
        x=d[d.site==site].sort_values('year')
        require(x.year.astype(int).tolist()==list(range(first,last+1)),f'{site}: expected consecutive years {first}-{last}')
        years={};ref=None
        for r in x.itertuples(index=False):
            file=Path(r.datm_nc)
            require(file.is_absolute() and file.is_file(),f'{site} missing DATM: {file}')
            require(file not in seen,f'Duplicated DATM file in manifest: {file}')
            seen.add(file)
            if check_sha:
                require(sha(file)==str(r.sha256),f'SHA256 mismatch: {file}')
            # Validate boundaries and a representative interior year to avoid rereading every annual file twice.
            if int(r.year) in (first,last,(first+last)//2):
                latlon=datm_integrity(file,site,int(r.year))
                if ref is not None:
                    require(np.allclose(ref,latlon,atol=1e-8),f'{site}: changing coordinates')
                ref=latlon
            years[int(r.year)]=file
            tot+=1
        # Site-specific user mods, surface. Never infer ZBOT from tower/WS height.
        root=SITEBASE/site
        surfaces=sorted((root/'subset_data').rglob('surfdata*.nc'))
        require(len(surfaces)==1 and surfaces[0].stat().st_size>0,f'{site}: expected exactly one nonempty surface')
        mods=root/'subset_data'/'user_mods'
        require((mods/'user_nl_clm').is_file(),f'{site}: missing user_mods/user_nl_clm')
        text=(mods/'user_nl_clm').read_text(errors='replace')
        require(surfaces[0].name in text,f'{site}: user_mods does NOT reference its surface {surfaces[0].name}')
        # Validate surface coordinates when available.
        with Dataset(str(surfaces[0])) as nc:
            def coord(keys):
                for k in keys:
                    if k in nc.variables:return float(np.asarray(nc[k][:]).ravel()[0])
                return None
            slat=coord(('LATIXY','lat','latitude'))
            slon=coord(('LONGXY','lon','longitude'))
            require(slat is not None and slon is not None,f'{site}: missing surface coordinates')
            # compare first-year netCDF coords with point surface across 0..360 convention.
            flat,flon=datm_integrity(years[first],site,first)
            require(abs(slat-flat)<0.02 and abs(((slon-flon+180)%360)-180)<0.02,
                    f'{site}: surface vs DATM latitude/longitude mismatch: {(slat,slon)} != {(flat,flon)}')
            pct_crop=coord(('PCT_CROP',))
        found[site]={'first':first,'last':last,'met':years,'lat':flat,'lon':flon,
                     'surface':surfaces[0],'mods':mods,'crop':pct_crop,'co2':CO2[first]}
        print(f'{site:<8} DATM {first}-{last} ({len(years)} files) ZBOT verified, '
              f'surface={surfaces[0].name} PCT_CROP={pct_crop}',flush=True)
    require(tot==271,'DATM count not 271')
    return found

def prerequisite_paths(source=SOURCE):
    require(os.environ.get('USER')==UID, f'Expected IRIDIS username {UID}; got {os.environ.get("USER")}')
    require(TOTAL_YEARS==1000 and YEARS_PER_JOB==5 and RESUBMIT==199,'Spinup segmentation mismatch')
    require((CTSM/'cime/scripts/create_clone').is_file(),'CIME create_clone missing')
    require((source/'xmlquery').is_file() and (source/'CaseStatus').is_file(),f'Source case absent: {source}')
    require(re.search(r'model execution success|case\.run success', (source/'CaseStatus').read_text(errors='replace'), re.I), 'Source case lacks a confirmed successful model run')
    exe=Path(xml(source,'EXEROOT'))/'cesm.exe'
    require(exe.is_file() and os.access(exe,os.X_OK),f'Source executable missing: {exe}')
    require(xml(source,'BUILD_COMPLETE').upper()=='TRUE','Source case BUILD_COMPLETE != TRUE')
    require(INPUT.is_dir() and CASES.is_dir(),'Inputdata / cases missing')
    require(shutil.which('sbatch') and shutil.which('squeue'), 'Slurm tools sbatch/squeue missing')
    return exe

def stream_config(site,item):
    first,last=item['first'],item['last']
    lines=[
       'CLM_USRDAT.UNSET:taxmode = cycle',
       'CLM_USRDAT.UNSET:tintalgo = linear',
       'CLM_USRDAT.UNSET:mapalgo = none',
       'CLM_USRDAT.UNSET:meshfile = none','',
       f'CLM_USRDAT.UNSET:year_first = {first}',
       f'CLM_USRDAT.UNSET:year_last = {last}',
       f'CLM_USRDAT.UNSET:year_align = {first}','',
       'CLM_USRDAT.UNSET:datafiles = \\',
    ]
    for yr in range(first,last+1):
        lines.append(str(item['met'][yr]) + (', \\' if yr<last else ''))
    lines.extend(['','CLM_USRDAT.UNSET:datavars = \\',
     'PRECTmms Faxa_precn, \\', 'FSDS Faxa_swdn, \\',
     'ZBOT Sa_z, \\', 'TBOT Sa_tbot, \\',
     'WIND Sa_wind, \\', 'QBOT Sa_shum, \\',
     'PSRF Sa_pbot, \\', 'FLDS Faxa_lwdn',''])
    return '\n'.join(lines)

def configure_site(site,item,source,exe,log):
    name=site+SUFFIX
    case=CASES/name
    run=OUT/name/'run'
    archive=OUT/'archive'/name
    # Existing submitted/running case cannot be reused. No source data modification.
    if case.exists():
        require((case/'xmlquery').exists(),f'{case}: existing noncase path')
        cs=(case/'CaseStatus').read_text(errors='replace')
        require(not re.search(r'case\.submit success|model execution starting|case\.run starting',cs,re.I),
                f'{case}: already submitted; will NOT duplicate')
        require(xml(case,'CASE')==name,'Existing case name mismatch')
    else:
        # CIME may edit USERMODS. Copy so original user_mods remain unchanged.
        with tempfile.TemporaryDirectory(prefix=f'flx13_{site}_mods_') as st:
            staged=Path(st)
            shutil.copytree(item['mods'],staged,dirs_exist_ok=True)
            commands=staged/'shell_commands'
            if commands.is_file():
                keep=[r for r in commands.read_text().splitlines() if not re.search(r'MPILIB\s*=\s*mpi-serial',r)]
                commands.write_text('\n'.join(keep)+'\n')
            cmd([str(CTSM/'cime/scripts/create_clone'),'--case',case,'--clone',source,
                 '--user-mods-dir',staged,'--keepexe'],cwd=CTSM/'cime/scripts',log=log)
    require((case/'xmlquery').is_file(),f'{site}: clone missing xmlquery')
    userclm=item['mods']/'user_nl_clm'
    data=userclm.read_text()
    data='\n'.join([line for line in data.splitlines()
         if not re.match(r'^\s*(use_excess_ice|use_excess_ice_streams|hist_nhtfrq|hist_mfilt)\s*=',line,re.I)])
    data+='\n\n! Stage31 exploratory 1000-year spin-up using published / BIF height assumptions\n'
    data+='use_excess_ice = .false.\nuse_excess_ice_streams = .false.\n'
    data+='hist_nhtfrq = -24\nhist_mfilt = 365\n'
    (case/'user_nl_clm').write_text(data)
    (case/'user_nl_datm_streams').write_text(stream_config(site,item))
    (case/'user_nl_datm').touch()
    settings={
     'DIN_LOC_ROOT':str(INPUT),'RUN_TYPE':'startup','CONTINUE_RUN':'FALSE',
     'RUN_STARTDATE':f"{item['first']}-01-01",'CALENDAR':'NO_LEAP',
     'ATM_NCPL':'48','CLM_CO2_TYPE':'constant',
     'CCSM_CO2_PPMV':f"{item['co2']:.2f}",
     'STOP_OPTION':'nyears','STOP_N':'5','REST_OPTION':'nyears','REST_N':'5',
     'RESUBMIT':'199','DOUT_S':'TRUE','DOUT_S_ROOT':str(archive),'RUNDIR':str(run),
    }
    for k,v in settings.items():cmd(['./xmlchange',f'{k}={v}'],cwd=case,log=log)
    for k,v in [('PTS_LAT',item['lat']),('PTS_LON',item['lon'])]:
        p=cmd(['./xmlquery',k,'--value'],cwd=case,log=log,check=False)
        if p.returncode==0:cmd(['./xmlchange',f'{k}={v}'],cwd=case,log=log)
    if not (case/'.case.run').is_file() or not (case/'case.st_archive').is_file():
        cs=(case/'CaseStatus').read_text(errors='replace')
        cmd(['./case.setup','--reset'] if 'case.setup success' in cs else ['./case.setup'],cwd=case,log=log)
    require((case/'.case.run').is_file() and (case/'case.st_archive').is_file(),
        f'{site}: CIME .case.run or case.st_archive missing')
    require(Path(xml(case,'EXEROOT'))/'cesm.exe'==exe,f'{site}: clone does not use checked shared executable')
    cmd(['./preview_namelists'],cwd=case,log=log)
    doc=case/'CaseDocs/lnd_in'
    require(doc.is_file(),f'{site}: lnd_in missing')
    land=doc.read_text(errors='replace')
    require(item['surface'].name in land,f'{site}: case points to wrong surface')
    require('use_excess_ice' in land and not re.search(r'use_excess_ice(?:_streams)?\s*=\s*\.true\.',land,re.I),
        f'{site}: unsafe excess ice in lnd_in')
    stream=(case/'user_nl_datm_streams').read_text()
    for p in item['met'].values():
        require(str(p) in stream,f'{site}: stream missing {p}')
    require('taxmode = cycle' in stream,f'{site}: DATM not cycling')
    cmd(['./check_input_data'],cwd=case,log=log)
    if xml(case,'BUILD_COMPLETE').upper()!='TRUE':
        # Reuse --keepexe GF-Guy executable, not an independent compile.
        require(exe.is_file(),f'{site}: source exe disappeared')
        cmd(['./xmlchange','BUILD_COMPLETE=TRUE'],cwd=case,log=log)
    for key,val in [('STOP_N','5'),('REST_N','5'),('RESUBMIT','199'),
                    ('RUN_STARTDATE',f"{item['first']}-01-01"),('ATM_NCPL','48'),
                    ('RUNDIR',str(run)),('CLM_CO2_TYPE','constant')]:
        got=xml(case,key)
        require(got.lower()==val.lower(),f'{site}: {key}={got} expected={val}')
    require(abs(float(xml(case,'CCSM_CO2_PPMV'))-item['co2'])<.011,f'{site}: CO2 mismatch')
    require(xml(case,'BUILD_COMPLETE').upper()=='TRUE',f'{site}: BUILD_COMPLETE false')
    cs=(case/'CaseStatus').read_text(errors='replace')
    require(not re.search(r'case\.submit success|model execution starting|case\.run starting',cs,re.I),
        f'{site}: case submitted while preparing')
    print(f'PREPARED {site:7} {name} co2={item["co2"]:.2f}ppm '
          f'5y x 200 segments; 1000 years; datm={len(item["met"])}',flush=True)
    return case

def run_campaign(args):
    require(args.source_case.is_dir(),'GF-Guy source case missing')
    with (CASES/'.stage31_spinup1000_setup.lock').open('a+') as lock:
        try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: raise RuntimeError('Another Stage31 case creator running')
        print('=== STAGE31 CHECK INPUTS ===',flush=True)
        inputs=get_inputs(args.manifest,not args.skip_full_sha)
        exe=prerequisite_paths(args.source_case)
        if args.mode=='check':
            print('CHECK_OK: Stage30 271 annual DATM files, site surfaces and GF-Guy executable. No changes.')
            return
        report=args.report or (Path.home()/('FLUXNET_13_spinup1000_STAGE31_'+datetime.now().strftime('%Y%m%d_%H%M%S')))
        require(not report.exists(),f'Report already exists: {report} (use a fresh --report)')
        report.mkdir(parents=True)
        try:
            cmd(['squeue','-u',UID,'-o','%.18i %.12j %.2t %.8D %.20R'],log=report/'squeue_before.txt',check=True)
            prepared={}
            for site in SITES:
                prepared[site]=configure_site(site,inputs[site],args.source_case,exe,report/f'prepare_{site}.log')
            entry=[]
            for site in SITES:
                item=inputs[site]
                entry.append(dict(site=site,case=str(prepared[site]),case_name=prepared[site].name,
                    forcing_first=item['first'],forcing_last=item['last'],annual_nc=len(item['met']),
                    fixed_co2_ppm=item['co2'],segments=200,years=1000,
                    cpu_allocation='SLURM_EXCLUSIVE_NODES',status='PREPARED_UNSUBMITTED',
                    risk='PROVISIONAL_DATM; NOT_SCIENCE_APPROVED'))
            df=pd.DataFrame(entry)
            result=report/'01_stage31_case_manifest.csv'
            df.to_csv(result,index=False)
            (report/'README.txt').write_text(
                'EXPLORATORY: 13 x 1000 model years. 200 x 5-yr segments per site.\n'
                'Stage30 DATM 271 annual NetCDF, Stage28 numeric QC only.\n'
                'CO2: NOAA annual global mean fixed at each site first forcing year.\n'
                'Slurm --exclusive: jobs may run simultaneously on distinct exclusive\n'
                'nodes, but cannot share node CPU cores. Not globally serial.\n'
                'WARNING: each site resubmits automatically 199 times; archive and\n'
                'case restart progression must be monitored. Any failed segment can\n'
                'stop the chain; submission does not certify convergence.\n'
                'ES-LJu heavy rainfall, DE-Gri/FI-Let MDS, IT-Col ZBOT proxy,\n'
                'and PFT/canopy consistency still require scientific review.\n')
            print('ALL_13_PREPARED: no site submitted until this checkpoint.',flush=True)
            if args.mode=='prepare':
                print('PREPARE_DONE:',result)
                return
            # Confirm case.submit --batch-args support BEFORE first submission.
            for site in SITES:
                case=prepared[site]
                help=cmd(['./case.submit','--help'],cwd=case,log=report/f'prepare_{site}.log')
                require('--batch-args' in help.stdout or '-a BATCH_ARGS' in help.stdout,
                        f'{site}: CIME does not support Slurm --exclusive batch argument')
            # The previous checks ran across ALL cases. Submission is deliberately
            # non-atomic: if a later submit fails, earlier jobs remain active.
            for i,site in enumerate(SITES):
                case=prepared[site]
                print(f'SUBMITTING {i+1}/13 {site} Slurm --exclusive...',flush=True)
                p=cmd(['./case.submit','--batch-args=--exclusive'],cwd=case,
                      log=report/f'submit_{site}.log',check=False)
                if p.returncode:
                    df.loc[df.site==site,'status']='SUBMIT_FAILED_MANUAL_REVIEW'
                    df.to_csv(result,index=False)
                    raise RuntimeError(f'{site}: initial CIME submit failed; earlier cases MAY be running; see {report}/submit_{site}.log')
                # CIME 5.6+ stores --batch-args in .submit_options for automatic resubmissions.
                # Verify this; otherwise 199 future segments could lose --exclusive.
                opt=case/'.submit_options'
                if not opt.is_file() or '--exclusive' not in opt.read_text(errors='replace'):
                    df.loc[df.site==site,'status']='SUBMITTED_BUT_EXCLUSIVE_PERSISTENCE_UNVERIFIED'
                    df.to_csv(result,index=False)
                    raise RuntimeError(f'{site}: initial job was submitted, but CIME did NOT persist --exclusive in .submit_options. Inspect CIME version before resubmissions; stop further site submissions.')
                df.loc[df.site==site,'status']='INITIAL_CIME_SUBMITTED_1000YR_TARGET'
                df.to_csv(result,index=False)
            print('\n=== STAGE31 INITIAL SUBMISSION COMPLETE ===',flush=True)
            print('Cases submitted:',len(SITES),'target 1000 model years/site',flush=True)
            print('Slurm allocation: --exclusive; separate CPU nodes; NOT one-site-at-a-time.',flush=True)
            print('First forcing years CO2 fixed: NOAA global annual mean',flush=True)
            print('SCIENCE APPROVAL: NONE. RUNS MAY FAIL; MONITOR RESTARTS.',flush=True)
            print('REPORT:',report,flush=True)
            print('MANIFEST:',result,flush=True)
            cmd(['squeue','-u',UID,'-o','%.18i %.25j %.2t %.8D %.20R'],log=report/'squeue_after.txt',check=False)
        except Exception:
            print(f'PARTIAL STATE/ERROR: inspect {report}. Existing submitted cases will NOT be deleted.',file=sys.stderr,flush=True)
            raise

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--mode',required=True,choices=('check','prepare','run'))
    a.add_argument('--manifest',type=Path,default=MANIFEST)
    a.add_argument('--source-case',type=Path,default=SOURCE)
    a.add_argument('--report',type=Path,help='Unique report directory, created only for prepare/run')
    a.add_argument('--skip-full-sha',action='store_true',
                   help='Skip per-file SHA hashing (NOT recommended; only if previously verified)')
    args=a.parse_args()
    try:run_campaign(args)
    except Exception as e:
        print('STAGE31 ERROR:',type(e).__name__,str(e),file=sys.stderr,flush=True)
        raise SystemExit(1)
if __name__=='__main__':main()

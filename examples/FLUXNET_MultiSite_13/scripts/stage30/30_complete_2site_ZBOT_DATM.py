#!/usr/bin/env python3
"""Stage30: complete only DE-Lnf and IT-Col DATM using explicit published height assumptions.

Uses Stage29b helper module, Stage28 frozen MET, original Stage23/24 provenance
and existing Stage29b 229-file manifests. Never rewrites old MET, BIF, DATM or
surface input; never represents Collelongo 32 m as a verified TA sensor height.

Run on IRIDIS6:
 python ~/30_complete_2site_ZBOT_DATM.py --mode check
 python ~/30_complete_2site_ZBOT_DATM.py --mode run --out "$OUT"
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import numpy as np
import pandas as pd

HOME=Path.home()
BASE=Path('/iridisfs/scratch/ly3n24/CLM_FATES')
STAGE29B=BASE/'experiments/FLUXNET_13_ZBOT_DATM_20261018_054150_1008203/reports'
HELPER=HOME/'29b_onepass_13site_dynamic_static_ZBOT_DATM.py'
SITES={
 'DE-Lnf':dict(height_m=44.0, years=(2002,2024),
    evidence='PUBLISHED_TA_SENSOR_AT_44M; HISTORICAL_CONSTANCY_ASSUMED',
    evidence_grade='PUBLISHED_AIR_TEMPERATURE_HEIGHT',
    paper='Jürgensen, J., Muhr, J. & Knohl, A. (2021). Variations of the Oxidative Ratio across Ecosystem Components and Seasons in a Managed Temperate Beech Forest (Leinefelde, Germany). Forests 12(12), 1693.',
    doi='https://doi.org/10.3390/f12121693',
    note='Section 2.1 explicitly reports air temperature measured at 44 m using a Vaisala HMP45A thermohygrometer. Its height in every forcing year 2002–2024 is not independently documented; constant 44 m is an explicit model assumption.'),
 'IT-Col':dict(height_m=32.0, years=(1996,2014),
    evidence='PUBLISHED_SITE_MEASUREMENT_HEIGHT_PROXY; NOT_TA_VERIFIED',
    evidence_grade='SITE_MEASUREMENT_HEIGHT_ONLY_PROXY_NOT_TA_SENSOR',
    paper='Keenan, T., García, R., Friend, A. D., Zaehle, S., Gracia, C. & Sabate, S. (2009). Improved understanding of drought controls on seasonal variation in Mediterranean forest canopy CO2 and water fluxes through combined in situ measurements and ecosystem modelling. Biogeosciences 6, 1423–1444.',
    doi='https://doi.org/10.5194/bg-6-1423-2009',
    note='Table 1 reports Collelongo site measurement height MH=32 m for 1998–1999; it does NOT establish TA_F sensor height or a fixed height throughout 1996–2014. Used ONLY as provisional model reference-height proxy, pending site confirmation and sensitivity assessment.')
}
README_HEAD='## Stage 30 — Literature-based height completion for DE-Lnf and IT-Col'
README_START='<!-- FLUXNET13_STAGE30_HEIGHT_START -->'
README_END='<!-- FLUXNET13_STAGE30_HEIGHT_END -->'

def ensure(b,msg):
 if not b:raise RuntimeError(msg)

def sha256(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for x in iter(lambda:f.read(4*1024*1024),b''):h.update(x)
 return h.hexdigest()

def get_helper(path):
 ensure(path.is_file(),f'Stage29b helper missing: {path}')
 spec=importlib.util.spec_from_file_location('s29b_height_helper',str(path))
 mod=importlib.util.module_from_spec(spec)
 sys.modules[spec.name]=mod
 spec.loader.exec_module(mod)
 for field in ('load_preflight','read_selected_met','surface_coords',
               'write_netcdf','write_full_datm','times_one_year'):
  ensure(hasattr(mod,field),f'Stage29b helper missing {field}')
 return mod

def read_old_manifest(report):
 p=report/'10_annual_full_DATM_SHA256_manifest.csv'
 z=report/'05_annual_ZBOT_NetCDF_SHA256_manifest.csv'
 ensure(p.is_file() and z.is_file(),'Missing successful Stage29b manifest(s)')
 d=pd.read_csv(p,dtype={'site':str}); dz=pd.read_csv(z,dtype={'site':str})
 ensure(len(d)==229 and len(dz)==229 and d.site.nunique()==11,
        f'Expected previous 11-site 229 annual files, found DATM={len(d)} ZBOT={len(dz)}')
 ensure(not set(d.site)&set(SITES),'The 29b manifest must not contain the two new sites')
 ensure(not d[['site','year']].duplicated().any(),'Duplicate 29b DATM year')
 ensure(not dz[['site','year']].duplicated().any(),'Duplicate 29b ZBOT year')
 for row in d.itertuples(index=False):
  p=Path(row.datm_nc)
  ensure(p.is_file() and sha256(p)==row.sha256,f'29b DATM changed/missing: {p}')
 for row in dz.itertuples(index=False):
  p=Path(row.zbot_nc)
  ensure(p.is_file() and sha256(p)==row.sha256,f'29b ZBOT changed/missing: {p}')
 return d,dz

def make_readme(outdir, newdir):
 a=SITES['DE-Lnf'];b=SITES['IT-Col']
 return f'''{README_START}
{README_HEAD}

This section supplements the original Stage 29b workflow, which created 229 annual provisional DATM files for 11 FLUXNET sites using **dated BIF TA_F measurement heights** (dynamic if the reported heights vary; otherwise static). Stage 30 adds **only** the two BIF-missing sites. Existing 11-site files, Stage 28 meteorology, raw BIF and surface inputs remain unchanged.

| Site | Forcing years | ZBOT in Stage 30 | Source and interpretation | Scientific caveat |
|---|---|---:|---|---|
| **DE-Lnf** | 2002–2024 | **44.0 m (static)** | **Air-temperature measurement height** independently stated in Jürgensen et al. (2021), Section 2.1; Vaisala HMP45A thermohygrometer | The article does not document an unchanged TA sensor position for the entire 2002–2024 forcing period. Static 44 m across the record is an **explicit historical-constancy assumption**, not a reconstruction of BIF history. |
| **IT-Col** | 1996–2014 | **32.0 m (static, proxy)** | **Site measurement height, MH=32 m**, in Keenan et al. (2009), Table 1, for **1998–1999** | **Not verified as the TA_F air-temperature sensor height.** The proxy is a provisional modelling assumption for 1996–2014, not observed TA metadata. Confirm with the tower team and consider ZBOT sensitivity runs before research conclusions. |

**Sources**

1. {a['paper']} [DOI]({a['doi']}). Section 2.1: air temperature at 44 m above ground.
2. {b['paper']} [DOI]({b['doi']}). Table 1: Collelongo 1998–1999 MH = 32 m; the table does not identify the TA sensor elevation.
3. [ICOS Italy Collelongo site](https://www.icos-italy.it/collelongo-it-col/) describes a 27 m meteorological/micrometeorological station, highlighting why different reported height definitions should **not** be conflated.

**Implementation and traceability**

- Static heights are model reference-height inputs, not new FLUXNET BIF observations. Stage 30 writes `ZBOT_HEIGHT_DOCUMENTED=0` in its ZBOT-only files to indicate no dated TA_F BIF height epochs for these two stations.
- All 7 meteorological variables are copied from the SHA256-validated **Stage 28 selected forcing**, without altering values or sampling times. Each annual DATM contains `TBOT, QBOT, PSRF, FSDS, FLDS, WIND, PRECTmms, ZBOT`, 17,520 half-hour records and a `noleap` calendar.
- Every new annual NetCDF and every pre-existing Stage 29b annual NetCDF has a separate SHA256 record in the consolidated inventory. Stage 30 adds **42 annual files**, bringing the consolidated provisional DATM inventory to **271 files / 13 sites**, if verification completes.
- The ZBOT assumption for IT-Col, historical constancy for DE-Lnf, unresolved Stage 28 MET scientific issues, and TA/WS reference-height differences mean **NOT scientifically approved for production 500/1000-year spin-up**. Short smoke tests and explicit sensitivity experiments are appropriate.
- Original Stage 29b report directory: `{outdir}`.
- Stage 30 complementary outputs: `{newdir}`. These absolute IRIDIS paths are run-specific and need not be committed to GitHub.

{README_END}
'''

def patch_readme(path,block):
 path=Path(path)
 ensure(path.is_file(),f'Cannot find repository README {path}')
 txt=path.read_text(encoding='utf-8')
 ensure((README_START in txt)==(README_END in txt),'Unbalanced existing README Stage30 markers')
 if README_START in txt:
  s=txt.index(README_START);e=txt.index(README_END)+len(README_END)
  txt=txt[:s]+block.strip()+txt[e:]
 else:
  txt=txt.rstrip()+'\n\n'+block.strip()+'\n'
 path.write_text(txt,encoding='utf-8')

def run(args):
 mod=get_helper(args.stage29b_script)
 ensure(args.old_reports.is_dir(),f'Stage29b report missing: {args.old_reports}')
 class Preflight:pass
 a=Preflight();a.stage23=Path(args.stage23);a.stage24=Path(args.stage24)
 a.stage28=Path(args.stage28);a.external_heights=None
 sources, src_hash, original_epochs, summary, m, risks=mod.load_preflight(a)
 manifest=m.set_index('site')
 # Ensure height absent in real BIF so documentary fallback cannot override a height record.
 for site in SITES:
  ensure(original_epochs[(original_epochs.site==site)&(original_epochs.variable=='TA_F')].empty,
         f'{site}: TA_F BIF now present! Do not apply literature height proxy')
  ensure(mod.SITES[site]==SITES[site]['years'],f'{site}: unexpected forcing year scope')
  ensure(manifest.loc[site,'sha256'] and Path(manifest.loc[site,'forcing_path']).is_file(),
         f'{site}: Stage28 selected MET absent')
 # Verify no source changed, including all original 229 files; expensive but intentionally deterministic.
 old_d,old_z=read_old_manifest(args.old_reports)
 surf={site:mod.surface_coords(site,mod.SITEBASE) for site in SITES}
 print('PREFLIGHT: Stage28 all 13 SHA256 verified; Stage23/24 BIF sources verified',flush=True)
 print('PREFLIGHT: Stage29b 229 DATM + 229 ZBOT SHA256 verified',flush=True)
 for site,row in SITES.items():
  print(f"{site}: {row['height_m']:g} m STATIC; evidence={row['evidence_grade']}; years={row['years'][0]}-{row['years'][1]}",flush=True)
 if args.mode=='check':
  print('CHECK_ONLY: no NetCDF or report written',flush=True);return
 ensure(args.out and not args.out.exists(),'Use an entirely NEW --out directory; overwrite forbidden')
 if args.repo_readme is not None:
  ensure(args.repo_readme.is_file(),f'GitHub repository README not found: {args.repo_readme}')
 args.out.mkdir(parents=True,exist_ok=False)
 rp=args.out/'reports';rp.mkdir()
 policy={'format':'FLUXNET_MultiSite_13_stage30_documentary_static_ZBOT_v1',
         'created_utc':datetime.now(timezone.utc).isoformat(),
         'source_stage29b_reports':str(args.old_reports),
         'source_stage29b_script':str(args.stage29b_script),
         'source_stage29b_script_sha256':sha256(args.stage29b_script),
         'source_stage29b_DATM_inventory_sha256':sha256(args.old_reports/'10_annual_full_DATM_SHA256_manifest.csv'),
         'source_stage28_selected_manifest_sha256':sha256(args.stage28/'01_selected_13site_STAGE28_provisional_manifest.csv'),
         'mode':'SCIENCE_PROVISIONAL_NOT_SPINUP_APPROVED',
         'time_convention':'30min NO_LEAP; reference heights are static proxies/assumptions not BIF epochs',
         'sites':SITES}
 pp=rp/'01_literature_ZBOT_policy.json'
 pp.write_text(json.dumps(policy,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 policysha=sha256(pp)
 newdat=[];newz=[];yearly=[]
 for site,item in SITES.items():
  first,last=item['years'];height=float(item['height_m'])
  lat,lon,surf_file=surf[site]
  ix,meteor=mod.read_selected_met(site,manifest.loc[site],first,last)
  for yr in range(first,last+1):
   yearix=mod.times_one_year(yr)
   offset=(yr-first)*17520
   ensure(np.array_equal(ix[offset:offset+17520].to_numpy(),yearix.to_numpy()),
          f'{site} {yr}: time axis mismatch')
   zz=np.full(17520,height,dtype=np.float64)
   documented=np.zeros(17520,dtype=bool)  # No actual dated TA_F BIF data for either site!
   targetz=args.out/site/'zbot_annual'
   targetz.mkdir(parents=True,exist_ok=True)
   pz=targetz/f'{site}_ZBOT_noleap_{yr}_PROVISIONAL.nc'
   mod.write_netcdf(pz,site,yr,yearix,zz,documented,lat,lon,surf_file,
                   policysha,str(manifest.loc[site,'sha256']))
   targetd=args.out/site/'datm_annual';targetd.mkdir(parents=True,exist_ok=True)
   pdst=targetd/f'{site}_DATM_{yr}_PROVISIONAL.nc'
   mod.write_full_datm(pdst,site,yr,zz,documented,meteor,offset,lat,lon,
                 surf_file,policysha,str(manifest.loc[site,'sha256']),'STATIC_LITERATURE_ASSUMPTION')
   # Explicit provenance on BOTH files, distinguishing actual air-temperature proof
   # from a generic measurement-height proxy; assert metadata roundtrips.
   from netCDF4 import Dataset
   for file in (pz,pdst):
    with Dataset(file,'a') as nc:
     nc.zbot_documentary_evidence_grade=item['evidence_grade']
     nc.zbot_height_m=float(height)
     nc.zbot_citation_doi=item['doi']
     nc.zbot_scientific_caveat=item['note']
     nc.zbot_historical_constancy_assumed=1
     nc.zbot_dated_TA_BIF_epochs_available=0
    with Dataset(file) as nc:
     ensure(abs(float(nc.zbot_height_m)-height)<1e-9,'NetCDF reference-height attribute mismatch')
     ensure(np.array_equal(np.asarray(nc['ZBOT'][:,0,0]),zz),'NetCDF height mismatch')
     ensure(len(nc.dimensions['time'])==17520,'Wrong NetCDF time dimension')
     ensure(np.allclose(np.asarray(nc['time'][:]),np.arange(17520)/48.),'Wrong NetCDF times')
     ensure(nc['time'].calendar=='noleap','Wrong NetCDF calendar')
    if file==pz:
     with Dataset(file) as nc:
      ensure((np.asarray(nc['ZBOT_HEIGHT_DOCUMENTED'][:,0,0])==0).all(),
             'Literature height must NOT be flagged as documented dated BIF')
   newdat.append(dict(site=site,year=yr,datm_nc=str(pdst),sha256=sha256(pdst),
       zbot_mode='STATIC_LITERATURE_ASSUMPTION',
       stage28_forcing_sha256=str(manifest.loc[site,'sha256']),
       approval='PROVISIONAL_SCIENCE_REVIEW_PENDING',height_m=height,
       evidence_grade=item['evidence_grade']))
   newz.append(dict(site=site,year=yr,zbot_nc=str(pz),sha256=sha256(pz),
       stage28_forcing_path=str(manifest.loc[site,'forcing_path']),
       stage28_forcing_sha256=str(manifest.loc[site,'sha256']),
       provenance_status='LITERATURE_STATIC_PROVISIONAL_NOT_DATED_TA_BIF',
       height_m=height,evidence_grade=item['evidence_grade']))
   yearly.append(dict(site=site,year=yr,height_m=height,
           documented_TA_BIF_halfhours=0,assumed_static_halfhours=17520))
  print(f'{site}: wrote {last-first+1} yearly ZBOT-only and full DATM NetCDF files',flush=True)
 # Check all original inventories again after writes: no mutation allowed.
 read_old_manifest(args.old_reports)
 new_df=pd.DataFrame(newdat)
 new_zdf=pd.DataFrame(newz)
 all_df=pd.concat([old_d.assign(height_m=np.nan,evidence_grade='DATED_BIF_TA_F'),new_df],ignore_index=True)
 all_zdf=pd.concat([old_z.assign(height_m=np.nan,evidence_grade='DATED_BIF_TA_F'),new_zdf],ignore_index=True)
 ensure(len(all_df)==271 and len(all_zdf)==271 and all_df.site.nunique()==13,
        f'Consolidated count invalid: DATM={len(all_df)} ZBOT={len(all_zdf)} sites={all_df.site.nunique()}')
 ensure(not all_df[['site','year']].duplicated().any(),'Duplicate final DATM site/year')
 ensure(not all_zdf[['site','year']].duplicated().any(),'Duplicate final ZBOT site/year')
 expect={(s,y) for s,(first,last) in mod.SITES.items() for y in range(first,last+1)}
 ensure(set(map(tuple,all_df[['site','year']].to_numpy()))==expect,
        'Consolidated full DATM annual coverage incomplete')
 ensure(set(map(tuple,all_zdf[['site','year']].to_numpy()))==expect,
        'Consolidated ZBOT annual coverage incomplete')
 all_df=all_df.sort_values(['site','year']).reset_index(drop=True)
 all_zdf=all_zdf.sort_values(['site','year']).reset_index(drop=True)
 new_df.to_csv(rp/'02_new_2site_DATM_SHA256_manifest.csv',index=False)
 new_zdf.to_csv(rp/'03_new_2site_ZBOT_SHA256_manifest.csv',index=False)
 all_df.to_csv(rp/'04_consolidated_13site_271_DATM_SHA256_manifest.csv',index=False)
 all_zdf.to_csv(rp/'05_consolidated_13site_271_ZBOT_SHA256_manifest.csv',index=False)
 pd.DataFrame(yearly).to_csv(rp/'06_2site_annual_height_assumption_audit.csv',index=False)
 risk=pd.DataFrame([dict(site=site,height_m=item['height_m'],years=f"{item['years'][0]}-{item['years'][1]}",
        citation=item['paper'],doi=item['doi'],evidence_grade=item['evidence_grade'],
        warning=item['note'],readiness='PROVISIONAL_DATM_CREATED_NOT_SCIENCE_APPROVED')
        for site,item in SITES.items()])
 risk.to_csv(rp/'07_2site_literature_evidence_and_science_caveats.csv',index=False)
 block=make_readme(args.old_reports,args.out)
 (rp/'README_STAGE30_HEIGHT_REFERENCES.md').write_text(block,encoding='utf-8')
 if args.repo_readme is not None:
  patch_readme(args.repo_readme,block)
  print('LOCAL_REPOSITORY_README_UPDATED:',args.repo_readme,flush=True)
 status={'created_utc':datetime.now(timezone.utc).isoformat(),
  'new_sites':2,'new_annual_datm_files':len(newdat),
  'prior_annual_datm_files':len(old_d),'consolidated_sites':13,
  'consolidated_annual_DATM':len(all_df),
  'original_11site_annual_DATM_SHA_verified':True,
  'stage28_forcing_SHA_verified':True,
  'BIF_TA_documented_for_the_two_sites':False,
  'science_MET_approved':False,'science_ZBOT_approved':False,
  'IT_Col_32m_is_air_temperature_measurement_height':False,
  'README_updated':str(args.repo_readme) if args.repo_readme else None}
 (rp/'08_summary_and_scope.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
 print('\n=== STAGE30 COMPLETE ===',flush=True)
 print('DE-Lnf: 44 m published TA height; static assumption across 2002-2024',flush=True)
 print('IT-Col: 32 m published MH only; STATIC PROXY, NOT CONFIRMED TA height',flush=True)
 print('New yearly DATM:',len(newdat),'Consolidated yearly DATM:',len(all_df),'sites:',all_df.site.nunique(),flush=True)
 print('Original 229 files unchanged and SHA256 verified: YES',flush=True)
 print('Science approval: NONE (provisional inputs and height assumptions)',flush=True)
 print('REPORTS:',rp,flush=True)
 print('README_SNIPPET:',rp/'README_STAGE30_HEIGHT_REFERENCES.md',flush=True)
 print('MANIFEST:',rp/'04_consolidated_13site_271_DATM_SHA256_manifest.csv',flush=True)

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--mode',required=True,choices=['check','run'])
 p.add_argument('--out',type=Path)
 p.add_argument('--stage29b-script',type=Path,default=HELPER)
 p.add_argument('--old-reports',type=Path,default=STAGE29B)
 p.add_argument('--stage23',type=Path,default=HOME/'FLUXNET_13_stage23_BIF_20261018_034917_060345')
 p.add_argument('--stage24',type=Path,default=HOME/'FLUXNET_13_stage24_BIF_unique_NOLEAP_20261018_040135_133053')
 p.add_argument('--stage28',type=Path,default=BASE/'experiments/FLUXNET_MultiSite_13_MET_stage28_20261018_052344_851367/reports')
 p.add_argument('--repo-readme',type=Path,
   help='Optional actual LOCAL GitHub-worktree README.md; appends/replaces marked Stage30 section only after success')
 args=p.parse_args()
 if args.mode=='run' and not args.out:p.error('--mode run requires a new --out directory')
 try:run(args)
 except Exception as e:raise SystemExit(f'STAGE30 ERROR: {type(e).__name__}: {e}')
if __name__=='__main__': main()

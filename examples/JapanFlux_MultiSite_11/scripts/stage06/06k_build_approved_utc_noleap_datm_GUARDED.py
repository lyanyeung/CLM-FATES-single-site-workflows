#!/usr/bin/env python3
"""Stage06K: UTC NOLEAP CDEPS/DATM forcing for the 11 JapanFlux sites from every QC decision approved by 2026-11-06
(not activated). Guarded writer.

Input: the twelve Stage06J tables (Stage06E plus the approved G2A/G2B TA rules; gzip SHA-256 pinned below).
Conversion, checks and attribute evidence (F4 drift, Tgf clock windows, accepted clock limits, E3 years) come from the
pinned Stage06F module and its private Stage06A instance, unchanged: approved tags only, full noleap years, no missing
value, e>0, physical ranges, exact UTC permutation, FSDS solar centroid, clock-limit guard.
Changes from Stage06F (user decisions 2026-11-06):
  G1 JP-Tgf forcing years 2004-2022 (2002-2003: humidity sensor wet against raw ERA5, logger clock errors);
  G2A/G2B are named in the approval attribute; R (other TA departures kept as measured) is recorded per site.
--self-test               synthetic checks, no files
--table-dir D             check only: reads, converts and tests all sites, writes nothing
--table-dir D --out NEW --write --ack-utc-plus9-cyclic-shift [--compare-06f SUMMARY]
                          also writes NetCDF files, stream plans and summaries to a brand-new directory; with
                          --compare-06f (Stage06F summary_APPROVED_20261105.json), lists every file whose data differ
                          from Stage06F and every Stage06F year no longer built
No case, stream activation, Slurm or model run. The files are not production forcing until separately accepted.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

F_PIN=('06f_build_approved_utc_noleap_datm_GUARDED.py','b974671f5f5dcc7a1e87a1f7c0403086839807a5de785fb8d8a76e6ed17b7f40')
TABLES={'JP-Api':'de568f13cca53a79fd48c613d49cd369f5175923d127c388f249a85a1b17ce19','JP-Fhk':'b1a7a0b870140016721c0a1f3cc8b87575ddf1903e159bc6495e2a5bc4ce8bcb',
 'JP-Fjy':'167add10aa4ef4f046d121a759abf372a468de1d60c8238035296b807682ef76','JP-Khw':'71c46d34c53c1c93332822a7bff5ccc9680cf4ef058450d3b8ffd11164b7f4ae',
 'JP-Spp':'217f4e93b94a5979b206bc3c83bec3f2e276286f56ae3ed688ef3be3aef07c68','JP-Tak':'fb7ec2fb89cdccf5c8bd5edde6406d7e4e2d0fd309bf48e045bbad5676445f4f',
 'JP-Tef':'0ce8f7659d2328c5d2fbfc808e5700fc903cf13596deb43d320b602a82295909','JP-Tmd':'7e98882c0b583fd91586bc04172414556d9a601ea8379dab31090b4883a24de5',
 'JP-Yms':'3de55e254f6975f05198c254325fb9ef3bc45e2cf28d7b938acd403c5dffbf6a','JP-Tgf_HH':'4f66685b14d4d13be62d914fd5179c1668b9f36ed3b8dad09b5a94814ddae5a9',
 'JP-Tom_HH':'03ce4521d0bb5c2e5031bf418acc1535e632d801b66e6f4bdfdc296126e54b95','JP-Tom_HR':'59fba16a38dad2afd3da28bb782335873ff0b235610e71026299ee35de75dc29'}
TABLE_NAME='{}_final_preforcing_APPROVED_20261106_G2.tsv.gz'   # Stage06J output name
FILE='{}_JP11_UTC_NOLEAP_DATM_APPROVED_20261106_{}.nc'
TA_KEPT={'JP-Khw':'2009-03-13 11:00..03-14 10:00 local: tower TA about 15 C below the reference for 23.5 h, kept (R1, no fault evidence); ',
         'JP-Yms':'2008-11-12 12:00..11-16 16:00 local: tower TA about 13 C below the reference for 100 h, kept (R2, no fault evidence); '}
TA_KEPT_ALL='other tower TA departures from the reanalysis kept as measured (decision R; Stage06I review list, mostly cold-pool nights at the mountain sites)'

def load_f6():
    name,expected=F_PIN;path=Path(__file__).with_name(name)
    if not path.is_file() or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('pinned 06F script missing or hash mismatch')
    spec=importlib.util.spec_from_file_location('stage06f_for_06k',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
f6=load_f6();a6=f6.a6;br=a6.br;FILE_06F=f6.FILE
# Stage06A build_site and stream_plan read these module globals: point this private instance at the Stage06J tables and
# the Stage06K file names. Nothing else in the pinned modules is changed.
a6.TABLES=TABLES;a6.TABLE_NAME=TABLE_NAME;a6.FILE=FILE
YEARS={**f6.YEARS,'JP-Tgf':(2004,2022)}   # E3 + G1
PERIOD={**f6.PERIOD,'JP-Tgf':'G1: local 2002-2003 excluded (humidity sensor about 2.5-2.7 C dew point wetter than raw ERA5, logger clock errors; Stage06H)'}
CLOCK={**f6.CLOCK,'JP-Tgf':f6.CLOCK['JP-Tgf']+'; the 2002 and 2003 windows lie outside the forcing period (G1)'}
QC_APPROVAL=(f6.QC_APPROVAL+'; Stage06J: G2A short TA faults and G2B gap-fill TA departures treated as gaps, TA and VPD (and RH at Tgf) '
             'from the approved reference (approved 2026-11-06)')

def changed_vs_06f(old,sites):
    """Stage06F summary 'sites' -> ({site: {year: [variables whose data hash differs, or NOT_IN_06F]}},
    {site: [Stage06F years not built here]}) for the sites built here."""
    changed={};removed={}
    for site,e in sites.items():
        built=set()
        for name,x in e['files'].items():
            y=int(name[-7:-3]);built.add(y);o=old.get(site,{}).get('files',{}).get(FILE_06F.format(site,y))
            d=['NOT_IN_06F'] if o is None else [v for v,h in sorted(x['data_sha256_by_variable'].items()) if o['data_sha256_by_variable'][v]!=h]
            if d:changed.setdefault(site,{})[str(y)]=d
        gone=sorted(int(n[-7:-3]) for n in old.get(site,{}).get('files',{}) if int(n[-7:-3]) not in built)
        if gone:removed[site]=gone
    return changed,removed

def run(a):
    write=a.out is not None
    if write:
        if not a.ack:raise ValueError('--write needs --ack-utc-plus9-cyclic-shift')
        if a.out.exists() or a.out.is_symlink() or not a.out.parent.is_dir() or a.out.parent.is_symlink():raise ValueError('fresh --out required')
        if a.table_dir.resolve() in (a.out.resolve(),*a.out.resolve().parents):raise ValueError('--out inside the source directory')
        a.out.mkdir()
    a.cb_dir=a.table_dir;a.years={**YEARS,**a.years}   # Stage06A build_site reads a.cb_dir and a.years
    report={'stage':'06K','status':'APPROVED_20261106_UTC_NOLEAP_DATM_NOT_ACTIVATED' if write else 'CHECK_ONLY_NOTHING_WRITTEN',
        'input':'Stage06J final pre-forcing tables (Stage06E plus approved G2A/G2B, 2026-11-06)','table_gzip_sha256':TABLES,'sites':{}}
    allrows=[]
    for site in a.sites:
        print('STAGE06K',site,flush=True)
        utc,rows,site_med,(y0,y1,lat,lon,zbot,formula)=a6.build_site(a,site)
        odd=f6.unaccepted_clock(site,rows)
        if odd:raise ValueError('%s: FSDS centroid >15 min off UTC in %s, not an accepted clock limit'%(site,odd))
        entry={'years':[y0,y1],'period_note':PERIOD.get(site,'full approved table range'),'lat':lat,'lon':lon,'zbot_m':zbot,'es_formula':formula,
               'clock':CLOCK.get(site,'BIF UTC_OFFSET 9'),'fsds_centroid_minus_toa_min_site_median':round(site_med,1),
               'accepted_clock_limit_years':[r['year'] for r in rows if r['clock_review']=='YES'],
               'humidity_screen':{k[9:]:sum(r[k] for r in rows) for k in rows[0] if k.startswith('humidity_')},
               'humidity_drift_F4':{str(r['year']):f6.f4_note(site,r['year']) for r in rows if any(y0<=r['year']<=y1 for y0,y1,_ in f6.F4.get(site,()))},
               'ta_kept':TA_KEPT.get(site,'')+TA_KEPT_ALL,'files':{}}
        if write:
            d=a.out/site;d.mkdir()
            for (y,spd,f,tail),row in zip(utc,rows):
                attrs={'title':'JapanFlux MultiSite 11 UTC NOLEAP DATM forcing from the QC decisions approved by 2026-11-06 (not activated)',
                    'site':site,'forcing_year':y,'forcing_period':'%d-%d; %s'%(y0,y1,entry['period_note']),
                    'source_tables':','.join('%s sha256 %s'%(k,TABLES[k]) for k in a6.SITES[site][0]),'qc_approval':QC_APPROVAL,
                    'science_status':'QC_APPROVED_DECISIONS_20261106; DATM_NOT_ACTIVATED','model_submission_authorised':'FALSE',
                    'time_reference':'UTC interval centre; source TIMESTAMP_START on UTC+9 moved -9 h by whole slots',
                    'clock_basis':entry['clock'],
                    'clock_check':'FSDS centroid minus TOA %.1f min on the UTC axis; %s'%(row['fsds_centroid_minus_toa_min_median'],
                        'sub-slot offset accepted as a known limit (user, 2026-11-05)' if row['clock_review']=='YES' else 'within 15 min'),
                    'time_boundary_policy':'last %d slots from %s'%(tail['tail_slots'],tail['tail_source']),
                    'calendar_policy':'noleap; local Feb 29 rows removed before the UTC shift',
                    'humidity':'QBOT=0.622e/(p-0.378e), e=es(TA)-VPD, es=%s; DATM caps QBOT at its own qsat'%formula,
                    'humidity_qc':'E1A/E1B outliers replaced by the reference RH at the tower TA (approved); screen after E1 and G2 this year: '
                        'Td>=28C %d, saturated at TA>=28C %d, RH<5%% %d (remaining cells are listed in Stage06H)'%(
                        row['humidity_Td_ge_28C'],row['humidity_saturated_TA_ge_28C'],row['humidity_RH_lt_5pct']),
                    'humidity_drift':f6.f4_note(site,y),'ta_qc':'G2A/G2B cells filled from the approved reference (Stage06J); '+entry['ta_kept'],
                    'radiation_precipitation':'FSDS=max(SW_IN_F,0); FLDS=LW_IN_F; PRECTmms=P_F/%d s'%(86400//spd),
                    'zbot_evidence':'TA_F sensor height %.1f m (BIF/BADM)'%zbot,'low_tower_coverage':row['low_tower_coverage']}
                p=d/FILE.format(site,y);h=a6.write_nc(p,site,y,spd,f,lat,lon,zbot,attrs)
                row['file']=p.name;row['file_sha256']=br.sha(p);row['data_sha256_by_variable']=h
                entry['files'][p.name]={'file_sha256':row['file_sha256'],'data_sha256_by_variable':h}
            with (d/'stream_plan_NOT_ACTIVATED.json').open('x',encoding='utf-8') as f:json.dump(a6.stream_plan(site,y0,y1,utc),f,indent=1);f.write('\n')
        report['sites'][site]=entry;allrows.extend(rows)
        print(json.dumps({'site':site,'years':[y0,y1],'files':len(rows),'fsds_offset_min':round(site_med,1),'accepted_clock_limit_years':entry['accepted_clock_limit_years'],
            'humidity_screen':entry['humidity_screen'],'low_coverage_years':[r['year'] for r in rows if r['low_tower_coverage']!='NO']}),flush=True)
    view={s:{**{k:v for k,v in e.items() if k!='files'},'files':{n:{k:v for k,v in x['data_sha256_by_variable'].items() if k!='QBOT'} for n,x in e['files'].items()}}
          for s,e in report['sites'].items()}
    report['fingerprint_without_QBOT_and_file_bytes']=br.fingerprint(view)
    if write:
        report['QBOT_digest']=f6.digest(report['sites'],'QBOT');report['file_bytes_digest']=f6.digest(report['sites'],None)
        if a.compare_06f:
            report['changed_vs_06F'],report['removed_vs_06F']=changed_vs_06f(json.loads(a.compare_06f.read_text(encoding='utf-8'))['sites'],report['sites'])
            report['changed_vs_06F_sha256']=hashlib.sha256(json.dumps([report['changed_vs_06F'],report['removed_vs_06F']],sort_keys=True).encode()).hexdigest()
    report['site_year_rows']=[{k:v for k,v in r.items() if k!='data_sha256_by_variable'} for r in allrows]
    if write:
        cols=[k for k in allrows[0] if k!='data_sha256_by_variable']
        with (a.out/'site_year_summary_APPROVED_20261106.tsv').open('x',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,cols,delimiter='\t',extrasaction='ignore');w.writeheader();w.writerows(allrows)
        with (a.out/'summary_APPROVED_20261106.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=1,sort_keys=True);f.write('\n')
    print('STAGE06K COMPLETE;',('DATM FILES WRITTEN TO '+str(a.out)) if write else 'CHECK ONLY, NOTHING WRITTEN','; NOT ACTIVATED; NO CASE, NO SLURM')
    print(json.dumps({'fingerprint':report['fingerprint_without_QBOT_and_file_bytes'],'files':len(allrows),**({k:report[k] for k in
        ('QBOT_digest','file_bytes_digest','changed_vs_06F_sha256','changed_vs_06F','removed_vs_06F') if k in report})}))

def selftest():
    a6.selftest()   # f6.selftest() would assert its own (now repointed) table pins
    assert f6.unaccepted_clock('JP-Tom',[{'year':2008,'clock_review':'YES'},{'year':2009,'clock_review':'YES'}])==[2009]
    assert a6.TABLES is TABLES and a6.TABLE_NAME==TABLE_NAME and a6.FILE==FILE and FILE_06F!=FILE
    assert sum(YEARS.get(s,v[1:3])[1]-YEARS.get(s,v[1:3])[0]+1 for s,v in a6.SITES.items())==215
    assert YEARS['JP-Tgf']==(2004,2022) and YEARS['JP-Khw']==(2007,2021) and 'G1' in PERIOD['JP-Tgf'] and 'G1' in CLOCK['JP-Tgf']
    sites={'JP-X':{'files':{FILE.format('JP-X',2004):{'data_sha256_by_variable':{'QBOT':'a','TBOT':'b'}},FILE.format('JP-X',2005):{'data_sha256_by_variable':{'QBOT':'a'}}}}}
    old={'JP-X':{'files':{FILE_06F.format('JP-X',y):{'data_sha256_by_variable':{'QBOT':'c','TBOT':'b'}} for y in (2002,2003,2004)}}}
    assert changed_vs_06f(old,sites)==({'JP-X':{'2004':['QBOT'],'2005':['NOT_IN_06F']}},{'JP-X':[2002,2003]})
    print('STAGE06K SELF-TEST PASS: 06A self-test, clock-limit guard, table/file repointing, G1 file count 215, 06F diff and removed years; NO FILES')

def main():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--self-test',action='store_true');p.add_argument('--table-dir',type=Path,help='Stage06J output');p.add_argument('--out',type=Path)
    p.add_argument('--write',action='store_true');p.add_argument('--ack-utc-plus9-cyclic-shift',dest='ack',action='store_true')
    p.add_argument('--compare-06f',type=Path,help='Stage06F summary_APPROVED_20261105.json')
    p.add_argument('--sites',default=','.join(a6.SITES));p.add_argument('--years',action='append',default=[],help='SITE=FIRST-LAST override')
    a=p.parse_args()
    if a.self_test:selftest();return
    if a.table_dir is None or a.write!=(a.out is not None):p.error('--table-dir required; --write and --out go together')
    if a.compare_06f and not a.write:p.error('--compare-06f needs --write')
    a.sites=a.sites.split(',')
    if not set(a.sites)<=set(a6.SITES):p.error('unknown site')
    a.years={s:tuple(int(x) for x in r.split('-')) for s,r in (y.split('=') for y in a.years)}
    run(a)
if __name__=='__main__':main()

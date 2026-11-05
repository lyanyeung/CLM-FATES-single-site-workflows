#!/usr/bin/env python3
"""Stage06F: UTC NOLEAP CDEPS/DATM forcing for the 11 JapanFlux sites from every QC rule approved by 2026-11-05
(not activated; items still under review are named in the attributes). Guarded writer.

Input: the twelve Stage06E tables (Stage05CB plus the approved Stage06C E rules; gzip SHA-256 pinned below).
Conversion and checks are the pinned Stage06A functions, unchanged: approved tags only, full noleap years, no missing
value, e>0, physical ranges, exact UTC permutation, FSDS solar centroid (per year |median| <= 90 min, site <= 20 min).
Changes from Stage06A (user decisions 2026-11-05):
  E3 forcing years Khw 2007-2021, Tef 2002-2023, Tmd 2006-2023 (others: full approved range; Tom 1999-2010, D3b);
  a year whose FSDS centroid is >15 min off must be an accepted sub-slot clock limit (Tef 2006, Tmd 2022, Yms 2004,
  Tom 2007/2008), otherwise the build stops;
  attributes record the approved E1/E2 rules, the Tgf clock windows and the F4 humidity drift kept as measured.
--self-test               synthetic checks, no files
--table-dir D             check only: reads, converts and tests all sites, writes nothing
--table-dir D --out NEW --write --ack-utc-plus9-cyclic-shift [--compare-06a SUMMARY]
                          also writes NetCDF files, stream plans and summaries to a brand-new directory; with
                          --compare-06a (Stage06A summary_CANDIDATE.json), lists every file whose data differ from 06A
No case, stream activation, Slurm or model run. The files are not production forcing until separately accepted.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

A6_PIN=('06a_build_utc_noleap_datm_candidates_GUARDED.py','88ff83e3f7fb6ec42c0b70eaf9d12019b70826851fe6132961dde08c0dc633cc')
TABLES={'JP-Api':'f97ad3ff74dd803c7ac491f171653007fa9c120d7e021ea5902f330c9849104f','JP-Fhk':'b1a7a0b870140016721c0a1f3cc8b87575ddf1903e159bc6495e2a5bc4ce8bcb',
 'JP-Fjy':'d16757109fce1a7cb4a85eb4b61f9aeec624bd26dcf39e7e0f090db137fea35c','JP-Khw':'103e5fdf856fec6ef52ec741dc583fe8940df4f8b55f6369c4b6a722c3105668',
 'JP-Spp':'adfa7311ac09201fe073469c4d76a0318930ac66a26578b4b46f0654ca200c72','JP-Tak':'c5433d52f9903a9798cbb56e94f6bc2e86861f719ce25c3ece9a8c38ac54b3a8',
 'JP-Tef':'a745ea2f704d5ee63ee018b38fb0c19fb1b084c590dfa319a000bc8335a61cb8','JP-Tmd':'12981895f344318fb511e05e10911f9d5c11d918497566603e8724d040414651',
 'JP-Yms':'d6528b6f3dee395e827d8b39dcf2309e208b3f74f1bf9b7abaf1c14074613e5f','JP-Tgf_HH':'589632bae2787738746e206016da9e39bfb18210a62afe4ff25e71c4d598d9f9',
 'JP-Tom_HH':'03ce4521d0bb5c2e5031bf418acc1535e632d801b66e6f4bdfdc296126e54b95','JP-Tom_HR':'59fba16a38dad2afd3da28bb782335873ff0b235610e71026299ee35de75dc29'}
TABLE_NAME='{}_final_preforcing_APPROVED_20261105_E.tsv.gz'   # Stage06E output name
FILE='{}_JP11_UTC_NOLEAP_DATM_APPROVED_20261105_{}.nc'
YEARS={'JP-Khw':(2007,2021),'JP-Tef':(2002,2023),'JP-Tmd':(2006,2023)}   # E3
PERIOD={'JP-Khw':'E3: local 2004-2006 have no tower TA/VPD/SW (all ERA-filled); the cycle uses the continuous tower period after them',
        'JP-Tef':'E3: local 2001 has about 33 % tower coverage','JP-Tmd':'E3: local 2005 has about 38 % tower coverage',
        'JP-Tom':'D3b: RH drifts wet from 2011'}
CLOCK_LIMITS={'JP-Tef':(2006,),'JP-Tmd':(2022,),'JP-Yms':(2004,),'JP-Tom':(2007,2008)}
TGF_E2=('logger clock windows corrected by whole half-hours on QC0 cells (E2, approved 2026-11-05): 2002-01-01..2002-10-23, '
        '2005-01-14..2005-03-22 and 2015-12-29..2017-01-02 moved -30 min, 2003-01-02..2003-04-18 moved +30 min; not confirmed '
        'by the TA phase and left unchanged: 2008-06-22..07-31 (+18.7 min), 2008-09-24..10-24 (-19.1 min), 2019-08-12..10-09 (+25.7 min)')
# F4 evidence: Stage06C humidity_by_year.tsv (QC0 rows; reference = same-release ERA RH at t+1h)
F4={'JP-Api':((2006,2017,'tower RH median +5.5 to +8.7 % above the reference (other years -1.5 to +4.2 %); tower RH>=99.5 % at TA>=20 C '
               'in up to 248 half-hours per year, reference none'),),
    'JP-Fjy':((2005,2006,'tower RH median +8.5 / +12.2 % above the reference (2001-2008 otherwise +3.1 to +6.2 %); tower RH>=99.5 % '
               'at TA>=20 C in 177 / 490 half-hours, reference none'),
              (2019,2021,'tower RH>=99.5 % at TA>=20 C in 328 / 159 / 69 half-hours, reference none')),
    'JP-Khw':((2019,2021,'tower RH clipped at 100 % near saturation: RH>=99.5 % at TA>=20 C in 1625 / 1582 / 1833 half-hours versus '
               'reference RH>=97 % in 650 / 606 / 432'),),
    'JP-Tef':((2016,2016,'tower RH>=99.5 % at TA>=20 C in 688 half-hours versus reference RH>=97 % in 132'),
              (2019,2019,'tower RH>=99.5 % at TA>=20 C in 527 half-hours versus reference RH>=97 % in 47')),
    'JP-Yms':((2015,2015,'tower RH>=99.5 % at TA>=20 C in 639 half-hours, reference none'),)}
QC_APPROVAL=('Stage05CB: D1-D14 approved 2026-11-05, D1, D2 and C1-C3 2026-11-04; Stage06E: E1A humid and E1B dry humidity '
             'outliers replaced by the reference RH at the tower TA, E2 Tgf clock windows (F1-F3, approved 2026-11-05)')
OPEN_ALL='tower TA anomalies against the reference (Stage06I, G2)'
OPEN={'JP-Tgf':'2002-2003 humidity about 2.5-2.7 C dew point wetter than raw ERA5 at TA>=25 C, other years -1.5 to +0.1 C (Stage06H, G1); '}

def load_a6():
    name,expected=A6_PIN;here=Path(__file__).parent
    for path in (here/name,here.parent/'stage06'/name):
        if path.is_file() and not path.is_symlink():break
    else:raise ValueError('pinned 06A script not found')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('pinned 06A hash mismatch')
    spec=importlib.util.spec_from_file_location('stage06a_for_06f',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
a6=load_a6();br=a6.br;FILE_06A=a6.FILE
# Stage06A build_site and stream_plan read these module globals: point them at the Stage06E tables and the Stage06F
# file names. Nothing else in this private instance of the pinned module is changed.
a6.TABLES=TABLES;a6.TABLE_NAME=TABLE_NAME;a6.FILE=FILE
CLOCK={**a6.CLOCK,'JP-Tgf':'BADM UTC_OFFSET 9; '+TGF_E2}

def unaccepted_clock(site,rows):
    return [r['year'] for r in rows if r['clock_review']=='YES' and r['year'] not in CLOCK_LIMITS.get(site,())]

def f4_note(site,year):
    notes=[t for y0,y1,t in F4.get(site,()) if y0<=year<=y1]
    return '; '.join(notes)+' (kept as measured, decision F4)' if notes else 'none identified (Stage06C humidity_by_year)'

def changed_vs_06a(old,sites):
    """Stage06A summary 'sites' -> {site: {year: [variables whose data hash differs, or NOT_IN_06A]}} for the files built here."""
    out={}
    for site,e in sites.items():
        for name,x in e['files'].items():
            y=int(name[-7:-3]);o=old.get(site,{}).get('files',{}).get(FILE_06A.format(site,y))
            d=['NOT_IN_06A'] if o is None else [v for v,h in sorted(x['data_sha256_by_variable'].items()) if o['data_sha256_by_variable'][v]!=h]
            if d:out.setdefault(site,{})[str(y)]=d
    return out

def digest(sites,key):
    xs=sorted(n+':'+(x['file_sha256'] if key is None else x['data_sha256_by_variable'][key]) for e in sites.values() for n,x in e['files'].items())
    return hashlib.sha256('\n'.join(xs).encode()).hexdigest()

def run(a):
    write=a.out is not None
    if write:
        if not a.ack:raise ValueError('--write needs --ack-utc-plus9-cyclic-shift')
        if a.out.exists() or a.out.is_symlink() or not a.out.parent.is_dir() or a.out.parent.is_symlink():raise ValueError('fresh --out required')
        if a.table_dir.resolve() in (a.out.resolve(),*a.out.resolve().parents):raise ValueError('--out inside the source directory')
        a.out.mkdir()
    a.cb_dir=a.table_dir;a.years={**YEARS,**a.years}   # Stage06A build_site reads a.cb_dir and a.years
    report={'stage':'06F','status':'APPROVED_20261105_UTC_NOLEAP_DATM_NOT_ACTIVATED' if write else 'CHECK_ONLY_NOTHING_WRITTEN',
        'input':'Stage06E final pre-forcing tables (Stage05CB plus approved E1A/E1B/E2, 2026-11-05)','table_gzip_sha256':TABLES,'sites':{}}
    allrows=[]
    for site in a.sites:
        print('STAGE06F',site,flush=True)
        utc,rows,site_med,(y0,y1,lat,lon,zbot,formula)=a6.build_site(a,site)
        odd=unaccepted_clock(site,rows)
        if odd:raise ValueError('%s: FSDS centroid >15 min off UTC in %s, not an accepted clock limit'%(site,odd))
        entry={'years':[y0,y1],'period_note':PERIOD.get(site,'full approved table range'),'lat':lat,'lon':lon,'zbot_m':zbot,'es_formula':formula,
               'clock':CLOCK.get(site,'BIF UTC_OFFSET 9'),'fsds_centroid_minus_toa_min_site_median':round(site_med,1),
               'accepted_clock_limit_years':[r['year'] for r in rows if r['clock_review']=='YES'],
               'humidity_screen_after_E1':{k[9:]:sum(r[k] for r in rows) for k in rows[0] if k.startswith('humidity_')},
               'humidity_drift_F4':{str(r['year']):f4_note(site,r['year']) for r in rows if any(y0<=r['year']<=y1 for y0,y1,_ in F4.get(site,()))},'files':{}}
        if write:
            d=a.out/site;d.mkdir()
            for (y,spd,f,tail),row in zip(utc,rows):
                attrs={'title':'JapanFlux MultiSite 11 UTC NOLEAP DATM forcing from the QC rules approved by 2026-11-05 (not activated)',
                    'site':site,'forcing_year':y,'forcing_period':'%d-%d; %s'%(y0,y1,entry['period_note']),
                    'source_tables':','.join('%s sha256 %s'%(k,TABLES[k]) for k in a6.SITES[site][0]),'qc_approval':QC_APPROVAL,
                    'qc_open_items_at_build':OPEN.get(site,'')+OPEN_ALL,
                    'science_status':'QC_APPROVED_RULES_20261105; DATM_NOT_ACTIVATED','model_submission_authorised':'FALSE',
                    'time_reference':'UTC interval centre; source TIMESTAMP_START on UTC+9 moved -9 h by whole slots',
                    'clock_basis':entry['clock'],
                    'clock_check':'FSDS centroid minus TOA %.1f min on the UTC axis; %s'%(row['fsds_centroid_minus_toa_min_median'],
                        'sub-slot offset accepted as a known limit (user, 2026-11-05)' if row['clock_review']=='YES' else 'within 15 min'),
                    'time_boundary_policy':'last %d slots from %s'%(tail['tail_slots'],tail['tail_source']),
                    'calendar_policy':'noleap; local Feb 29 rows removed before the UTC shift',
                    'humidity':'QBOT=0.622e/(p-0.378e), e=es(TA)-VPD, es=%s; DATM caps QBOT at its own qsat'%formula,
                    'humidity_qc':'E1A/E1B outliers replaced by the reference RH at the tower TA (approved); screen after E1 this year: '
                        'Td>=28C %d, saturated at TA>=28C %d, RH<5%% %d (each remaining cell is explained in Stage06H)'%(
                        row['humidity_Td_ge_28C'],row['humidity_saturated_TA_ge_28C'],row['humidity_RH_lt_5pct']),
                    'humidity_drift':f4_note(site,y),
                    'radiation_precipitation':'FSDS=max(SW_IN_F,0); FLDS=LW_IN_F; PRECTmms=P_F/%d s'%(86400//spd),
                    'zbot_evidence':'TA_F sensor height %.1f m (BIF/BADM)'%zbot,'low_tower_coverage':row['low_tower_coverage']}
                p=d/FILE.format(site,y);h=a6.write_nc(p,site,y,spd,f,lat,lon,zbot,attrs)
                row['file']=p.name;row['file_sha256']=br.sha(p);row['data_sha256_by_variable']=h
                entry['files'][p.name]={'file_sha256':row['file_sha256'],'data_sha256_by_variable':h}
            with (d/'stream_plan_NOT_ACTIVATED.json').open('x',encoding='utf-8') as f:json.dump(a6.stream_plan(site,y0,y1,utc),f,indent=1);f.write('\n')
        report['sites'][site]=entry;allrows.extend(rows)
        print(json.dumps({'site':site,'years':[y0,y1],'files':len(rows),'fsds_offset_min':round(site_med,1),'accepted_clock_limit_years':entry['accepted_clock_limit_years'],
            'humidity_screen_after_E1':entry['humidity_screen_after_E1'],'low_coverage_years':[r['year'] for r in rows if r['low_tower_coverage']!='NO']}),flush=True)
    view={s:{**{k:v for k,v in e.items() if k!='files'},'files':{n:{k:v for k,v in x['data_sha256_by_variable'].items() if k!='QBOT'} for n,x in e['files'].items()}}
          for s,e in report['sites'].items()}
    report['fingerprint_without_QBOT_and_file_bytes']=br.fingerprint(view)
    if write:
        report['QBOT_digest']=digest(report['sites'],'QBOT');report['file_bytes_digest']=digest(report['sites'],None)
        if a.compare_06a:
            report['changed_vs_06A']=changed_vs_06a(json.loads(a.compare_06a.read_text(encoding='utf-8'))['sites'],report['sites'])
            report['changed_vs_06A_sha256']=hashlib.sha256(json.dumps(report['changed_vs_06A'],sort_keys=True).encode()).hexdigest()
    report['site_year_rows']=[{k:v for k,v in r.items() if k!='data_sha256_by_variable'} for r in allrows]
    if write:
        cols=[k for k in allrows[0] if k!='data_sha256_by_variable']
        with (a.out/'site_year_summary_APPROVED_20261105.tsv').open('x',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,cols,delimiter='\t',extrasaction='ignore');w.writeheader();w.writerows(allrows)
        with (a.out/'summary_APPROVED_20261105.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=1,sort_keys=True);f.write('\n')
    print('STAGE06F COMPLETE;',('DATM FILES WRITTEN TO '+str(a.out)) if write else 'CHECK ONLY, NOTHING WRITTEN','; NOT ACTIVATED; NO CASE, NO SLURM')
    print(json.dumps({'fingerprint':report['fingerprint_without_QBOT_and_file_bytes'],'files':len(allrows),**({k:report[k] for k in
        ('QBOT_digest','file_bytes_digest','changed_vs_06A_sha256','changed_vs_06A') if k in report})}))

def selftest():
    a6.selftest()
    assert a6.TABLES is TABLES and a6.TABLE_NAME==TABLE_NAME and a6.FILE==FILE and FILE_06A!=FILE
    assert sum(YEARS.get(s,v[1:3])[1]-YEARS.get(s,v[1:3])[0]+1 for s,v in a6.SITES.items())==217
    assert unaccepted_clock('JP-Tef',[{'year':2006,'clock_review':'YES'},{'year':2007,'clock_review':'YES'},{'year':2008,'clock_review':'NO'}])==[2007]
    assert unaccepted_clock('JP-Tgf',[{'year':2016,'clock_review':'YES'}])==[2016]
    assert '+5.5 to +8.7' in f4_note('JP-Api',2010) and f4_note('JP-Api',2018).startswith('none') and '688' in f4_note('JP-Tef',2016)
    sites={'JP-X':{'files':{FILE.format('JP-X',2001):{'data_sha256_by_variable':{'QBOT':'a','TBOT':'b'}},FILE.format('JP-X',2002):{'data_sha256_by_variable':{'QBOT':'a'}}}}}
    old={'JP-X':{'files':{FILE_06A.format('JP-X',2001):{'data_sha256_by_variable':{'QBOT':'c','TBOT':'b'}}}}}
    assert changed_vs_06a(old,sites)=={'JP-X':{'2001':['QBOT'],'2002':['NOT_IN_06A']}}
    print('STAGE06F SELF-TEST PASS: 06A self-test, table/file repointing, E3 file count 217, clock-limit guard, F4 notes, 06A diff; NO FILES')

def main():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--self-test',action='store_true');p.add_argument('--table-dir',type=Path,help='Stage06E output');p.add_argument('--out',type=Path)
    p.add_argument('--write',action='store_true');p.add_argument('--ack-utc-plus9-cyclic-shift',dest='ack',action='store_true')
    p.add_argument('--compare-06a',type=Path,help='Stage06A summary_CANDIDATE.json')
    p.add_argument('--sites',default=','.join(a6.SITES));p.add_argument('--years',action='append',default=[],help='SITE=FIRST-LAST override')
    a=p.parse_args()
    if a.self_test:selftest();return
    if a.table_dir is None or a.write!=(a.out is not None):p.error('--table-dir required; --write and --out go together')
    if a.compare_06a and not a.write:p.error('--compare-06a needs --write')
    a.sites=a.sites.split(',')
    if not set(a.sites)<=set(a6.SITES):p.error('unknown site')
    a.years={s:tuple(int(x) for x in r.split('-')) for s,r in (y.split('=') for y in a.years)}
    run(a)
if __name__=='__main__':main()

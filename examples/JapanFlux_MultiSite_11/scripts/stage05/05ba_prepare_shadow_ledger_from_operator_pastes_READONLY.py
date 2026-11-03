#!/usr/bin/env python3
"""Prepare a new *unapproved shadow ledger* from operator-pasted evidence.

Reads only local text. Writes new derived TSV/JSON in a fresh output directory.
Never reads or writes a production forcing file or authorizes repair values.
"""
import argparse,csv,hashlib,json,math,statistics
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path

STEP=timedelta(minutes=30)
SITES=Counter({'JP-Fjy':6,'JP-Khw':11,'JP-Yms':10,'JP-Tef':4,'JP-Tmd':14})
VARS=Counter({'PA':27,'TA':6,'LW_IN':12})
WINDOW_SHA='89e9b41055b782da97ebcbda9c6ddb55a3c6bf6426ad40fdd2bb865e98a687d9'
AW_SHA='6b717bdf8232388f59af849da01dbc316a8166e0a07305d3d2567d2d7d55e6ad'
REPORTED={'group_source_grid_residuals_HOLD.tsv':'ed5597796982bafd86a253f670870e90ebabb67212706b0f185d6ee147e7cd61',
          'candidate_hourly_context_HOLD.tsv':'e7b3ca99f28e27e7b0a508697c607241767d238548dc3405f9231620737be785',
          'background_pairs_READONLY.tsv':'6ff971ca857be54cc9eff1253087cc3179b19a53f2215672bced6e865a9b199b'}
def stamp(s):return datetime.strptime(s,'%Y%m%d%H%M')
def num(x):
    f=float(x)
    if not math.isfinite(f) or f<=-9990:raise ValueError('invalid number')
    return f
def compare(x,lo,hi):
    if lo>hi:raise ValueError('invalid envelope')
    return 'BELOW' if x<lo else 'ABOVE' if x>hi else 'INSIDE'
def hashbytes(b):return hashlib.sha256(b).hexdigest()
def selftest():
    assert compare(1,2,3)=='BELOW' and compare(2,2,3)=='INSIDE' and compare(4,2,3)=='ABOVE'
    assert stamp('202212312330')+STEP==stamp('202301010000')
    assert hashbytes(b'abc')=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
    print('STAGE05BA SELF-TEST PASS; SHADOW ONLY; ZERO APPROVALS')
def prepare(a):
    paths=[a.windows_paste,a.aw_paste,a.az_paste];data=[p.read_bytes() for p in paths];texts=[b.decode('utf8') for b in data]
    w,aw,az=texts
    if 'INPUT_SHA256 '+WINDOW_SHA not in w or 'FULL_WINDOWS 45 UNIQUE_ROWS 1677' not in w or 'STAGE05AW_SHA256 '+AW_SHA not in aw:
        raise ValueError('Operator-reported window/AW source identity or coverage missing')
    for filename,sha in REPORTED.items():
        if sha not in az or ('/'+filename) not in az:raise ValueError('Operator-reported AZ file identity missing: '+filename)
    source={}; flags=set()
    for line in w.splitlines():
        if not line.startswith('JP-'):continue
        p=line.split()
        if len(p)!=16 or p[-1] not in ('True','False'):raise ValueError('malformed window row')
        k=(p[0],p[1],stamp(p[2]))
        if k in source:raise ValueError('duplicate window point')
        source[k]={'f':num(p[3]),'qc':p[4],'era':num(p[5]),'flag':p[-1]=='True','tokens':p}
        if p[-1]=='True':flags.add(k)
    if len(source)!=1677 or len(flags)!=45 or Counter(x[0] for x in flags)!=SITES or Counter(x[1] for x in flags)!=VARS or len({(x[0],x[2]) for x in flags})!=35:
        raise ValueError('window scope mismatch')
    records={}
    for line in aw.splitlines():
        if not line.startswith('JP-'):continue
        p=line.split()
        if len(p) not in (11,12):raise ValueError('malformed AW record')
        site,native,var,orig=p[:4];utc,clock,lo,hi,tier,hold=p[-6:];unit=' '.join(p[4:-6]);k=(site,var,stamp(native))
        if k in records or hold!='HOLD_NO_APPROVED_30MIN_REPLACEMENT' or unit!={'PA':'kPa','TA':'deg C','LW_IN':'W m-2'}.get(var):raise ValueError('AW duplicate/HOLD/unit')
        expected_clock='OPERATOR_JST_PLUS9_DIAGNOSTIC_README_SOLAR_CONFLICT' if site in ('JP-Tef','JP-Tmd') else 'ORIGINAL_SOURCE_README_JST_PLUS9_VERIFIED'
        if clock!=expected_clock or stamp(native)-stamp(utc)!=timedelta(hours=9):raise ValueError('clock provenance')
        records[k]={'orig':num(orig),'lo':num(lo),'hi':num(hi),'unit':unit,'clock':clock,'tier':tier}
    if set(records)!=flags:raise ValueError('AW flags differ from windows')
    sections={};section=None
    for line in az.splitlines():
        if line.startswith('FILE '):
            name=line.split()[-1].rsplit('/',1)[-1]
            section=name if name in REPORTED else None
            continue
        if section and line.startswith('JP-'):sections.setdefault(section,[]).append(line.split())
    if [len(sections.get(x,[])) for x in REPORTED] != [38,99,1936]:raise ValueError('incomplete AZ pasted output')
    candidates={}
    for p in sections['candidate_hourly_context_HOLD.tsv']:
        if p[3]!='540':continue
        k=(p[0],p[1],stamp(p[2]))
        if k in candidates or len(p)<12:raise ValueError('duplicate/malformed AZ candidate')
        candidates[k]={'value':num(p[5]),'grid':num(p[6]),'difference':float(p[7]),'excess':float(p[8]),
                       'lo':num(p[9]),'hi':num(p[10])}
    if set(candidates)!=flags:raise ValueError('AZ candidates and AW flags differ')
    bg=defaultdict(list);bg_quality=Counter()
    for p in sections['background_pairs_READONLY.tsv']:
        if len(p)<12:raise ValueError('malformed AZ background')
        if p[3]!='540':continue
        site,var,group=p[:3];quality=int(p[7]);f=num(p[6]);grid=num(p[8]);delta=float(p[9])
        if abs((f-grid)-delta)>1e-6:raise ValueError('background arithmetic mismatch')
        bg_quality[quality]+=1
        bg[(site,var,stamp(group),quality)].append(delta)
    groups=[]
    for site,var in sorted({k[:2] for k in flags}):
        for k in sorted(k for k in flags if k[:2]==(site,var)):
            if not groups or groups[-1][0]!=(site,var) or k[2]-groups[-1][1][-1][2]!=STEP:groups.append(((site,var),[k]))
            else:groups[-1][1].append(k)
    if len(groups)!=17:raise ValueError('group count')
    result=[];summary=[]
    for (site,var),keys in groups:
        left=source[(site,var,keys[0][2]-STEP)];right=source[(site,var,keys[-1][2]+STEP)]
        if any(p['flag'] or p['qc']!='2' or abs(p['f']-p['era'])>1e-6 for p in (left,right)):
            raise ValueError('invalid source shadow anchor')
        baseline=bg[(site,var,keys[0][2],2)]
        if not baseline:raise ValueError('missing QC2 paired background')
        median=statistics.median(baseline);n_out=0
        for i,k in enumerate(keys,1):
            p=source[k];r=records[k];c=candidates[k]
            if not p['flag'] or p['qc']!='2' or abs(p['f']-p['era'])>1e-6 or abs(p['f']-r['orig'])>1e-6:
                raise ValueError('original flagged value mismatch')
            expected=left['f']+(right['f']-left['f'])*i/(len(keys)+1)
            if abs(expected-c['value'])>1e-6 or abs(r['lo']-c['lo'])>1e-6 or abs(r['hi']-c['hi'])>1e-6:
                raise ValueError('shadow value or reference bounds mismatch')
            if abs((expected-c['grid'])-c['difference'])>1e-6 or abs((c['difference']-median)-c['excess'])>1e-6:
                raise ValueError('AZ grid/background arithmetic mismatch')
            outside=c['difference']<min(baseline) or c['difference']>max(baseline)
            n_out+=outside
            result.append({'site':site,'variable':var,'native_start':k[2].strftime('%Y%m%d%H%M'),
                'unit':r['unit'],'original_F':p['f'],'shadow_value_NOT_APPROVED':expected,
                'shadow_method':'FULL_FLAG_GROUP_SAME_RELEASE_QC2_BRIDGE',
                'left_QC2_F':left['f'],'right_QC2_F':right['f'],
                'grid_context_UTC9_hypothesis':c['grid'],'shadow_minus_grid':c['difference'],
                'background_QC2_count':len(baseline),'background_QC2_median':median,
                'shadow_grid_delta_outside_observed_QC2_background_range':outside,
                'prior_hourly_envelope_position':compare(expected,r['lo'],r['hi']),
                'clock_provenance':r['clock'],'source_quality':'QC2_ERA_DERIVED_NOT_QC0',
                'science_status':'HOLD_NO_APPROVED_REPLACEMENT','production_forcing_modified':False})
        summary.append({'site':site,'variable':var,'native_start':keys[0][2].strftime('%Y%m%d%H%M'),
            'flagged_fields':len(keys),'qc2_background_count':len(baseline),'qc2_background_median':median,
            'shadow_delta_outside_background_range_fields':n_out,
            'review_route':'CLOCK_CONFLICT_AND_MANUAL_SCIENCE_REVIEW' if site in ('JP-Tef','JP-Tmd') else 'MANUAL_SCIENCE_REVIEW_NO_INDEPENDENT_QC0',
            'science_status':'HOLD_NO_APPROVED_REPLACEMENT'})
    if (len(result)!=45 or a.out_dir.parent.name!='japanflux_stage05ba' or
        a.out_dir.parent.is_symlink() or a.out_dir.exists() or a.out_dir.is_symlink()):
        raise ValueError('Output must be a fresh child of a japanflux_stage05ba directory')
    a.out_dir.mkdir(parents=True)
    shadow_lookup={(r['site'],r['variable'],stamp(r['native_start'])):r['shadow_value_NOT_APPROVED'] for r in result}
    preview=[]
    for k,p in sorted(source.items()):
        t=p['tokens'];isflag=k in shadow_lookup
        preview.append({'site':t[0],'variable':t[1],'native':t[2],
            'original_F':t[3],'shadow_F_NOT_APPROVED':shadow_lookup[k] if isflag else t[3],
            'original_F_QC':t[4],'original_same_release_ERA':t[5],
            'original_raw_sensor':t[6],'original_F_MDS':t[7],'original_F_MDS_QC':t[8],
            'original_co_PA_F':t[9],'original_co_PA_F_QC':t[10],
            'original_co_TA_F':t[11],'original_co_TA_F_QC':t[12],
            'original_co_LW_IN_F':t[13],'original_co_LW_IN_F_QC':t[14],
            'flagged':isflag,'science_status':'HOLD_NO_APPROVED_REPLACEMENT'})
    if len(preview)!=1677 or sum(r['flagged'] for r in preview)!=45 or any(
        str(r['original_F'])!=str(r['shadow_F_NOT_APPROVED']) for r in preview if not r['flagged']):
        raise ValueError('preview non-event identity failed')
    for name,rows in [('shadow_45_NOT_APPROVED.tsv',result),('group_review_HOLD.tsv',summary),
                      ('shadow_window_preview_NOT_FORCING.tsv',preview)]:
        with (a.out_dir/name).open('x',encoding='utf8',newline='') as f:
            out=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t');out.writeheader();out.writerows(rows)
    meta={'status':'SHADOW_ONLY_ALL_45_HOLD','approved_replacements':0,'source_field_count':45,
          'groups':17,'background_QC_counts_at_UTC9':dict(bg_quality),
          'window_paste_sha256':hashbytes(data[0]),'AW_paste_sha256':hashbytes(data[1]),'AZ_paste_sha256':hashbytes(data[2]),
          'remote_file_hashes_operator_reported_not_independently_verified':{**REPORTED,'AW':AW_SHA,'WINDOWS':WINDOW_SHA},
          'AZ_summary_json_not_present_in_paste':True,
          'reference_limits':'same-source QC2 background; hourly grid context, NOT measured half-hour truth',
          'clock_warning':'Tef/Tmd UTC+9 is hypothesis, and mean-solar scenario mislabeled generic in original AZ output',
          'window_preview_rows':1677,'window_preview_flagged_fields':45,
          'unflagged_preview_F_textually_identical':True,
          'preview_is_not_a_complete_forcing_or_source_release':True,
          'preview_co_fields_remain_original':True,
          'production_forcing_source_zip_modified':False}
    with (a.out_dir/'summary_HOLD.json').open('x',encoding='utf8') as f:json.dump(meta,f,indent=2);f.write('\n')
    print('STAGE05BA 45 SHADOW RECORDS PREPARED; ALL HOLD; ZERO APPROVED')
    print('BACKGROUND_QC_COUNTS_UTC9',dict(bg_quality),'GROUPS',len(groups))
    print('OUTPUT',a.out_dir)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true')
    p.add_argument('--windows-paste',type=Path);p.add_argument('--aw-paste',type=Path);p.add_argument('--az-paste',type=Path);p.add_argument('--out-dir',type=Path)
    a=p.parse_args()
    if a.self_test:selftest();return
    if any(getattr(a,k) is None for k in ('windows_paste','aw_paste','az_paste','out_dir')):p.error('all pasted inputs and fresh output required')
    prepare(a)
if __name__=='__main__':main()

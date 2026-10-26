#!/usr/bin/env python3
"""Verify US-Me2 4-6 clocks and map the four legacy holds, without forcing edits.

Site BADM supplement: AMF_US-Me2_BIF_20260527.xlsx, AMF-BIF!A767:E767,
GROUP_ID=12976, UTC_OFFSET=-8. This BIF is separate from the original ZIP.
Use local standard time throughout the year, UTC=LST+8h. Never use DST.
--check writes nothing; --run writes only a new isolated clock report.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
from uuid import uuid4
import zipfile

ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03')
RELEASE='AMF_US-Me2_FLUXNET_FULLSET_2002-2022_4-6'
RAW=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE/US-Me2/forcing/raw')/RELEASE
S07=ROOT/'qcv5_native_trial_20261022T024559Z_36c46e58'
BIF={'filename':'AMF_US-Me2_BIF_20260527.xlsx',
     'sha256':'adcd983cca9c9c8392e0581a43414c8c4382c10ffaba431022a7656c59ba4cd4',
     'sheet':'AMF-BIF','range':'A767:E767','SITE_ID':'US-Me2',
     'GROUP_ID':12976,'VARIABLE_GROUP':'GRP_UTC_OFFSET','VARIABLE':'UTC_OFFSET','DATAVALUE':'-8',
     'date_scope':'No date fields or alternative UTC_OFFSET records in this site BIF.',
     'relationship':'Separate site BADM supplement, not a member of the 4-6 release ZIP.'}
SOURCES={
 'primary':{'name':'AMF_US-Me2_FLUXNET_FULLSET_HH_2002-2022_4-6.csv',
  'sha256':'5b29b04da37960a1640c19b75fc2a8ffbffd703ada89ba6c36689d86f834ae3e',
  'bytes':576695188,'first_year':2002,'last_year':2022,'rows':368160,'leap_rows':240},
 'era':{'name':'AMF_US-Me2_FLUXNET_ERA5_HH_1981-2023_4-6.csv',
  'sha256':'ad0ce6a1d934bb965d939375c1c8588ed643f3513c3ac7e31afed6ca993d3115',
  'bytes':51455118,'first_year':1981,'last_year':2023,'rows':753840,'leap_rows':480}}
DOCS=[
 'https://ameriflux.lbl.gov/data/tips-ameriflux-flux-met-data-processing-pipeline/',
 'https://fluxnet.org/data/fluxnet2015-dataset/',
 'https://fluxnet.org/data/fluxnet2015-dataset/fullset-data-product/']


def sha_stream(stream):
    h=hashlib.sha256()
    for block in iter(lambda:stream.read(1<<20),b''):h.update(block)
    return h.hexdigest()


def sha(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file():raise ValueError('Missing or symlink file: '+str(path))
    with path.open('rb') as stream:return sha_stream(stream)


def utc_interval(start,end):
    if end-start!=timedelta(minutes=30):raise ValueError('Expected 30 minute averaging interval')
    # UTC_OFFSET means local minus UTC, hence subtract the negative offset.
    a=start-timedelta(hours=-8);b=end-timedelta(hours=-8)
    return a,b,a+(b-a)/2


def audit_times(frame,first,last):
    import pandas as pd
    starts=pd.to_datetime(frame['TIMESTAMP_START'],format='%Y%m%d%H%M',errors='raise')
    ends=pd.to_datetime(frame['TIMESTAMP_END'],format='%Y%m%d%H%M',errors='raise')
    expected=pd.date_range(str(first)+'-01-01',str(last+1)+'-01-01',freq='30min')[:-1]
    if len(starts)!=len(expected) or not (starts.to_numpy()==expected.to_numpy()).all():
        raise ValueError('Incomplete, duplicate, reversed, off-grid or unexpected Gregorian timestamp axis')
    if not ((ends-starts).dt.total_seconds()==1800).all():raise ValueError('Wrong interval end')
    return {'rows':len(starts),'first_start':str(starts.iloc[0]),'last_end':str(ends.iloc[-1]),
            'leap_day_rows':int(((starts.dt.month==2)&(starts.dt.day==29)).sum()),
            'invalid_intervals':0,'cadence_discontinuities':0},starts,ends


def read_source(info,raw,archive):
    import pandas as pd
    if archive:
        with archive.open(info['name']) as stream:actual=sha_stream(stream)
        size=archive.getinfo(info['name']).file_size
        if actual!=info['sha256'] or size!=info['bytes']:raise ValueError('ZIP source hash/size mismatch')
        with archive.open(info['name']) as stream:
            frame=pd.read_csv(stream,usecols=['TIMESTAMP_START','TIMESTAMP_END'],dtype=str)
    else:
        path=raw/info['name'];before=path.stat()
        actual=sha(path)
        if actual!=info['sha256'] or before.st_size!=info['bytes']:raise ValueError('Source hash/size mismatch: '+str(path))
        frame=pd.read_csv(path,usecols=['TIMESTAMP_START','TIMESTAMP_END'],dtype=str)
        after=path.stat()
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('Source changed during check')
    rec,starts,ends=audit_times(frame,info['first_year'],info['last_year'])
    if rec['rows']!=info['rows'] or rec['leap_day_rows']!=info['leap_rows']:raise ValueError('Pinned row counts changed')
    rec.update(name=info['name'],sha256=actual,bytes=size if archive else before.st_size)
    return rec,starts,ends


def stage07_check(folder,raw):
    if not (folder/'INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP').is_file():raise ValueError('Original Stage07 hold marker missing')
    manifest=folder/'exact_input_manifest.json'
    m=json.loads(manifest.read_text())
    items=[r for r in m['sites'] if r['site']=='US-Me2']
    if len(items)!=1 or items[0]['release']!=RELEASE or int(items[0]['native_minutes'])!=30:
        raise ValueError('Stage07 US-Me2 release/interval differs')
    for kind,info in SOURCES.items():
        path=(raw/info['name']).resolve()
        if Path(items[0][kind]).resolve()!=path or m['input_sha256'].get(str(path))!=info['sha256']:
            raise ValueError('Stage07 source path/hash differs: '+kind)
    return {'path':str(manifest),'sha256':sha(manifest)}


def legacy_events(folder,starts,ends):
    import pandas as pd
    receipt_path=folder/'scientific_hold_receipt.json'
    receipt=json.loads(receipt_path.read_text())
    name='1924_source_event_science_review.csv';path=folder/name
    if receipt['events']!=1924 or receipt['output_SHA256'].get(name)!=sha(path):
        raise ValueError('Stage11a event receipt mismatch')
    table=pd.read_csv(path,dtype=str,keep_default_na=False)
    if len(table)!=1924 or table.duplicated(['site','source_csv_row','time']).any():raise ValueError('Legacy event scope changed')
    selected=table[table.site=='US-Me2']
    if len(selected)!=4 or not selected.review_route.eq('CLOCK_METADATA_HOLD').all():
        raise ValueError('Expected exactly four original US-Me2 clock holds')
    result=[]
    for row in selected.to_dict('records'):
        pos=int(row['source_csv_row'])-2
        if not 0<=pos<len(starts) or pd.Timestamp(row['time'])!=starts.iloc[pos]:
            raise ValueError('Original source row/time identity differs')
        a,b,mid=utc_interval(starts.iloc[pos].to_pydatetime(),ends.iloc[pos].to_pydatetime())
        result.append({'site':'US-Me2','source_csv_row':int(row['source_csv_row']),
            'local_start':str(starts.iloc[pos]),'local_end':str(ends.iloc[pos]),
            'utc_start':a.isoformat()+'Z','utc_end':b.isoformat()+'Z','utc_midpoint':mid.isoformat()+'Z',
            'previous_route':row['review_route'],
            'next_route':'CLOCK_DOCUMENTED_HUMIDITY_SCIENCE_REVIEW_PENDING',
            'humidity_repair_approved':False})
    return result,{'receipt':str(receipt_path),'receipt_sha256':sha(receipt_path),'event_csv_sha256':sha(path)}


def self_test():
    import pandas as pd
    # Test winter, summer, UTC year rollover, Gregorian leap-day before NOLEAP conversion.
    for text in ['2002-01-01T00:00','2020-07-01T12:00','2022-12-31T23:30','2020-02-29T23:30']:
        s=datetime.fromisoformat(text);e=s+timedelta(minutes=30);a,b,m=utc_interval(s,e)
        assert a-s==timedelta(hours=8) and b-a==timedelta(minutes=30) and m-a==timedelta(minutes=15)
    index=pd.date_range('2020-01-01','2021-01-01',freq='30min')[:-1]
    frame=pd.DataFrame({'TIMESTAMP_START':index.strftime('%Y%m%d%H%M'),
                        'TIMESTAMP_END':(index+pd.Timedelta(minutes=30)).strftime('%Y%m%d%H%M')})
    rec,_,_=audit_times(frame,2020,2020);assert rec['leap_day_rows']==48
    for bad in [frame.drop(3),frame.iloc[::-1],frame.assign(TIMESTAMP_END=frame.TIMESTAMP_START)]:
        try:audit_times(bad,2020,2020)
        except ValueError:pass
        else:raise AssertionError('Corrupt axis accepted')
    print('ME2 CLOCK SELF-TEST PASS: fixed UTC+8 winter/summer, rollover, leap day, corrupt axes rejected')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    action=parser.add_mutually_exclusive_group(required=True)
    for flag in ['check','run','self-test']:action.add_argument('--'+flag,action='store_true')
    parser.add_argument('--raw-dir',type=Path,default=RAW)
    parser.add_argument('--source-zip',type=Path)
    parser.add_argument('--source-only',action='store_true',help='Check local release only; no cluster Stage07/four-event assertion')
    parser.add_argument('--stage07',type=Path,default=S07)
    parser.add_argument('--stage11a',type=Path)
    parser.add_argument('--report-root',type=Path,default=ROOT/'reports')
    args=parser.parse_args()
    if args.self_test:self_test();return
    if args.source_zip and not args.source_only:parser.error('--source-zip requires --source-only')
    inputs={};events=[];archive=None
    if not args.source_only:inputs['stage07']=stage07_check(args.stage07,args.raw_dir)
    try:
        if args.source_zip:archive=zipfile.ZipFile(args.source_zip)
        summaries={};primary=None
        for kind,info in SOURCES.items():
            rec,starts,ends=read_source(info,args.raw_dir,archive)
            summaries[kind]=rec
            if kind=='primary':primary=(starts,ends)
            print('ME2 SOURCE',kind,json.dumps(rec),flush=True)
    finally:
        if archive:archive.close()
    if not args.source_only:
        choices=[args.stage11a] if args.stage11a else sorted(ROOT.glob('reports/stage11a_science_decision_matrix_*'))
        if len(choices)!=1:raise ValueError('Use --stage11a with the exact original sealed report; found '+str(len(choices)))
        events,inputs['stage11a']=legacy_events(choices[0],*primary)
        for row in events:print('ME2 LEGACY EVENT',json.dumps(row),flush=True)
    status='LOCAL_SOURCE_CLOCK_VERIFIED' if args.source_only else 'CLUSTER_SOURCE_AND_FOUR_CLOCK_HOLDS_VERIFIED'
    report={'status':status,'site':'US-Me2','release':RELEASE,'metadata_gate':'RESOLVED_WITH_SITE_BADM_SUPPLEMENT',
            'UTC_OFFSET_hours':-8,'time_basis':'LOCAL_STANDARD_TIME','daylight_saving':False,
            'utc_rule':'UTC=LST+8h; midpoint=(TIMESTAMP_START+TIMESTAMP_END)/2+8h',
            'bif_evidence':BIF,'official_conventions':DOCS,'sources':summaries,'legacy_events':events,
            'input_receipts':inputs,'humidity_repair_approvals':0,'post_v5_approval':False,'DATM_ready':False,
            'source_timestamps_modified':False,'model_jobs_submitted':0}
    if args.run:
        out=args.report_root/('stage14a_US_Me2_documented_clock_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8])
        out.mkdir(parents=True,exist_ok=False)
        (out/'clock_verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print('ME2 CLOCK REPORT',out,flush=True)
    print('ME2 CLOCK SUMMARY',status,'UTC_OFFSET=-8 DST=FALSE legacy_events='+str(len(events)),
          'humidity_repairs=0 DATM=FALSE jobs=0',flush=True)


if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError,TypeError,zipfile.BadZipFile) as exc:
        print('ME2 CLOCK STOP:',str(exc),file=sys.stderr);sys.exit(2)

#!/usr/bin/env python3
"""Stage65 — read-only BASE/native-temperature evidence inventory for Batch01.

Targets 53 QC0->QC1 P1 boundaries and 7 same-QC0 P1 events from Stage64.
Discovers per-site BASE-BADM ZIP archives, optionally looks for BASE_HH CSV
inside ZIP without extracting. Saves ONLY a new, small timestamped report.
No source data, forcing, CIME, DATM, FATES, surface, or Slurm modifications.

TIME WARNING: Raw BASE TIMESTAMP_START and processed forcing time have not
been independently cross-validated; exact-time matches are NOT approvals.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

EXP=Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10')
SITES=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
ROW_FIELDS=[
    'site','episode_id','timestamp','QC_direction','review_bucket',
    'candidate_step_C','post_QC_run_points_in_context',
    'single_step_reversal_candidate','BASE_status','archive_path',
    'BASE_member','raw_time_alignment','raw_TA_columns',
    'BASE_TA_30min_before_JSON','BASE_TA_at_event_JSON',
    'BASE_TA_30min_after_JSON','BASE_TA_offsets_available',
    'review_decision','next_action'
]
EXPECTED={'0->1':53,'0->0':7}

def rows(path,needed):
    if not path.is_file():
        raise RuntimeError('Missing Stage64 report: '+str(path))
    with path.open(newline='',encoding='utf-8-sig') as stream:
        reader=csv.DictReader(stream)
        names=reader.fieldnames or []
        if len(names)!=len(set(names)) or not set(needed).issubset(names):
            raise RuntimeError('Unexpected Stage64 schema '+str(path)+' missing '+str(set(needed)-set(names)))
        return list(reader)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):
            h.update(block)
    return h.hexdigest()

def validate(stage64):
    receipt=json.loads((stage64/'manifest.json').read_text(encoding='utf-8'))
    if (receipt.get('stage'),receipt.get('P1_events'),receipt.get('science_approved'),
        receipt.get('auto_repair'))!=(64,96,False,False):
        raise RuntimeError('Stage64 manifest differs from approved audit evidence')
    original=rows(stage64/'all_96_transition_persistence.csv',
                  {'site','episode_id','timestamp','QC_direction','review_bucket',
                   'candidate_step_C','post_QC_run_points_in_context','single_step_reversal_candidate'})
    if len(original)!=96 or len({(r['site'],r['episode_id']) for r in original})!=96:
        raise RuntimeError('Stage64 expected 96 distinct P1 groups')
    selected=[r for r in original if r['QC_direction'] in EXPECTED]
    if Counter(r['QC_direction'] for r in selected)!=EXPECTED:
        raise RuntimeError('Expected exactly 53 QC0->QC1 and 7 QC0->QC0 episodes')
    if any((r['QC_direction']=='0->0') != (r['review_bucket']=='SAME_QC0_MEASURED')
           for r in selected):
        raise RuntimeError('Same-QC0 status / Stage64 category mismatch')
    return selected

def find_archives(exp,sites,site):
    # Restrict to exact site prefix. No file mutation or extraction.
    folders=[exp/'base_original_validation',sites/site/'forcing'/'packages']
    prefix=('AMF_'+site+'_BASE-').upper()
    choices=[]
    for folder in folders:
        if folder.is_dir():
            choices.extend(p for p in folder.glob('*.zip') if p.name.upper().startswith(prefix))
    return sorted(set(choices),key=str)

def choose_archive(paths):
    if not paths:
        return None,'BASE_ARCHIVE_NOT_FOUND'
    if len(paths)==1:
        return paths[0],'ONE_BASE_ARCHIVE'
    # Only select duplicates that are byte-for-byte identical; never guess
    # between distinct BASE packages or historical releases.
    values={sha(x) for x in paths}
    if len(values)!=1:
        return None,'MULTIPLE_DISTINCT_BASE_ARCHIVES_HOLD'
    return paths[0],'IDENTICAL_ARCHIVE_COPIES'

def evidence_from_zip(path,wanted):
    matches={}
    if path is None:
        return matches,'ARCHIVE_UNAVAILABLE','',''
    try:
        with zipfile.ZipFile(path) as archive:
            members=[m for m in archive.infolist() if m.filename.upper().endswith('.CSV')
                     and 'BASE_HH' in m.filename.upper() and not m.is_dir()]
            if not members:
                return matches,'BASE_HH_CSV_NOT_FOUND','',''
            if len(members)>1:
                return matches,'MULTIPLE_BASE_HH_FILES_HOLD','',''
            member=members[0]
            # Protect against accidental decompression of unexpectedly huge files.
            if member.file_size>2500000000:
                return matches,'BASE_HH_MEMBER_TOO_LARGE_HOLD',member.filename,''
            with archive.open(member,'r') as raw:
                with io.TextIOWrapper(raw,encoding='utf-8-sig',errors='replace',newline='') as txt:
                    header=None
                    for i,line in enumerate(txt):
                        if i>500:
                            break
                        names=next(csv.reader([line]))
                        if 'TIMESTAMP_START' in names:
                            header=names
                            break
                    if header is None:
                        return matches,'BASE_TIMESTAMP_HEADER_NOT_FOUND',member.filename,''
                    ta_cols=[name for name in header if name=='TA' or name.startswith('TA_')]
                    if not ta_cols:
                        return matches,'BASE_RAW_TA_COLUMNS_NOT_FOUND',member.filename,''
                    if len(ta_cols)>200:
                        return matches,'BASE_TA_COLUMN_AMBIGUITY_HOLD',member.filename,''
                    source=csv.DictReader(txt,fieldnames=header)
                    for row in source:
                        key=str(row.get('TIMESTAMP_START','')).strip().removesuffix('.0')
                        if key not in wanted:
                            continue
                        if key in matches:
                            raise RuntimeError('Duplicated BASE TIMESTAMP_START '+key+' in '+member.filename)
                        matches[key]={col:row.get(col,'') for col in ta_cols}
                    return matches,'BASE_HH_READABLE',member.filename,';'.join(ta_cols)
    except (OSError,zipfile.BadZipFile,UnicodeError,ValueError) as exc:
        return {},'BASE_ZIP_READ_ERROR_'+type(exc).__name__,'',''

def analyze(selected,exp,sites):
    grouped=defaultdict(list)
    for item in selected:
        grouped[item['site']].append(item)
    out=[]
    archives={}
    for site,episodes in sorted(grouped.items()):
        choices=find_archives(exp,sites,site)
        archive,status=choose_archive(choices)
        watch=set()
        for e in episodes:
            t=datetime.fromisoformat(e['timestamp'])
            for step in (-2,-1,0,1,2):
                watch.add((t+timedelta(minutes=30*step)).strftime('%Y%m%d%H%M'))
        matched,zstatus,member,ta_cols=evidence_from_zip(archive,watch)
        archives[site]={
            'available_ARCHIVE_paths':[str(p) for p in choices],
            'archive_selection_status':status,
            'member_status':zstatus,'BASE_HH_member':member,
            'BASE_TA_column_names':ta_cols,
            'exact_candidate_time_matches':len(matched),
            'archive_sha256':sha(archive) if archive and archive.is_file() else None
        }
        print(f"SITE {site:7s} target_events={len(episodes):2d} "
              f"archives={len(choices)} status={status} BASE={zstatus} "
              f"matched_context_stamps={len(matched)}",flush=True)
        for e in episodes:
            t=datetime.fromisoformat(e['timestamp'])
            def at(step):
                return matched.get((t+timedelta(minutes=30*step)).strftime('%Y%m%d%H%M'))
            prior=at(-1);now=at(0);after=at(1)
            n=sum(at(step) is not None for step in (-2,-1,0,1,2))
            present=(prior is not None and now is not None)
            record=dict(e)
            record.update({
                'BASE_status':zstatus if status in ('ONE_BASE_ARCHIVE','IDENTICAL_ARCHIVE_COPIES') else status,
                'archive_path':str(archive) if archive else '',
                'BASE_member':member,
                'raw_time_alignment':'EXACT_START_ONLY_NOT_VALIDATED' if n else 'NOT_VERIFIED',
                'raw_TA_columns':ta_cols,
                'BASE_TA_30min_before_JSON':json.dumps(prior,sort_keys=True) if prior is not None else '',
                'BASE_TA_at_event_JSON':json.dumps(now,sort_keys=True) if now is not None else '',
                'BASE_TA_30min_after_JSON':json.dumps(after,sort_keys=True) if after is not None else '',
                'BASE_TA_offsets_available':n,
                'review_decision':'EVIDENCE_AVAILABLE_NOT_SCIENCE_APPROVED' if present else 'SOURCE_EVIDENCE_HOLD',
                'next_action':'Confirm native clock and identify the actual measured TA sensor/height; compare before and after; never auto-overwrite QC0 or gapfills'
            })
            out.append(record)
    out.sort(key=lambda r:(r['QC_direction'],r['site'],r['timestamp']))
    return out,archives

def output_new(exp,stage64,selected,provenance):
    parent=exp/'reports'
    if not parent.is_dir():
        raise RuntimeError('Experiment reports directory missing')
    target=parent/('stage65_BASE_TA_source_evidence_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    target.mkdir(exist_ok=False)
    with (target/'targeted_60_temperature_events.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=ROW_FIELDS,extrasaction='ignore')
        writer.writeheader()
        writer.writerows(selected)
    for name,direction in [('53_QC0_to_QC1_events.csv','0->1'),
                           ('7_measured_QC0_to_QC0_events.csv','0->0')]:
        with (target/name).open('w',newline='',encoding='utf-8') as stream:
            writer=csv.DictWriter(stream,fieldnames=ROW_FIELDS,extrasaction='ignore')
            writer.writeheader()
            writer.writerows(e for e in selected if e['QC_direction']==direction)
    receipt={
        'stage':65,'purpose':'BASE_HH raw/native TA sensor evidence',
        'source_report_path':str(stage64),'stage64_manifest_sha256':sha(stage64/'manifest.json'),
        'source_report_sha256':sha(stage64/'all_96_transition_persistence.csv'),
        'events':len(selected),'science_approved':False,
        'clock_alignment_verified':False,'forcing_modified':False,'auto_repair':False,
        'archived_input_discovery':provenance,
        'warning':'BASE archive names, raw sensor channels and exact TIMESTAMP_START matching do not establish data identity or clock agreement.'
    }
    (target/'manifest.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print('REPORT:',target)
    print('Only NEW report files written. Source archives and forcing unchanged.')

def self_test():
    assert len(EXPECTED)==2 and sum(EXPECTED.values())==60
    with __import__('tempfile').TemporaryDirectory(prefix='stage65_test_') as d:
        base=Path(d)
        z=base/'AMF_US-Bar_BASE-BADM_demo.zip'
        with zipfile.ZipFile(z,'w',compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('AMF_US-Bar_BASE_HH_demo.csv',
                             'intro\nTIMESTAMP_START,TIMESTAMP_END,TA_1_1_1,TA_1_1_1_QC\n'
                             '202001010000,202001010030,10,0\n'
                             '202001010030,202001010100,11,0\n')
        out,status,name,cols=evidence_from_zip(z,{'202001010000','202001010030'})
        assert status=='BASE_HH_READABLE' and len(out)==2
        assert out['202001010000']['TA_1_1_1']=='10'
        assert 'TA_1_1_1_QC' in cols
    print('SELF-TEST PASS: zipped BASE_HH streaming, sensor columns and timestamps')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--self-test',action='store_true')
    group.add_argument('--check',action='store_true')
    group.add_argument('--audit',action='store_true')
    p.add_argument('--stage64-dir',type=Path)
    p.add_argument('--experiment-root',type=Path,default=EXP)
    p.add_argument('--sites-root',type=Path,default=SITES)
    a=p.parse_args()
    if a.self_test:
        self_test();return
    if a.stage64_dir is None:
        p.error('--stage64-dir is required for --check or --audit')
    stage64=a.stage64_dir.resolve(strict=True)
    experiment=a.experiment_root.resolve(strict=True)
    sites=a.sites_root.resolve(strict=True)
    selection=validate(stage64)
    print('STAGE65 BASE/native TA inventory | source READ ONLY')
    print('P1 targeted groups:',len(selection),'QC0->QC1=',53,'QC0->QC0=',7)
    if a.check:
        for site in sorted({e['site'] for e in selection}):
            paths=find_archives(experiment,sites,site)
            print('SITE',site,'BASE candidate archives:',len(paths))
            for f in paths:
                print('  ',f)
        print('CHECK PASS: case census and archive discovery; no files written.')
        return
    result,provenance=analyze(selection,experiment,sites)
    output_new(experiment,stage64,result,provenance)

if __name__=='__main__':
    main()

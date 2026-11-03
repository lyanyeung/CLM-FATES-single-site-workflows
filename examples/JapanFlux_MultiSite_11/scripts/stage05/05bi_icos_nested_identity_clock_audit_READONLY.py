#!/usr/bin/env python3
"""Compare nested JPF source ZIPs to ICOS published archive SHA256s, read-only.

Only the original outer/nested ZIP and README are read. No source extraction,
forcing, CDS, PFT, model or scheduler modifications. All repair values HOLD.
"""
import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path, PurePosixPath

ROOT=Path('/iridisfs/scratch/ly3n24/CLM_FATES/sites/MY_EC_SITE')
README_SHA='17a886f56abc2673b43ad43ba17d95aacb7830b8475231a10b56c619bf5d4ac5'
SITES={
 'JP-Tef':{'name':'JPF_JP-Tef_FLUXNET_2001-2023_v1.3_r1.zip',
           'outer':'315c825b64669aa03daff1d969f58a0a1cf3b574c43400ea1f84588df7f6d684',
           'icos_archive':'537ea32af19f1880874893b4d529388c465331ccfc42dd5987341568a5427527',
           'archive_url':'https://meta.icos-cp.eu/objects/U36jKvGfGICHSJO01Sk4jEZT',
           'subset_url':'https://meta.icos-cp.eu/objects/5EPoidiNgWdizvMjVuk1G1vC'},
 'JP-Tmd':{'name':'JPF_JP-Tmd_FLUXNET_2005-2023_v1.3_r1.zip',
           'outer':'3ef287018725cb2b5b4c78130804febbe022dad66415807e70f628b756a13479',
           'icos_archive':'d28f9eec6e3226029852ba638cb7bbc3496d74880da8f3f29fec95b0ea3cb48f',
           'archive_url':'https://meta.icos-cp.eu/objects/0o-e7G4yJgKYUrpjjLe7w0lt',
           'subset_url':'https://meta.icos-cp.eu/objects/bnc9Cg8Jxf1opT9_Fq8boBvS'}}
MAX_INNER=512*1024*1024

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(2*1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def sha_bytes(data):return hashlib.sha256(data).hexdigest()
def clock_lines(text):
    lines=text.splitlines()
    return [{'line':i+1,'text':line.strip()} for i,line in enumerate(lines)
            if any(x in line.lower() for x in ('solar time','standard time','time zone','timezone','utc','dst'))]
def inspect(site,root):
    item=SITES[site];path=root/site/'forcing'/'packages'/item['name']
    if path.is_symlink() or not path.is_file() or digest(path)!=item['outer']:raise ValueError('outer ZIP SHA mismatch: '+site)
    with zipfile.ZipFile(path) as outer:
        found=[x for x in outer.infolist() if x.filename==item['name'] and not x.is_dir()]
        if len(found)!=1 or not 0<found[0].file_size<=MAX_INNER:raise ValueError('nested ZIP missing/duplicate/too large: '+site)
        h=hashlib.sha256();buf=io.BytesIO();count=0
        with outer.open(found[0]) as src:
            for block in iter(lambda:src.read(2*1024*1024),b''):
                count+=len(block)
                if count>MAX_INNER:raise ValueError('nested ZIP exceeds cap')
                h.update(block);buf.write(block)
        if count!=found[0].file_size:raise ValueError('nested size mismatch')
        inner_sha=h.hexdigest();buf.seek(0)
        with zipfile.ZipFile(buf) as inner:
            hits=[x for x in inner.infolist() if not x.is_dir() and PurePosixPath(x.filename).name.lower()=='readme.txt']
            if len(hits)!=1 or hits[0].file_size>65536:raise ValueError('README scope mismatch: '+site)
            data=inner.read(hits[0])
    if digest(path)!=item['outer']:raise ValueError('outer ZIP changed during scan: '+site)
    if sha_bytes(data)!=README_SHA:raise ValueError('README SHA mismatch: '+site)
    lines=clock_lines(data.decode('utf-8-sig',errors='replace'))
    if not any('local solar time' in x['text'].lower() and 'without dst' in x['text'].lower() for x in lines):
        raise ValueError('expected source clock wording absent: '+site)
    return {'site':site,'outer_sha256_before_after':item['outer'],'nested_member':item['name'],
        'nested_bytes':count,'nested_sha256':inner_sha,'icos_archive_sha256':item['icos_archive'],
        'nested_byte_identity_to_publisher_archive':inner_sha==item['icos_archive'],
        'publisher_archive_url':item['archive_url'],'publisher_subset_url':item['subset_url'],
        'readme_sha256':sha_bytes(data),'readme_clock_lines':lines,
        'publisher_subset_clock_metadata':'TIMESTAMP_END local non-DST; UTC bounds consistent with +9',
        'clock_conflict_status':'README_SOLAR_VS_METADATA_STANDARD_NEEDS_RECONCILIATION',
        'science_status':'ALL_45_HOLD_NO_APPROVED_REPLACEMENT'}
def selftest():
    assert sha_bytes(b'abc')=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
    a=clock_lines('ordinary\nTimestamp is local solar time without DST\nother')
    assert len(a)==1 and a[0]['line']==2
    print('STAGE05BI SELF-TEST PASS; IDENTITY AND README ONLY; ALL HOLD')
def run(root,out):
    base=Path.home()/'japanflux_stage05bi'
    if base.is_symlink() or (base.exists() and not base.is_dir()) or out.parent.resolve()!=base.resolve() or out.exists() or out.is_symlink():
        raise ValueError('output must be a fresh direct child of ~/japanflux_stage05bi')
    results=[]
    for site in ('JP-Tef','JP-Tmd'):
        print('CHECK',site,flush=True);results.append(inspect(site,root))
    # All checks precede creation; an identity mismatch is reported, not hidden.
    base.mkdir(exist_ok=True);out.mkdir()
    report={'status':'SOURCE_IDENTITY_DIAGNOSTIC_ALL_45_HOLD','approved_values':0,
        'sites':results,'icos_sha_values_published_metadata_not_downloaded':True,
        'interpretation':'matching nested/archive bytes establishes identity, not resolution of conflicting clock descriptions or scientific repair approval',
        'original_zip_forcing_model_pft_soil_slurm_modified':False}
    with (out/'summary_HOLD.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,ensure_ascii=False);f.write('\n')
    print('STAGE05BI COMPLETE; TWO SOURCE IDENTITIES CHECKED; ALL 45 HOLD; ZERO APPROVED')
    print('OUTPUT',out);print(json.dumps(report,indent=2,ensure_ascii=False))
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-test',action='store_true')
    p.add_argument('--source-root',type=Path,default=ROOT);p.add_argument('--out',type=Path);a=p.parse_args()
    if a.self_test:selftest();return
    if a.out is None:p.error('--out required')
    run(a.source_root,a.out)
if __name__=='__main__':main()

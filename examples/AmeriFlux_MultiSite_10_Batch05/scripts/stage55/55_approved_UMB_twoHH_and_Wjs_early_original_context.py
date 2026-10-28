#!/usr/bin/env python3
"""AmeriFlux Batch05 Stage55: two approved US-UMB RH-interpolation candidate rows,
plus expanded unmodified US-Wjs original context BEFORE 2018-03-11 19:00
and BEFORE 2021-11-02 06:00. No source, forcing, CIME, Slurm edits.
The product's TA_ERA/VPD_ERA is not independent ERA5-Land. RH inferred from
T/VPD is a diagnostic, not an independently verified sensor observation.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

SOURCE_EVENTS = {'US-UMB_E0003':1, 'US-Wjs_E0079':3, 'US-Wjs_E0114':4}
UMB_TIMES = ('200905191030','200905191100','200905191130','200905191200')
UMB_INTERP = UMB_TIMES[1:3]
WJS_WINDOWS = {
 '2018_before_19': ('201803111300','201803112000'),
 '2021_before_06': ('202111020000','202111020700'),
}
UMBFIELDS = ('site','native_time','original_T_C','original_TA_F_QC','original_VPD_hPa',
 'original_VPD_F_QC','original_RH_source_field','approved_interpolated_RH_pct',
 'approved_reconstructed_VPD_hPa','left_anchor_native','right_anchor_native',
 'left_anchor_source_RH_pct','right_anchor_source_RH_pct',
 'method','approval','production_DATM_permission','source_file','source_member','source_sha256')
CONTEXT_FIELDS = ('site','window','native_time','position','TA_F_C','TA_F_QC',
 'VPD_F_hPa','VPD_F_QC','RH_original_source_pct','RH_derived_from_TA_VPD_pct',
 'source_TA_ERA_C','source_VPD_ERA_hPa','source_ERA_RH_derived_pct',
 'source_file','source_member','source_sha256')

def n(s):
 try:
  x=float(s)
  if math.isfinite(x) and x not in (-9999.,-6999.):return x
 except(TypeError,ValueError):pass
 return None

def es(t):
 return 6.112*math.exp(17.67*t/(243.5+t)) if t is not None and -80<=t<=60 else None

def rhcalc(t,v):
 e=es(t)
 return 100*(1-v/e) if e is not None and v is not None else None

def clk(s):return datetime.strptime(s,'%Y%m%d%H%M')
def ts(d):return d.strftime('%Y%m%d%H%M')
def stamp_range(start,end):
 a,b=clk(start),clk(end)
 if a>b:raise ValueError('bad original native range')
 return [ts(a+timedelta(minutes=30*i)) for i in range(int((b-a).total_seconds()//1800)+1)]

def fp(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def read(p):
 if p.is_symlink() or not p.is_file():raise ValueError('source report missing '+str(p))
 with p.open(newline='',encoding='utf-8-sig') as f:
  rd=csv.DictReader(f); hdr=rd.fieldnames or []
  if len(set(hdr))!=len(hdr):raise ValueError('duplicate source report headers')
  return list(rd)

def csvwrite(p,fields,rows):
 with p.open('x',newline='',encoding='utf-8') as f:
  wr=csv.DictWriter(f,fieldnames=fields,extrasaction='raise');wr.writeheader();wr.writerows(rows)

def source_rows(file,member,clock,times):
 p=Path(file)
 if p.is_symlink() or not p.is_file():raise ValueError('source product missing '+file)
 wanted=set(times)
 if p.suffix.lower()=='.zip':
  z=zipfile.ZipFile(p)
  try:
   if member not in z.namelist():raise ValueError('original ZIP member missing '+member)
   with z.open(member) as fb:
    return extract(io.TextIOWrapper(fb,encoding='utf-8-sig',newline=''),clock,wanted)
  finally:z.close()
 with p.open(newline='',encoding='utf-8-sig') as f:return extract(f,clock,wanted)

def extract(f,clock,wanted):
 rd=csv.DictReader(f)
 hdr=rd.fieldnames or []
 if not {clock,'TA_F','TA_F_QC','VPD_F','VPD_F_QC','RH'}.issubset(hdr) or len(set(hdr))!=len(hdr):
  raise ValueError('original product headers missing, RH or clock invalid')
 out={}
 for r in rd:
  t=r[clock]
  if t in wanted:
   if t in out:raise ValueError('duplicate native source time '+t)
   out[t]=r
 if set(out)!=wanted:raise ValueError('incomplete actual original window; missing '+str(sorted(wanted-set(out))))
 return out

def f(x):return 'NA' if x is None or x=='' else (f'{x:.3f}' if isinstance(x,(float,int)) else str(x))

def selftest():
 assert stamp_range('200905191030','200905191200')==list(UMB_TIMES)
 assert len(stamp_range(*WJS_WINDOWS['2018_before_19']))==15
 assert len(stamp_range(*WJS_WINDOWS['2021_before_06']))==15
 assert n('-9999') is None and abs(rhcalc(20,0)-100)<1e-12
 assert sum(SOURCE_EVENTS.values())==8
 T=8.168; trial=97.193+(95.568-97.193)/3
 assert abs(es(T)*(1-trial/100)-.363)<.002
 print('STAGE55 SELF-TEST PASS | two exact US-UMB approved trial overlay rows, two 15HH Wjs source windows; NO source writes')

def main():
 a=argparse.ArgumentParser(description=__doc__)
 a.add_argument('--self-test',action='store_true')
 a.add_argument('--stage53-dir',type=Path)
 a.add_argument('--stage52-dir',type=Path)
 a.add_argument('--out',type=Path)
 v=a.parse_args()
 if v.self_test:selftest();return
 if any(z is None for z in (v.stage53_dir,v.stage52_dir,v.out)):a.error('Stage52/53 and new --out required')
 d53,d52,out=[z.expanduser().resolve() for z in (v.stage53_dir,v.stage52_dir,v.out)]
 if not (d53.is_dir() and d52.is_dir() and out.parent.is_dir()) or out.exists() or any(out==d or out in d.parents or d in out.parents for d in (d53,d52)):
  a.error('original read-only report directories and new output must be distinct')
 p53=d53/'stage53_20_HH_BEFORE_DURING_AFTER_PRIMARY_TOWER_SOURCE_ERA.csv'
 p52=d52/'stage52_THREE_EVENT_RAW_SOURCE_PRODUCT_INVENTORY.csv'
 stage53=read(p53);inventory=read(p52)
 if len(stage53)!=20:raise ValueError('Stage53 population drift')
 for event,count in SOURCE_EVENTS.items():
  rows=[r for r in stage53 if r.get('episode_id')==event and r.get('role')=='EVENT']
  if len(rows)!=count:raise ValueError('original event population drift '+event)
 if any(r.get('science_approval')!='NO' or r.get('DATM_permission')!='NO' for r in stage53):
  raise ValueError('Stage53 science/production status unexpectedly changed')
 sites={}
 for site in ('US-UMB','US-Wjs'):
  candidates=[r for r in stage53 if r.get('site')==site and r.get('role')=='EVENT']
  keys={(r['source_file'],r['source_member'],r['source_sha256']) for r in candidates}
  if len(keys)!=1:raise ValueError('event source products changed or mixed '+site)
  file,member,sha=keys.pop()
  inv=[r for r in inventory if r.get('site')==site and r.get('source_file')==file and
       r.get('source_member')==member and r.get('source_file_SHA256')==sha]
  clocks={r['timestamp_column'] for r in inv}
  if len(clocks)!=1:raise ValueError('missing/ambiguous Stage52 native clock '+site)
  p=Path(file)
  if not p.is_file() or p.is_symlink() or fp(p)!=sha:
   raise ValueError('immutable original product SHA mismatch '+site)
  sites[site]=(file,member,sha,clocks.pop())
 umbsource=sites['US-UMB']
 umb=source_rows(umbsource[0],umbsource[1],umbsource[3],UMB_TIMES)
 for r in stage53:
  if r.get('site')!='US-UMB' or r.get('native_time') not in UMB_TIMES:continue
  src=umb[r['native_time']]
  if abs(n(src['TA_F'])-n(r['tower_TA_C']))>.002 or abs(n(src['VPD_F'])-n(r['tower_VPD_hPa']))>.002 or src['VPD_F_QC']!=r['tower_VPD_QC']:
   raise ValueError('original verified Stage53 US-UMB science evidence drift')
 l,r=umb[UMB_TIMES[0]],umb[UMB_TIMES[3]]
 if any(z['TA_F_QC']!='0' or z['VPD_F_QC']!='0' for z in (l,r)):
  raise ValueError('US-UMB original RH endpoints not both source QC0')
 rl,rr=n(l['RH']),n(r['RH'])
 if rl is None or rr is None or not(0<=rl<=100 and 0<=rr<=100):
  raise ValueError('US-UMB original RH anchor fields missing')
 for z in (l,r):
  if n(z['TA_F']) is None or n(z['VPD_F']) is None or abs(rhcalc(n(z['TA_F']),n(z['VPD_F']))-n(z['RH']))>.03:
   raise ValueError('US-UMB source QC0 anchor physical RH mismatch')
 applied=[]
 print('STAGE55 US-UMB USER-APPROVED 2HH INTERPOLATION | ORIGINAL SOURCE PRESERVED')
 print('native time | T C | original VPD hPa | original VPD QC | source RH | interpolated RH | versioned candidate VPD hPa')
 for j,t in enumerate(UMB_TIMES):
  z=umb[t];T,V=n(z['TA_F']),n(z['VPD_F'])
  if j in (1,2):
   if z['TA_F_QC']!='0' or z['VPD_F_QC']!='1' or n(z['RH']) is not None or T is None or V is None:
    raise ValueError('US-UMB only two exact missing-RH, source T QC0/VPD QC1 timestamps may be reconstructed')
   rhnew=rl+(rr-rl)*(j/3)
   vnew=es(T)*(1-rhnew/100)
   if not 0<=rhnew<=100 or not 0<=vnew<=es(T):
    raise ValueError('unphysical RH/VPD trial')
   applied.append(dict(site='US-UMB',native_time=t,original_T_C=T,original_TA_F_QC=z['TA_F_QC'],
    original_VPD_hPa=V,original_VPD_F_QC=z['VPD_F_QC'],original_RH_source_field=z['RH'],
    approved_interpolated_RH_pct=f'{rhnew:.9f}',approved_reconstructed_VPD_hPa=f'{vnew:.9f}',
    left_anchor_native=UMB_TIMES[0],right_anchor_native=UMB_TIMES[3],
    left_anchor_source_RH_pct=l['RH'],right_anchor_source_RH_pct=r['RH'],
    method='original_source_RH_linear_time_interpolation_then_original_TA_Magnus_water_VPD',
    approval='USER_APPROVED_2026-10-28_VERSIONED_CANDIDATE_ONLY',production_DATM_permission='NO',
    source_file=umbsource[0],source_member=umbsource[1],source_sha256=umbsource[2]))
  else:rhnew=vnew=None
  print(t,'|',f(T),'|',f(V),'|',z['VPD_F_QC'],'|',f(n(z['RH'])),'|',f(rhnew),'|',f(vnew))
 if len(applied)!=2 or [z['native_time'] for z in applied]!=list(UMB_INTERP):
  raise ValueError('exact-two approved target protection failed')
 wjs=sites['US-Wjs']
 alltimes=set()
 for x in WJS_WINDOWS.values():alltimes.update(stamp_range(*x))
 ww=source_rows(wjs[0],wjs[1],wjs[3],alltimes)
 context=[]
 for label,(start,end) in WJS_WINDOWS.items():
  print('\nSTAGE55 US-Wjs',label,'ORIGINAL DATA BEFORE AND AFTER REQUESTED THRESHOLD')
  print('native HH | Phase | TA C | TA QC | VPD hPa | VPD QC | original RH field | RH from T/VPD | source ERA T C | source ERA VPD hPa | source ERA derived RH')
  mark='201803111900' if label=='2018_before_19' else '202111020600'
  for t in stamp_range(start,end):
   z=ww[t];T,V=n(z.get('TA_F')),n(z.get('VPD_F'));Te,Ve=n(z.get('TA_ERA')),n(z.get('VPD_ERA'))
   position='BEFORE' if t<mark else 'ANCHOR_OR_ONSET' if t==mark else 'AFTER'
   row=dict(site='US-Wjs',window=label,native_time=t,position=position,
    TA_F_C=z.get('TA_F',''),TA_F_QC=z.get('TA_F_QC',''),VPD_F_hPa=z.get('VPD_F',''),
    VPD_F_QC=z.get('VPD_F_QC',''),RH_original_source_pct=z.get('RH',''),
    RH_derived_from_TA_VPD_pct='' if rhcalc(T,V) is None else f'{rhcalc(T,V):.9f}',
    source_TA_ERA_C=z.get('TA_ERA',''),source_VPD_ERA_hPa=z.get('VPD_ERA',''),
    source_ERA_RH_derived_pct='' if rhcalc(Te,Ve) is None else f'{rhcalc(Te,Ve):.9f}',
    source_file=wjs[0],source_member=wjs[1],source_sha256=wjs[2])
   context.append(row)
   print(t,'|',position,'|',f(T),'|',z.get('TA_F_QC','NA'),'|',f(V),'|',
    z.get('VPD_F_QC','NA'),'|',f(n(z.get('RH'))),'|',f(rhcalc(T,V)),'|',
    f(Te),'|',f(Ve),'|',f(rhcalc(Te,Ve)))
 # All source and original validity checks must succeed before any output is created.
 if len(context)!=30 or any(z['site']!='US-Wjs' for z in context):
  raise ValueError('exact requested windows missing')
 out.mkdir(exist_ok=False)
 csvwrite(out/'stage55_USER_APPROVED_US_UMB_2HH_INTERPOLATION_VERSIONED_CANDIDATE.csv',UMBFIELDS,applied)
 csvwrite(out/'stage55_US_Wjs_TWO_EARLIER_NATIVE_CONTEXT_WINDOWS_UNCHANGED.csv',CONTEXT_FIELDS,context)
 manifest={'source_stage53_sha256':fp(p53),'source_stage52_inventory_sha256':fp(p52),
  'source_product_sha256':{k:v[2] for k,v in sites.items()},
  'approval_scope':'US-UMB 200905191100 and 200905191130 ONLY',
  'UMB_approved_versioned_candidate_HH':2,'US_Wjs_untouched_original_context_HH':30,
  'US_Wjs_2018_unchanged':True,'US_Wjs_2021_unchanged':True,
  'existing_166_approved_overlay_unchanged':True,'original_sources_unchanged':True,
  'production_DATM_permission':False,'Slurm_jobs_submitted':0,
  'ERA_source_companion_NOT_independent_ERA5_Land':True,
  'stage55_outputs_sha256':{}}
 for path in sorted(out.glob('*.csv')):manifest['stage55_outputs_sha256'][path.name]=fp(path)
 (out/'stage55_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 print('\nSTAGE55 SUCCESS | US-UMB 2 exact approved interpolation candidate rows | US-Wjs 30 early context HH read-only')
 print('STAGE55_OUTPUT='+str(out))
 print('STAGE55 NO ORIGINAL/166/OTHER HOLDS/DATM/CIME/SLURM MODIFICATIONS')
if __name__=='__main__':main()

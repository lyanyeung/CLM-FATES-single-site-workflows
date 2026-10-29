#!/usr/bin/env python3
"""IRIDIS6 Batch05 DIRECT AD400 stack + Slurm inheritance guard.

Adapted from Non-Competition-CLM-experiment
examples/AmeriFlux_Batch04_10/scripts/b04_stack_guard.py and
examples/Batch03_10/scripts/11_batch03_AD400_oneclick.py.
THIS MODULE DOES NOT SUBMIT ANY JOB.

IMPORTANT: The future actual Batch05 AD400 submission controller MUST import
and call require_for_submission(site=...,phase="DIRECT_AD400") immediately
before subprocess.run([CASE/"case.submit", "--skip-preview-namelist"]) in
THE SAME Python process, and persist returned resource record in its per-site
ATTEMPTED submission ledger BEFORE calling case.submit.
Standalone Python that raises RLIMIT_STACK does NOT change a later shell.

Soft stack >=65536 KiB. Preferred when raising: 300000 KiB.
Never lower unlimited/already-high soft stack. Never change the hard limit.
Slurm PropagateResourceLimits must contain STACK or ALL, checked live.
"""
import argparse,json,re,resource,subprocess

MIN_KIB=65536
PREFERRED_KIB=300000
KIB=1024
SITES=("US-UiD","US-UMB","US-UMd","US-Var","US-Vcm",
       "US-Vcp","US-WCr","US-Whs","US-Wjs","US-Wkg")
def show(x):
 return "unlimited" if x==resource.RLIM_INFINITY else x//KIB
def okay(x):return x==resource.RLIM_INFINITY or x>=MIN_KIB*KIB
def target(soft,hard):
 if okay(soft):return soft
 if hard!=resource.RLIM_INFINITY and hard<MIN_KIB*KIB:return None
 preferred=PREFERRED_KIB*KIB
 return preferred if hard==resource.RLIM_INFINITY else min(preferred,hard)
def inspect_stack(*,raise_current_soft=False):
 before,hard=resource.getrlimit(resource.RLIMIT_STACK)
 after=before
 if not okay(before) and raise_current_soft:
  new=target(before,hard)
  if new is None:raise RuntimeError("Batch05 HARD STACK LIMIT BELOW 65536 KiB")
  try:resource.setrlimit(resource.RLIMIT_STACK,(new,hard))
  except (OSError,ValueError) as e:raise RuntimeError("Batch05 cannot raise current process soft stack") from e
  after,newhard=resource.getrlimit(resource.RLIMIT_STACK)
  if newhard!=hard or (before==resource.RLIM_INFINITY and after!=before) or (
    before!=resource.RLIM_INFINITY and after<before):
   raise RuntimeError("Batch05 stack monotonicity or hard-limit invariant violated")
 rec=dict(soft_before_KiB=show(before),soft_at_guard_KiB=show(after),
          hard_limit_KiB=show(hard),minimum_KiB=MIN_KIB,
          adequate=okay(after),raised_only_current_python_process=after!=before,
          no_lowering=True,hard_limit_unchanged=True)
 if not rec["adequate"]:
  raise RuntimeError("Batch05 stack HOLD "+json.dumps(rec,sort_keys=True)+
   "; use ulimit -s unlimited (or ulimit -s 300000) in the actual submit shell, "+
   "or import this module inside the actual submitting Python process")
 return rec
def slurm_propagation():
 try:
  p=subprocess.run(["scontrol","show","config"],capture_output=True,text=True,timeout=20,check=False)
 except (OSError,subprocess.TimeoutExpired) as e:
  raise RuntimeError("Batch05 SLURM config unavailable, cannot prove inherited STACK") from e
 if p.returncode:
  raise RuntimeError("Batch05 SLURM scontrol failed "+p.stderr[-400:])
 m=re.search(r"(?mi)^\s*PropagateResourceLimits\s*=\s*(\S.*)$",p.stdout)
 if not m:raise RuntimeError("Batch05 SLURM PropagateResourceLimits not found")
 raw=m.group(1).strip().split()[0]
 tokens={x.upper() for x in raw.split(",")}
 if not ({"ALL","STACK"} & tokens):
  raise RuntimeError("Batch05 SLURM PropagateResourceLimits="+raw+" excludes STACK")
 return dict(PropagateResourceLimits=raw,stack_propagated_by_scheduler=True)
def require_for_submission(*,site,phase="DIRECT_AD400",may_raise=True):
 if site not in SITES:raise RuntimeError("Batch05 unexpected site "+str(site))
 if phase!="DIRECT_AD400":raise RuntimeError("Batch05 requires direct 400y phase")
 rec=inspect_stack(raise_current_soft=may_raise)
 rec["slurm"]=slurm_propagation()
 rec["site"]=site;rec["phase"]=phase
 rec["in_same_process_as_future_case_submit_required"]=True
 print("BATCH05 DIRECT AD400 STACK/SCHEDULER SUBMISSION GATE PASS",
   site,json.dumps(rec,sort_keys=True),flush=True)
 return rec
def selftest():
 inf=resource.RLIM_INFINITY
 assert okay(inf) and okay(65536*KIB) and not okay(8192*KIB)
 assert target(8192*KIB,inf)==300000*KIB
 assert target(8192*KIB,180000*KIB)==180000*KIB
 assert target(8192*KIB,32768*KIB) is None
 assert target(inf,inf)==inf
 assert target(500000*KIB,inf)==500000*KIB
 assert len(SITES)==10
 print("BATCH05 STACK GUARD SELF-TEST PASS | 8MiB cannot submit; target 300000KiB; >=65536KiB & unlimited never lowered; hard cannot be changed")
def main():
 a=argparse.ArgumentParser(description=__doc__)
 a.add_argument("--self-test",action="store_true")
 a.add_argument("--check",action="store_true")
 x=a.parse_args()
 if x.self_test:selftest();return
 if not x.check:a.error("use --check or --self-test; guard never submits jobs")
 rec=inspect_stack(raise_current_soft=False)
 scheduler=slurm_propagation()
 print("BATCH05 DIRECT AD400 LIVE STACK PRECHECK PASS",json.dumps(rec,sort_keys=True))
 print("BATCH05 DIRECT AD400 LIVE SLURM STACK PROPAGATION PASS",
   json.dumps(scheduler,sort_keys=True))
 print("BATCH05 NOTE: actual submitting controller MUST call require_for_submission in same Python process; this precheck alone is NOT a submission guarantee")
if __name__=="__main__":main()

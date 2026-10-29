#!/usr/bin/env python3
"""US-MMS: isolated one-pass exploratory humidity scenario; NOT DATM approved.

16 missing hourly values: 6 March-2000 use companion ERA RH at retained T;
5 Sep-2014 missing included in whole 47-QC1 48h ERA-RH replacement;
5 cold QC2 gaps interpolate ice-relative RH between physically valid
selected-source anchors. Never touch original Stage12G or tower input.
"""
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

ROOT = Path('/iridisfs/scratch/ly3n24/CLM_FATES/experiments/AmeriFlux_MultiSite_10_Batch03')
OLD = ROOT/'science_trials/stage12g_six_site_new_year_gridRH_science_20261025T083234Z_e168f29f'
MAN = ROOT/'qcv5_native_trial_20261022T024559Z_36c46e58/exact_input_manifest.json'
AUD = ROOT/'reports/us_mms_16hour_onepass_manual_science_20261029T031440Z_b66bdf1c'
FN = 'US-MMS_STAGE12G_INCOMPLETE_NOLEAP.csv'
MARCH = '200003051700 200003061600 200003061700 200003061800 200003061900 200003062000'.split()
SEPT = '201409220700 201409220900 201409221000 201409230700 201409230800'.split()
COLD = '201502240700 201901301000 201901301100 201901301200 201901301300'.split()
GAPS = set(MARCH + SEPT + COLD)
FIELDS = 'time TBOT QBOT PSRF FSDS FLDS WIND PRECTmms TA_USE VPD_USE'.split()

def ensure(flag, message):
    if not bool(flag):
        raise RuntimeError('US-MMS STOP (no input changed): ' + message)

def digest(path):
    p = Path(path)
    ensure(p.is_file() and not p.is_symlink(), 'required pinned file '+str(p))
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def esw(t):
    t = np.asarray(t, float)
    return 6.112*np.exp(17.67*t/(t+243.5))

def esi(t):
    t = np.asarray(t, float)
    return 6.112*np.exp(22.46*t/(t+272.62))

def qcalc(e,p):
    return 0.622*(100*e)/(p-0.378*100*e)

def main():
    ensure(len(GAPS)==16 and 25*365*24==219000 and esi(-20)<esw(-20), 'internal self-test')
    old_receipt = json.loads((OLD/'stage12g_research_only_sha_receipt.json').read_text())
    ensure(old_receipt['output_sha256'][FN]==digest(OLD/FN), 'Stage12G source SHA')
    ensure(old_receipt['Postv5_approved']==0, 'Stage12G model status changed')
    aud_receipt = json.loads((AUD/'US_MMS_readonly_source_science_SHA_receipt.json').read_text())
    audit = AUD/'US_MMS_16_missing_hour_manual_science_decisions.csv'
    ensure(aud_receipt['outputs_SHA256'][audit.name]==digest(audit), 'Stage14B signed audit SHA')
    manifest = json.loads(MAN.read_text())
    info = next(s for s in manifest['sites'] if s['site']=='US-MMS')
    ensure(int(info['native_minutes'])==60, 'native source must be hourly')
    for var in ('primary','era'):
        p = Path(info[var])
        ensure(manifest['input_sha256'][str(p.resolve())]==digest(p), 'original '+var+' SHA')
    source = pd.read_csv(info['primary'], usecols=['TIMESTAMP_START','TA_F_QC','VPD_F_QC'],
                         dtype={'TIMESTAMP_START':str}).set_index('TIMESTAMP_START')
    era = pd.read_csv(info['era'], usecols=['TIMESTAMP_START','TA_ERA','VPD_ERA'],
                      dtype={'TIMESTAMP_START':str}).set_index('TIMESTAMP_START')
    base = pd.read_csv(OLD/FN)
    ensure(len(base)==219000 and list(base.columns)==FIELDS, 'original 219000 schema')
    base.index = pd.to_datetime(base.time).dt.strftime('%Y%m%d%H%M')
    ensure(base.index.is_unique and set(base.index[base.VPD_USE.isna()])==GAPS and
           set(base.index[base.QBOT.isna()])==GAPS, 'exact original 16 gaps')

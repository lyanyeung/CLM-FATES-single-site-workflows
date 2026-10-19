#!/usr/bin/env bash
# Publish only source/docs to GitHub. Fresh SSH clone: never alters user's working repository or runs Slurm.
set -Eeuo pipefail
trap 'rc=$?; echo "[ERROR] at line $LINENO, exit $rc; publication incomplete. Do not assume git push succeeded." >&2' ERR

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PKG="$HERE/package"
ORIGINAL="$HOME/CLM-FATES-single-site-workflows"
SSH_REMOTE="git@github.com:lyanyeung/CLM-FATES-single-site-workflows.git"
REL="examples/FLUXNET_MultiSite_13"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
SESSION="$HOME/FLUXNET13_PUBLICATION_${STAMP}_$$"
CHECKOUT="$SESSION/repo"
LEDGER="$SESSION/source_inventory.tsv"
mkdir -p "$SESSION"
[[ -s "$HERE/README_APPENDIX.md" && -d "$PKG/scripts" && -d "$PKG/docs" ]] || { echo 'Incomplete bundle; abort.' >&2; exit 1; }
command -v git >/dev/null && command -v python3 >/dev/null || { echo 'git/python3 unavailable' >&2; exit 1; }

printf '\n[1/6] Clone current GitHub main into separate publication directory (SSH)\n'
printf 'Session: %s\n' "$SESSION"
GIT_TERMINAL_PROMPT=0 git clone --quiet --single-branch --branch main "$SSH_REMOTE" "$CHECKOUT"
[[ -d "$CHECKOUT/.git" && -f "$CHECKOUT/$REL/README.md" ]] || { echo 'Wrong repository structure' >&2; exit 1; }
mkdir -p "$CHECKOUT/$REL/scripts" "$CHECKOUT/$REL/docs"
printf 'source_rel\torigin\tarchive_rel\tsha256\tbytes\tresult\n' > "$LEDGER"

printf '\n[2/6] Copy source scripts from actual IRIDIS HOME when available, bundled copies otherwise\n'
python3 - "$HERE" "$CHECKOUT" "$LEDGER" "$HOME" <<'PY'
from pathlib import Path
import hashlib,sys,shutil,re
bundle, checkout, ledger, home=map(Path,sys.argv[1:])
rel=Path('examples/FLUXNET_MultiSite_13')
sourcebase=bundle/'package'/'scripts'
allowed={'.py','.sh','.md'}
counts={'added':0,'same':0,'conflict_variant':0}

def store(src, name, origin):
    src=Path(src)
    assert src.is_file() and not src.is_symlink(),f'Bad source {src}'
    assert src.suffix in allowed, f'Invalid extension {src}'
    size=src.stat().st_size
    assert size>0 and size<=512*1024, f'Bad size {src}: {size}'
    raw=src.read_bytes()
    assert b'\x00' not in raw, f'Binary data rejected: {src}'
    assert not re.search(rb'(?:-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----|ghp_[A-Za-z0-9]{20,})', raw),f'Possible secret in {src}'
    target=checkout/rel/name
    assert target.resolve().is_relative_to((checkout/rel).resolve()),f'Escaping target {target}'
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if target.read_bytes()==raw:
            result='IDENTICAL'; counts['same']+=1
        else:
            sha=hashlib.sha256(raw).hexdigest()[:10]
            suffix=target.suffix
            target=target.with_name(target.stem+'_IRIDIS_'+sha+suffix)
            if target.exists():
                assert target.read_bytes()==raw,f'Variant hash collision: {target}'
            else:target.write_bytes(raw)
            result='VERSIONED_DIFFERENCE';counts['conflict_variant']+=1
    else:
        target.write_bytes(raw);result='ADDED';counts['added']+=1
    relpath=target.relative_to(checkout).as_posix()
    with ledger.open('a',encoding='utf-8') as f:
        f.write(f'{name.as_posix()}\t{origin}\t{relpath}\t{hashlib.sha256(raw).hexdigest()}\t{len(raw)}\tSOURCE_SNAPSHOT\n')
    print(f'{result:<21} {relpath} ({origin})')

for packaged in sorted(sourcebase.rglob('*')):
    if not packaged.is_file():continue
    sub=packaged.relative_to(sourcebase)
    # Prefer actual implementation on IRIDIS, where available; never touch IRIDIS case directories.
    home_script=home/packaged.name
    candidate=home_script if home_script.is_file() else packaged
    store(candidate,Path('scripts')/sub,'IRIDIS_HOME' if candidate==home_script else 'BUNDLED_VERIFIED_SNAPSHOT')
    if candidate==home_script and home_script.read_bytes()!=packaged.read_bytes():
        store(packaged,Path('scripts')/sub,'BUNDLED_SNAPSHOT_ALTERNATIVE')

# Stage23 source scripts can be in IRIDIS home; our bundle only contains source-confirmed stages.
extra=[]
for pat in ('23*BIF*.py','23*BIF*.sh','23*13site*.py','23*13site*.sh','23*height*.py'):
    extra.extend(home.glob(pat))
for src in sorted(set(extra)):
    if src.is_file() and src.stat().st_size<=512*1024:
        store(src,Path('scripts/stage23')/src.name,'IRIDIS_HOME_DISCOVERED')
if not extra:print('STAGE23: original runnable source not found in HOME; docs explicitly identify its report provenance.')

# Site surface source is already in GitHub. Archive actual IRIDIS version separately when different.
for n in ('02_make_13_surfaces.sh','make_13_surfaces.sh'):
    src=home/n
    if src.is_file():store(src,Path('scripts/stage02')/src.name,'IRIDIS_HOME')
print('Script files:',counts)
PY

printf '\n[3/6] Add detailed documentation, preserving any pre-existing GitHub documents\n'
python3 - "$HERE" "$CHECKOUT" <<'PY'
from pathlib import Path
import hashlib,sys
here,checkout=map(Path,sys.argv[1:])
root=checkout/'examples/FLUXNET_MultiSite_13'
for p in sorted((here/'package/docs').glob('*.md')):
    data=p.read_bytes()
    dest=root/'docs'/p.name
    if dest.exists() and dest.read_bytes()!=data:
        dest=dest.with_name(dest.stem+'_REV_'+hashlib.sha256(data).hexdigest()[:10]+dest.suffix)
    dest.write_bytes(data)
    print('DOC',dest.relative_to(checkout))

readme=root/'README.md'
s=readme.read_text(encoding='utf-8')
append=(here/'README_APPENDIX.md').read_text(encoding='utf-8').strip()
start='<!-- FLUXNET13_20261018_FULLSYNC_START -->'
end='<!-- FLUXNET13_20261018_FULLSYNC_END -->'
assert (start in s)==(end in s), 'README old stage markers are unbalanced'
if start in s:
    a=s.index(start);b=s.index(end,a)+len(end)
    s=s[:a]+s[b:]
lines=s.splitlines(keepends=True)
assert lines and 'FLUXNET MultiSite 13' in lines[0], 'Unexpected README beginning'
# Preserve old historical timeline, surface/BIF audit and any Stage30 locally present.
old_header=lines[0]
rest=''.join(lines[1:])
if 'Research checkpoint, 15 October 2026' in rest:
    rest=rest.replace('**Research checkpoint, 15 October 2026.**', '**Historical checkpoint, 15 October 2026 (prior to the 18 October Stage28–30 completions).**',1)
rest=rest.replace('## Decisions still pending before BIF','## Historical Stage21 science decisions before the later BIF implementation',1)
rest=rest.replace('**BIF gate: CLOSED_PENDING_SCIENTIFIC_MET_QC.**','**Historical Stage21 BIF gate: CLOSED_PENDING_SCIENTIFIC_MET_QC.** The later Stage29b/30 research-only BIF/ZBOT/DATM products are described above; scientific approval remains open.',1)
readme.write_text(old_header+'\n'+append+'\n\n'+rest.lstrip('\n'),encoding='utf-8')
print('README refreshed with current scientific checkpoint; older notes preserved.')
PY

# Persist source manifest under docs. No absolute local paths or source data.
cp "$LEDGER" "$CHECKOUT/$REL/docs/CODE_SOURCES_SHA256_20261018.tsv"

printf '\n[4/6] Audit all staged files; do not push data, secrets or syntax errors\n'
cd "$CHECKOUT"
git add -- "$REL/README.md" "$REL/docs" "$REL/scripts"
python3 - "$CHECKOUT" "$REL" <<'PY'
from pathlib import Path
import subprocess,sys,ast,re
repo,rel=Path(sys.argv[1]),sys.argv[2]
paths=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=repo).decode().strip('\x00').split('\x00')
for name in filter(None,paths):
    assert name.startswith(rel+'/'),f'Non-target git add: {name}'
    p=repo/name
    assert p.suffix in ('.md','.py','.sh','.tsv'),f'Unsafe staged extension {name}'
    assert p.is_file() and p.stat().st_size<=512*1024,f'Unexpected data file {name}'
    raw=p.read_bytes()
    assert not re.search(rb'-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----|ghp_[A-Za-z0-9]{20,}',raw),f'Possible credentials {name}'
    if p.suffix=='.py':
        ast.parse(raw.decode('utf-8'),filename=name)
print('PY_SYNTAX_AND_WHITELIST_OK; staged=',len(list(filter(None,paths))))
PY
# These are original historical source snapshots. A few contain pre-existing
# trailing spaces, which are not reasons to rewrite research code. Ignore only
# that whitespace class while still checking for substantive whitespace errors.
git -c core.whitespace=-trailing-space,-space-before-tab diff --cached --check
git diff --cached --stat
if git diff --cached --quiet; then
    echo 'NO_CHANGES: GitHub content is already identical; no commit necessary.'
    git log -1 --format='%h %s'
    exit 0
fi

printf '\n[5/6] Commit only audited changes and push to main without force\n'
git commit -m 'Archive 13-site MET BIF height DATM surface and spinup1000 sources with science caveats'
git push origin HEAD:refs/heads/main

printf '\n[6/6] Confirm GitHub HEAD and report successful publication\n'
local_head="$(git rev-parse HEAD)"
remote_head="$(git ls-remote origin refs/heads/main | awk '{print $1}')"
[[ "$local_head" == "$remote_head" ]] || { echo "REMOTE_HEAD_MISMATCH local=$local_head remote=$remote_head" >&2; exit 1; }
printf '\n=== GITHUB FULL 13-SITE CODE + DOCS SYNC SUCCESS ===\n'
printf 'COMMIT: %s\n' "$local_head"
printf 'URL: https://github.com/lyanyeung/CLM-FATES-single-site-workflows/tree/main/examples/FLUXNET_MultiSite_13\n'
printf 'REPORT: %s\n' "$SESSION"
echo 'Note: no MET NetCDF, flux data, case directories, Slurm actions or model outputs were modified.'

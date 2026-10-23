#!/usr/bin/env python3
"""Batch03 Stage09g: one-command, resumable completion of all remaining CDS data.

Calls the existing verified Stage09f queue sequentially in batches of at most
three. Before and after every batch, rechecks SHA receipts, NetCDF variables,
grid coordinates and hourly UTC coverage through Stage09f. Existing outputs
are never overwritten. Stops immediately on failure; re-run to resume.

--check is strictly READ ONLY and never calls CDS.
--run writes ONLY external evidence ZIP/receipt and an advisory lock file;
it does not produce forcing, perform tower/UTC joins, or launch model jobs.
"""
import argparse
import fcntl
import importlib.util
from pathlib import Path
import subprocess
import sys

EXPECTED_REQUESTS = 32
EXPECTED_BLOCKERS = 1924
SOURCE_NAME = "09f_incremental_dewpoint_queue.py"
LOCK_NAME = ".batch03_stage09g_active_download.lock"


def load_queue(script: Path):
    if not script.is_file() or script.is_symlink():
        raise RuntimeError(f"Stage09f script missing or unsafe: {script}")
    spec = importlib.util.spec_from_file_location("batch03_stage09f", str(script))
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load Stage09f")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snapshot(queue):
    plan = queue.read_source()
    if len(plan) != EXPECTED_REQUESTS:
        raise RuntimeError("Stage09a plan differs from 32 requested site-years")
    if sum(int(record["blocked_native_records"]) for record in plan) != EXPECTED_BLOCKERS:
        raise RuntimeError("Stage09a blocker event total differs from 1924")
    if not queue.PILOT.is_file() or queue.PILOT.is_symlink():
        raise RuntimeError("Stage09b single-year downloader missing")
    marker = (queue.ROOT /
              "qcv5_native_trial_20261022T024559Z_36c46e58" /
              "INCOMPLETE_DO_NOT_USE_FOR_DATM_OR_SPINUP")
    if not marker.is_file():
        raise RuntimeError("Stage07 scientific hold marker unexpectedly missing")
    verified, missing, events_covered = [], [], 0
    for record in plan:
        state, metadata = queue.check_artifact(record)
        if state == "VERIFIED":
            verified.append(record)
            events_covered += int(record["blocked_native_records"])
        elif state == "MISSING":
            missing.append(record)
        else:
            raise RuntimeError("Unexpected data state for " + str(record))
    missing.sort(key=lambda r: (-int(r["blocked_native_records"]), r["site"], int(r["year"])))
    return len(verified), len(missing), events_covered, missing


def report(prefix, state):
    valid, todo, covered, pending = state
    print(f"{prefix} VERIFIED={valid}/{EXPECTED_REQUESTS} "
          f"REMAINING={todo} BLOCKER_EVIDENCE={covered}/{EXPECTED_BLOCKERS}",
          flush=True)
    if todo:
        print(prefix, "NEXT:", ", ".join(
            f"{r['site']}:{r['year']}({r['blocked_native_records']})"
            for r in pending[:3]), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true",
                      help="Audit all 32 requested products; do not write or retrieve")
    mode.add_argument("--run", action="store_true",
                      help="Continue until every requested site-year is verified or one fails")
    p.add_argument("--batch-size", type=int, default=3,
                   help="Maximum serial requests in each Stage09f pass (1–3)")
    args = p.parse_args()
    if not 1 <= args.batch_size <= 3:
        p.error("--batch-size must be 1, 2, or 3")
    script = Path(__file__).resolve().with_name(SOURCE_NAME)
    queue = load_queue(script)
    start = snapshot(queue)
    report("STAGE09G PREFLIGHT:", start)
    print("SCIENTIFIC HOLD: external dewpoint is NOT forcing approval;"
          " UTC offsets, time alignment, grid elevation and QC remain unresolved.", flush=True)
    if args.check:
        print("CHECK ONLY: no API calls, files, or model jobs", flush=True)
        return
    if start[1] == 0:
        print("STAGE09G COMPLETE: 32/32 verified, no additional downloads required", flush=True)
        return

    external = queue.ARCHIVE
    if not external.is_dir() or external.is_symlink():
        raise RuntimeError("Expected preexisting non-symlink external evidence directory")
    lock_path = external / LOCK_NAME
    if lock_path.is_symlink():
        raise RuntimeError("Refusing a symlink lock path")
    # A persistent advisory lock file is safer than trying to delete the
    # lock file while another process might be attempting the same work.
    with lock_path.open("a+", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Another Stage09g drain is running; stop duplicate requests") from exc
        # Revalidate after taking the lock to avoid a stale preflight.
        before = snapshot(queue)
        report("STAGE09G LOCKED:", before)
        batches = 0
        newly_downloaded = 0
        while before[1] > 0:
            count = min(args.batch_size, before[1])
            print(f"\nSTAGE09G BATCH {batches+1}: downloading at most {count}, "
                  f"remaining before={before[1]}", flush=True)
            cmd = [sys.executable, "-B", "-u", str(script),
                   "--run", "--max-new", str(count)]
            # Stage09f rechecks every saved artifact and invokes Stage09b
            # sequentially. An error halts here and leaves verified products
            # intact for an explicit rerun.
            subprocess.run(cmd, check=True)
            after = snapshot(queue)
            delta = after[0] - before[0]
            if delta != count or after[1] != before[1] - count:
                raise RuntimeError("Verified progress disagrees with requested batch: "
                                   f"delta={delta}, expected={count}; stop and inspect")
            newly_downloaded += delta
            batches += 1
            report("STAGE09G CHECKPOINT:", after)
            before = after
            if batches > EXPECTED_REQUESTS:
                raise RuntimeError("Batch bound exceeded")
        print(f"\nSTAGE09G COMPLETE: VERIFIED={before[0]}/{EXPECTED_REQUESTS} "
              f"newly_validated={newly_downloaded} batches={batches} "
              f"blocker_evidence={before[2]}/{EXPECTED_BLOCKERS} "
              "original_inputs_unchanged=True", flush=True)
        print("NO DATM, no forcing repair, no spinup and no UTC join were performed.",
              flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSTAGE09G INTERRUPTED. Completed downloads are retained;"
              " run --check before safely resuming. Do not overwrite partial files.",
              file=sys.stderr, flush=True)
        raise SystemExit(130)

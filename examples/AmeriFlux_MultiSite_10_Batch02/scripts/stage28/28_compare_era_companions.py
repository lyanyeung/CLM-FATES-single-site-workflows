#!/usr/bin/env python3
"""Batch02 Stage28: read-only science audit."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"diagnostics"))
from batch02_stage23_31_audits import main
if __name__=="__main__":
    main(fixed=28)

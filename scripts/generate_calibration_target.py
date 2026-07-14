#!/usr/bin/env python3
"""Generate a reproducible SO-101 calibration target kit.

Thin wrapper around :mod:`scenesmith.calibration.cli`. Produces a versioned
directory with the ground-truth bundle, acceptance sheet, MuJoCo/URDF assets,
BOMs, fiducial tables, and preview/printable geometry.

Usage:
    python scripts/generate_calibration_target.py --out dist/calbrick
    python scripts/generate_calibration_target.py --out dist/calbrick \
        --measured-shell-g 58.7 --watertight --step
"""

from scenesmith.calibration.cli import main

if __name__ == "__main__":
    raise SystemExit(main())

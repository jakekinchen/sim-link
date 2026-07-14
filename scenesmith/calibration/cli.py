"""Command-line generator for the calibration target kit.

Emits a self-contained, versioned artifact directory from a single spec:
the ground-truth bundle, acceptance sheet, receipt template, MJCF + URDF sim
assets, BOMs, fiducial tables, and preview/printable geometry -- with the
three-way mass verification run by default.

Two designs are available via ``--design``:
  * ``wcw1`` (default): the ball-cartridge Workcell Calibration Witness.
  * ``calbrick``: the earlier slug-socket brick.

Example:
    python -m scenesmith.calibration --out dist/wcw1 --metrology
"""

from __future__ import annotations

import argparse
import json
import logging

from dataclasses import fields, replace
from pathlib import Path

from scenesmith.calibration import export_stl, wcw1
from scenesmith.calibration.configurations import resolve_target, standard_kit
from scenesmith.calibration.export_bom import write_bom_csv, write_fiducial_csv
from scenesmith.calibration.export_mjcf import to_mjcf_string
from scenesmith.calibration.export_urdf import to_urdf_string
from scenesmith.calibration.geometry import build_geometry
from scenesmith.calibration.receipt import blank_receipt
from scenesmith.calibration.report import (
    acceptance_markdown,
    build_bundle,
    write_bundle,
)
from scenesmith.calibration.spec import default_so101_target

console_logger = logging.getLogger(__name__)

# Design registry: spec factory, geometry builder, kit factory, resolver.
DESIGNS = {
    "wcw1": {
        "factory": wcw1.default_wcw1_target,
        "build_geometry": wcw1.build_wcw1_geometry,
        "kit": wcw1.wcw1_kit,
        "resolve": wcw1.resolve_wcw1,
    },
    "calbrick": {
        "factory": default_so101_target,
        "build_geometry": build_geometry,
        "kit": standard_kit,
        "resolve": resolve_target,
    },
}


def build_spec_from_args(args: argparse.Namespace):
    """Apply CLI overrides on top of the chosen design's default spec."""
    design = DESIGNS[args.design]
    spec = design["factory"]()
    valid_fields = {f.name for f in fields(spec)}
    overrides = {}
    for field_name in (
        "length_mm",
        "width_mm",
        "height_mm",
        "wall_mm",
        "shell_material",
        "cartridge_material",
    ):
        value = getattr(args, field_name, None)
        if value is not None:
            if field_name not in valid_fields:
                console_logger.warning(
                    "--%s ignored: design %s has no such parameter",
                    field_name.replace("_", "-"),
                    args.design,
                )
                continue
            overrides[field_name] = value
    if overrides:
        spec = replace(spec, **overrides)

    if args.measured_shell_g is not None:
        geom = design["build_geometry"](spec)
        spec = spec.with_measured_shell_mass(
            args.measured_shell_g, geom.shell_solid_volume()
        )
    if args.measured_slug_g is not None:
        spec = spec.with_measured_slug_mass(args.measured_slug_g)
    return spec


def generate(
    spec,
    out_dir: Path,
    design: str = "wcw1",
    slugs: int = 4,
    verify: bool = True,
    mc_samples: int = 500_000,
    watertight: bool = False,
    step: bool = False,
    metrology: bool = False,
) -> dict:
    """Generate the full artifact directory for a spec. Returns a summary dict."""
    handlers = DESIGNS[design]
    warnings = spec.validate()
    for w in warnings:
        console_logger.warning("spec warning: %s", w)

    root = out_dir / spec.revision()
    for sub in ("mjcf", "urdf", "bom", "stl"):
        (root / sub).mkdir(parents=True, exist_ok=True)

    geom = handlers["build_geometry"](spec)
    configs = handlers["kit"](spec, slugs=slugs)
    targets = [handlers["resolve"](spec, cfg, geometry=geom) for cfg in configs]

    verify_map: dict[str, list] = {}
    if verify:
        from scenesmith.calibration.verify import verify_all

        for t in targets:
            if t.config.name in ("bare", "C0"):
                continue  # baseline shells: nothing beyond the shell to check
            verify_map[t.config.name] = verify_all(t, mc_samples=mc_samples)

    # Per-configuration assets.
    for t in targets:
        name = t.config.name
        (root / "mjcf" / f"{name}.xml").write_text(to_mjcf_string(t))
        (root / "mjcf" / f"{name}_scene.xml").write_text(
            to_mjcf_string(t, include_scene=True, freejoint=True)
        )
        (root / "urdf" / f"{name}.urdf").write_text(to_urdf_string(t))
        write_bom_csv(root / "bom" / f"{name}.csv", t)
        export_stl.write_primitive_soup(
            root / "stl" / f"{name}_preview.stl",
            t.all_primitives,
            segments=spec.triangulation_segments,
        )

    # Shared artifacts.
    write_fiducial_csv(root / "fiducials.csv", geom)
    (root / "spec.json").write_text(json.dumps(spec.to_dict(), indent=2, default=list))
    bundle = build_bundle(spec, targets, verify_map)
    write_bundle(root / "calibration_target.json", bundle)
    (root / "acceptance.md").write_text(acceptance_markdown(spec, targets, verify_map))
    blank_receipt(spec, design).to_json(root / "receipt_template.json")

    # Optional printable geometry.
    if watertight:
        ok = export_stl.write_watertight(root / "stl" / "shell_watertight.stl", geom)
        if not ok:
            console_logger.warning("watertight STL skipped (trimesh/manifold3d absent)")
    if step:
        from scenesmith.calibration import build123d_cad

        if build123d_cad.available() and design == "calbrick":
            build123d_cad.export_cad(
                spec, root / "shell.step", root / "stl" / "shell_cad.stl"
            )
        elif design != "calbrick":
            console_logger.warning("STEP export currently supports calbrick only")
        else:
            console_logger.warning("STEP export skipped (build123d absent)")
    if metrology:
        from scenesmith.calibration import metrology as metrology_mod

        written = metrology_mod.export_metrology(root / "metrology")
        if not written:
            console_logger.warning("metrology extras skipped (trimesh absent)")

    return {
        "root": root,
        "revision": spec.revision(),
        "warnings": warnings,
        "targets": targets,
        "verify_map": verify_map,
    }


def _print_summary(summary: dict) -> None:
    print(f"\nCalibration kit written to: {summary['root']}")
    print(f"Revision: {summary['revision']}")
    if summary["warnings"]:
        print("Spec warnings:")
        for w in summary["warnings"]:
            print(f"  - {w}")
    print(f"\n{'config':13s}{'mass(g)':>10s}{'CoM (mm)':>26s}   checks")
    for t in summary["targets"]:
        if t.config.name in ("bare", "C0"):
            continue
        com = t.com_mm
        checks = summary["verify_map"].get(t.config.name, [])
        status = (
            "  ".join(
                f"{r.method}:{'ok' if r.passed else 'FAIL'}"
                for r in checks
                if r.available
            )
            or "not run"
        )
        print(
            f"{t.config.name:13s}{t.mass_g:10.3f}"
            f"   [{com[0]:6.2f} {com[1]:6.2f} {com[2]:6.2f}]   {status}"
        )
    print()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--design",
        choices=sorted(DESIGNS),
        default="wcw1",
        help="Target design: wcw1 (ball cartridges, recommended) or calbrick.",
    )
    parser.add_argument("--out", type=Path, default=Path("dist/caltarget"))
    parser.add_argument("--slugs", type=int, default=4)
    parser.add_argument("--length-mm", dest="length_mm", type=float)
    parser.add_argument("--width-mm", dest="width_mm", type=float)
    parser.add_argument("--height-mm", dest="height_mm", type=float)
    parser.add_argument("--wall-mm", dest="wall_mm", type=float)
    parser.add_argument("--shell-material", dest="shell_material")
    parser.add_argument("--cartridge-material", dest="cartridge_material")
    parser.add_argument(
        "--measured-shell-g",
        type=float,
        default=None,
        help="Weighed bare-shell mass to fix effective density.",
    )
    parser.add_argument(
        "--measured-slug-g",
        type=float,
        default=None,
        help="Weighed per-slug mass for ground truth.",
    )
    parser.add_argument("--verify", action="store_true", default=True)
    parser.add_argument("--no-verify", dest="verify", action="store_false")
    parser.add_argument("--mc-samples", type=int, default=500_000)
    parser.add_argument(
        "--watertight",
        action="store_true",
        help="Also write a watertight STL (needs trimesh).",
    )
    parser.add_argument(
        "--step",
        action="store_true",
        help="Also write parametric STEP (needs build123d).",
    )
    parser.add_argument(
        "--metrology",
        action="store_true",
        help="Also write the D405 depth plate + grip gauge (needs trimesh).",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    spec = build_spec_from_args(args)
    summary = generate(
        spec,
        args.out,
        design=args.design,
        slugs=args.slugs,
        verify=args.verify,
        mc_samples=args.mc_samples,
        watertight=args.watertight,
        step=args.step,
        metrology=args.metrology,
    )
    _print_summary(summary)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

# Slice Brief 214 - T19.2a Printable Metric Calibration Target

**Date:** 2026-07-16

## Objective

Eliminate the missing-target artifact gap from Reviewer 283 by generating a
print-ready, dimensioned checkerboard target and a signed machine-readable
geometry contract. This is an offline artifact slice; physical printing,
placement, camera observation, and motion remain separate.

## Target contract

- US Letter portrait page at exact PDF points, intended for 100 percent / actual
  size printing with all scaling disabled.
- Ten columns by seven rows of exact 20.00 mm squares, yielding nine by six
  inner corners and a 200.00 x 140.00 mm active board.
- Top-left square black, deterministic row/column convention, exact page-space
  origin, a 100.00 mm verification bar, orientation labels, and instructions
  kept outside the active board.
- A signed JSON spec binds geometry, units, page size, generator identity, PDF
  SHA-256/size/page count, and print instructions.
- Regeneration and verification must reject page, geometry, scale, hash,
  orientation, count, path, or extra-field drift.

## Verification

Generate with ReportLab from tracked code, inspect with pypdf/pdfinfo, render
through Poppler, and visually inspect the PNG. Add deterministic unit tests and
run compilation, strict JSON, and diff checks.

## Authority withheld

The target's existence does not prove it was printed at scale, placed, visible,
or measured. It grants no camera/serial access, write, torque change, motion,
calibration result, twin update, physical qualification, transfer, policy,
external compute, or Brev authority.

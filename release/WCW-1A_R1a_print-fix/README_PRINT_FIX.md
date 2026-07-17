# WCW-1A R1a print-orientation fix

**What this is:** the 13 R1 STLs with their documented print orientations
actually baked into the geometry. Import any file and it lands on the bed in
the correct, support-free orientation at z=0, centered in XY. Print at 100%
scale with the same settings as before. These supersede both the R1 loose STLs
**and** the R1 Bambu 3MF plates for printing.

**What was wrong with R1** (reported by Zane, 2026-07-17, with screenshot —
see `docs/wcw-1a-print-correspondence/`): every R1 STL was exported in
body-frame coordinates. The filenames describe the intended print orientation
("exterior-face-down", "top-down", ...) but the rotation was never applied by
`wcw1a_cad.py`, and the 3MF plates carry identity rotations for every object,
despite the R1 docs claiming the plates were "already rotated". Consequences
as shipped:

| Part | As shipped (R1) | Correct (R1a) |
|---|---|---|
| Ball retainers (x5) | Standing on a 5.9 x 49.9 mm edge, ~24 mm tall | Flat, exterior face down, spring bosses up, 5.9 mm tall |
| Carriers (x5) | Lying on -z side, wells sideways | Closed -x face down, wells and rails vertical |
| Body | Open rim down; the closed top would bridge the full ~35 x 55 mm cavity at 65 mm height | Tag face down, open bottom up, no bridges |
| Bottom lid | Already correct by luck | Unchanged (outer face down) |
| Fit coupon | Already correct by luck | Unchanged (flat, labels up) |

**How the fix was made and verified:** `source/reorient_for_print.py`
(numpy + trimesh, runs anywhere) applies exactly the rotation each filename
declares — verified against the R1 geometry itself by cross-section (the
retainer's flat face is +x with bosses at -x; the carrier's closed face is -x;
the body's closed tag face is +z; the lid's outer face is -z). The transform
is rigid: triangle counts and volumes are bit-for-bit preserved (the script
aborts otherwise), so every R1 dimensional/mass validation still applies to
R1a. After reorientation every part was audited for bed contact and >45 deg
unsupported downward area: the retainers/body/carriers now show only the
design's intentional small features (45 deg well cones, 0.8 mm rail lips,
shallow recess bridges), matching the "no supports required" design intent.

**Printing:** follow `../WCW-1A_print_package/README_PRINTING.md` for
materials and settings (0.4 mm nozzle, 0.20 mm layers, 4 walls, 6 top/bottom,
100% rectilinear infill, no supports, 5 mm brim on the body only, 100% scale).
Slicer-agnostic: no plate files needed — import the STLs and arrange freely.

**Color note:** the AprilTags are printed paper labels applied after QC, so
body color does not affect tag contrast. Prefer matte, lighter colors for the
body (dark/black surfaces return weaker depth data to the D405); internal
carriers, retainers, and the lid can be any color. Steel grey for the body is
a good choice; black is fine for all internal parts.

**Provenance:** upstream fix for the next full CAD rebuild is to run
`source/reorient_for_print.py` as a post-export step (or port the same
transforms into `wcw1a_cad.py`'s `export_stl`); the Blender pipeline was not
re-run for R1a, so R1 geometry is untouched by construction. SHA-256 hashes
of the R1a files are in `MANIFEST.sha256`.

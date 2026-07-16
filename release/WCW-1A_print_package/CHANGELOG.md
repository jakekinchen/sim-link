# WCW-1A changelog

## WCW-1A-R1.1 batched packaging - 2026-07-16

- Added a standard-3MF 256 x 256 mm full-production plate containing all 12 cube parts in one job after the fit coupon.
- Added a conservative four-job 180 x 180 mm fallback: coupon, C1 fit pair, remaining hardware/lid, and body.
- Bound every named 3MF object to its source STL hash, verified support-free orientation, z=0 placement, object spacing, bed margins, XML/OPC structure, CRC, and triangle indices.
- Added five rendered top-view plate maps and explicit Bambu Studio printer-profile/slice-review instructions. Frozen part geometry and AprilTag artwork are unchanged.

## WCW-1A-R1 - 2026-07-16

- Replaced the historical WCW-1 exact-20.000-mm/G25 assumption with a parameterized 20.0 mm nominal ball plus 0.8 mm diametral FDM fit allowance and 19.8-20.2 mm expected ordinary-ball range.
- Replaced idealized sealed spherical voids with printable 45-degree conical seats, open vertical bores, and separate sliding spring retainers.
- Added a reversible keyed bottom lid, asymmetric cartridge key rail, hard stops, crush ribs, detents, and tactile C0-C4 retainer codes.
- Preserved body-frame y conditions: C0 empty, C1 0, C2 +15, C3 +/-11, C4 +/-15 mm. Corrected the simultaneous kit count to six balls.
- Preserved plain central 18 mm grasp bands and added unique top/+y/-y/+x/-x tag36h11 label definitions.
- Added 1:1 vector label PDF, high-resolution PNGs, placement diagram, fit coupon, renders, independent STL validation, mass/CoM estimates, docs, hashes, and verified ZIP packaging.

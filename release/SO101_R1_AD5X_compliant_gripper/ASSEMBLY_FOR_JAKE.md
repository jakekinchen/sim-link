# Assembly notes for Jake

Zane only needs to print and return the three loose parts.

The release contains two rigid PLA bases plus one TPU Fin-Ray finger. The
upstream design uses two additional M3 screws to fasten the TPU element to the
two bases. The upstream source does not freeze screw length; select the shortest
screw that achieves full thread engagement without bottoming or protruding.
Do not ask the printer to guess the length.

Before installing on the robot:

1. Compare every mounting hole and interface against the removed stock SO-101
   components without powering the arm.
2. Deburr only loose strings or elephant-foot flash; do not sand contact or
   mounting geometry to force a fit.
3. Confirm the TPU element seats symmetrically and moves without rubbing the
   wrist shell or camera.
4. Measure open/closed aperture, fingertip stand-off, and pad centerline.
5. Update the SimLink mesh/contact model and recalibrate gripper closure before
   any calibrated robot use.

Two M3 screws and optional 3M TB641 gripping material are owner-supplied and
are not part of this print package.

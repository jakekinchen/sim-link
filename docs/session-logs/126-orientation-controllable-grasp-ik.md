# Session 126 - Orientation-Controllable Grasp IK

**Date:** 2026-07-13

Brief 096 adds a grasp-specific solver that fixes wrist flex and wrist roll and
solves only shoulder pan/lift/elbow for position with joint limits and current-
configuration regularization. It rejects non-finite inputs, out-of-range wrists,
excess residual, requested-variable drift, and forbidden non-adjacent robot
self-contact.

Object yaw is written explicitly to the anchor free-joint quaternion and read
back independently from the body quaternion after forward kinematics. Four
candidates span wrist flex [-0.5, 0.5], wrist roll [-1.2, 1.2], and object yaw
[-0.6, 0.6] radians. All four pass before contact simulation with exact wrist
and yaw readback, no initial/final forbidden self-contact, and maximum position
residual 0.537937313 mm.

Artifact `cdcb2359...` retains requested/achieved pregrasp position, lateral and
vertical offsets, wrist values, object yaw, approach and closing axes, full
achieved gripper rotation, residual, and collision evidence. Ten focused tests
pass in each pinned runtime, the writer verifies exactly, and the final 176-test
broad gate passes. No contact search, grasp, hardware, inference, optimizer,
training, Brev, paid compute, or physical motion ran.

# Session 315 - RGB-Only Camera Census Implementation

**Date:** 2026-07-16
**Support task:** K3 / Brief 228

Implemented a camera-only central authority and one-use evidence path for the
owner-present D405 UVC plus C922 census. The path proves the active Codex
runtime before camera metadata enumeration, requires a reviewed origin-aligned
open gate, rejects missing or ambiguous target identities, preserves all
signed AVFoundation modes, selects a reviewed 640x480-or-better exact-30-fps
mode, and captures exactly one sequential RGB PNG per camera under a 600-second
ceiling.

Each PNG is retained privately and bound by an independently signed frame
record containing hash, size, dimensions, host monotonic receive interval, and
explicit null T20.22 fields for frame age, observation assembly, inference,
and action hold. The tracked manifest redacts camera unique IDs while retaining
public name/model, advertised configurations, selected mode, signed-frame
identity, coarse receive latency, and zero depth/serial/motion counts.

Adversarial coverage rejects closed or consumed gate state, remote drift,
expired owner window, wrong-thread runtime, path escape, re-signed depth
escalation, missing D405, unsupported modes, camera property writes, frame-byte
tampering, and private identity leakage. Both pinned robot runtimes pass 92
focused-plus-related tests. No camera or serial metadata was enumerated, no
device was opened, and no hardware action occurred during this implementation
boundary.

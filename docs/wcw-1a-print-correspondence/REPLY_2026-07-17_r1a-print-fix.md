# Outgoing reply — orientation fix + color answer (2026-07-17)

Response to Zane's 15:34 (filament color) and 16:12 (baked orientations)
messages. Send as iMessage; attach or email
`release/WCW-1A_R1a_print-fix.zip` (298 KB) to zane.cooke17@gmail.com.

The R1a package this reply references was produced and verified in
`release/WCW-1A_R1a_print-fix/` — see `README_PRINT_FIX.md` there for the
technical writeup.

---

## Message 1

> ok real jake this time lol. you were right about the orientations — i dug
> into it and the rotation never got baked into ANY of the files. the
> filenames say stuff like "exterior-face-down" but the meshes are all still
> in model coordinates, and the bambu plate files have the same bug even
> though the docs claim they're pre-rotated. so ignore the "keep the supplied
> orientations" thing entirely, that advice was based on files that were
> supposed to be rotated and weren't. good catch fr
>
> just emailed you a fixed zip (WCW-1A_R1a). every part now drops onto the
> bed the right way at z=0 — retainers lie flat with the bosses up, carriers
> sit on their closed face with the ball wells pointing up, body prints
> tag-face-down with the open end up. same geometry, same scale, just
> rotated, so anything you already printed after reorienting yourself is
> still perfectly good. no supports needed on anything once they're in these
> orientations — if your slicer still insists somewhere, just keep support
> contact off the ball wells and the two big flat gripper faces. skip the 3mf
> plates entirely, just import the stls and arrange however you like

## Message 2

> and steel grey is perfect for the body — honestly better than white for
> us, the depth camera hates dark surfaces so grey beats black there, and
> the apriltags are stickers that go on after printing so plastic color
> doesn't matter for tracking. black is totally fine for all the internal
> pieces (carriers, retainers, lid). so: grey body, black everything else,
> zero new filament needed 🙏

---

### Why this resolution

- Concedes the orientation bug with the actual root cause (bakes trust after
  the triple-send bot incident; Zane diagnosed it correctly and should hear
  that plainly).
- Nothing Zane already printed is wasted, and his manual reorientations are
  validated as correct — no reprint requests.
- Kills the two failure paths left open: the body (would have needed the
  whole cavity roof bridged) and the 3MF plates (same bug, "validated" docs
  notwithstanding).
- Answers the open color question with what he has on hand (steel grey +
  black), so nothing blocks the remaining prints.
- Keeps the only real constraints (100% scale, orientations, support-free,
  support keep-out zones) without re-listing settings he already confirmed.

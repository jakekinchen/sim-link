# Session Log 298 - T20.44 Stable Interpreter Correction

**Date:** 2026-07-16
**Task:** T20.44 / Brief 220

The first model-free materialization was held before commit because its valid
renderer smoke recorded an ephemeral `uv --with` interpreter that disappeared
after the command. No marker or model action occurred. The rejected artifacts
remain untracked pending bounded cleanup.

The correction binds stable `external/lerobot/.venv/bin/python` plus an existing
cached MuJoCo 3.3.5 support site-packages tree, requires that exact pair in
preflight/runner/mirror subprocesses, and forbids temporary uv build paths.
Spec `ec45331c...`, 22 focused/pointer tests, Ruff, formatting, compilation,
and direct stable-interpreter imports pass. Reviewer 295 opens only cleanup of
the newly created rejected artifacts followed by one stable rematerialization.

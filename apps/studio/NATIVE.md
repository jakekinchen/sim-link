# SceneSmith Studio Native Mac Shell

The Tauri 2 shell bundles the existing React control room and a fixed,
loopback-only PyInstaller sidecar for the existing FastAPI server. The webview
has only `core:default`; it receives no shell, filesystem, hardware, or generic
process capability. The sidecar exposes the same REST API and the same two
no-authority write actions as the browser stack.

## Build and run

Prerequisites: Bun, `uv`, Rust, and the Xcode command-line tools.

From `apps/studio/web`:

```sh
bun install
bun run native:dev
```

Build a macOS app bundle:

```sh
bun run native:build
```

The app bundle is written below `apps/studio/web/src-tauri/target/release/bundle/macos/`.
The build command applies a local ad-hoc signature and finishes with strict,
deep `codesign` verification; distribution signing and notarization remain a
separate release concern.
The backend remains bound to `127.0.0.1:8321` and reads `SIM_LINK_DATA_ROOT`,
defaulting to `/Users/kelly/Developer/sim-link` exactly like the web stack.

The sidecar build uses the server's locked `uv` environment and creates only
ignored build output below `apps/studio/web/src-tauri/`.

## Lifecycle diagnostics

The Event Ledger includes a native-backend strip when it runs inside Tauri. It
shows sidecar startup, ready, fault, and stopped states; the sidecar PID and
exit code; and a bounded stdout/stderr buffer. Port conflicts and early
backend exits are therefore visible in the app instead of appearing only as a
generic API-link failure.

The native command is read-only and returns at most 120 log entries with each
entry capped at 2,000 characters. These messages are explicitly operational
diagnostics, not repository evidence, and do not add shell, filesystem,
hardware, or process-control capability to the webview.

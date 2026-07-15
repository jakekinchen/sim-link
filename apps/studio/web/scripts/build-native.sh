#!/usr/bin/env bash
set -euo pipefail

WEB_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_BUNDLE="$WEB_DIR/src-tauri/target/release/bundle/macos/SceneSmith Studio.app"

cd "$WEB_DIR"
bun run native:bundle
codesign --force --deep --sign - --timestamp=none "$APP_BUNDLE"
codesign --verify --deep --strict --verbose=2 "$APP_BUNDLE"

#!/usr/bin/env bash
# Shared helpers for macOS packaging scripts.
# Source this from other scripts: . "$(dirname "$0")/lib.sh"

set -euo pipefail

# Repo root (scripts live in scripts/macos/)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Temp dir: use CI's RUNNER_TEMP when present, else a local mktemp dir.
TMP_DIR="${RUNNER_TEMP:-$(mktemp -d)}"

APP_PATH="${APP_PATH:-$REPO_ROOT/dist/jfather.app}"
DMG_PATH="${DMG_PATH:-$REPO_ROOT/dist/jfather-macos.dmg}"
ENTITLEMENTS="${ENTITLEMENTS:-$REPO_ROOT/packaging/entitlements.plist}"
ICNS="${ICNS:-$REPO_ROOT/jfather/resources/jfather.icns}"
KEYCHAIN_PATH="${KEYCHAIN_PATH:-$TMP_DIR/app-signing.keychain-db}"

log() { echo "==> $*"; }

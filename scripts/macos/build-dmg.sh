#!/usr/bin/env bash
# Build a distributable DMG with an /Applications drag target.
# Signs the DMG when MACOS_SIGN_IDENTITY is set. Notarization is handled
# separately by notarize.sh (call it on the resulting DMG).
#
# Env:
#   APP_PATH             path to .app (default dist/jfather.app)
#   DMG_PATH             output DMG (default dist/jfather-macos.dmg)
#   ICNS                 volume icon (optional)
#   MACOS_SIGN_IDENTITY  Developer ID Application identity (optional)
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

if [ ! -d "$APP_PATH" ]; then
  echo "ERROR: app bundle not found at $APP_PATH" >&2
  exit 1
fi

if ! command -v create-dmg >/dev/null 2>&1; then
  log "create-dmg not found -> installing via Homebrew"
  brew install create-dmg
fi

APP_NAME="$(basename "$APP_PATH")"
rm -f "$DMG_PATH"

VOLICON_ARGS=()
[ -f "$ICNS" ] && VOLICON_ARGS=(--volicon "$ICNS")

log "Creating DMG: $DMG_PATH"
create-dmg \
  --volname "jfather" \
  "${VOLICON_ARGS[@]}" \
  --window-pos 200 120 \
  --window-size 660 400 \
  --icon-size 100 \
  --icon "$APP_NAME" 165 175 \
  --hide-extension "$APP_NAME" \
  --app-drop-link 495 175 \
  "$DMG_PATH" "$APP_PATH"

if [ -n "${MACOS_SIGN_IDENTITY:-}" ]; then
  log "Signing DMG"
  codesign --force --sign "$MACOS_SIGN_IDENTITY" --timestamp "$DMG_PATH"
fi

log "DMG ready: $DMG_PATH"

#!/usr/bin/env bash
# Deep-sign the .app bundle.
#   - With MACOS_SIGN_IDENTITY: Developer ID sign + hardened runtime + entitlements.
#   - Without it: ad-hoc sign (prevents "damaged app", but Gatekeeper warning remains).
#
# Env:
#   MACOS_SIGN_IDENTITY  Developer ID Application identity (optional)
#   APP_PATH             path to .app (default dist/jfather.app)
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

if [ ! -d "$APP_PATH" ]; then
  echo "ERROR: app bundle not found at $APP_PATH" >&2
  exit 1
fi

if [ -n "${MACOS_SIGN_IDENTITY:-}" ]; then
  log "Signing with Developer ID: $MACOS_SIGN_IDENTITY"
  codesign --force --deep --options runtime --timestamp \
    --entitlements "$ENTITLEMENTS" \
    --sign "$MACOS_SIGN_IDENTITY" "$APP_PATH"
else
  log "No MACOS_SIGN_IDENTITY -> ad-hoc signing (Gatekeeper warning will remain)."
  codesign --force --deep --sign - "$APP_PATH"
fi

log "Verifying signature"
codesign --verify --deep --verbose=2 "$APP_PATH"

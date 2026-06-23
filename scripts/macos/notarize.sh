#!/usr/bin/env bash
# Notarize + staple a target (.app or .dmg).
# No-op when NOTARY_KEY is not set.
#
# Usage: notarize.sh <path-to-app-or-dmg>
#
# Env:
#   NOTARY_KEY        base64-encoded App Store Connect API key (.p8)
#   NOTARY_KEY_ID     key id
#   NOTARY_ISSUER_ID  issuer id
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

TARGET="${1:-$APP_PATH}"

if [ -z "${NOTARY_KEY:-}" ]; then
  log "NOTARY_KEY not set -> skipping notarization for $TARGET."
  exit 0
fi

if [ ! -e "$TARGET" ]; then
  echo "ERROR: notarization target not found: $TARGET" >&2
  exit 1
fi

KEY_PATH="$TMP_DIR/notary.p8"
if [ ! -f "$KEY_PATH" ]; then
  echo -n "$NOTARY_KEY" | base64 --decode -o "$KEY_PATH"
fi

case "$TARGET" in
  *.app)
    SUBMIT="$TMP_DIR/notarize.zip"
    log "Zipping app for submission"
    ditto -c -k --keepParent "$TARGET" "$SUBMIT"
    ;;
  *)
    SUBMIT="$TARGET"
    ;;
esac

log "Submitting to notary service (waits for result)"
xcrun notarytool submit "$SUBMIT" \
  --key "$KEY_PATH" --key-id "$NOTARY_KEY_ID" --issuer "$NOTARY_ISSUER_ID" \
  --wait

log "Stapling ticket to $TARGET"
xcrun stapler staple "$TARGET"

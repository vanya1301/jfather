#!/usr/bin/env bash
# Import a Developer ID certificate into a temporary keychain.
# No-op when MACOS_CERTIFICATE is not set (free / unsigned builds).
#
# Env:
#   MACOS_CERTIFICATE      base64-encoded .p12 (required to run)
#   MACOS_CERTIFICATE_PWD  .p12 password
#   KEYCHAIN_PWD           password for the temp keychain (any random string)
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

if [ -z "${MACOS_CERTIFICATE:-}" ]; then
  log "MACOS_CERTIFICATE not set -> skipping keychain import (build will be ad-hoc signed)."
  exit 0
fi

CERT_PATH="$TMP_DIR/cert.p12"
echo -n "$MACOS_CERTIFICATE" | base64 --decode -o "$CERT_PATH"

log "Creating temporary keychain: $KEYCHAIN_PATH"
security create-keychain -p "$KEYCHAIN_PWD" "$KEYCHAIN_PATH"
security set-keychain-settings -lut 21600 "$KEYCHAIN_PATH"
security unlock-keychain -p "$KEYCHAIN_PWD" "$KEYCHAIN_PATH"

log "Importing certificate"
security import "$CERT_PATH" -P "$MACOS_CERTIFICATE_PWD" -A -t cert -f pkcs12 -k "$KEYCHAIN_PATH"
security set-key-partition-list -S apple-tool:,apple: -k "$KEYCHAIN_PWD" "$KEYCHAIN_PATH"
security list-keychain -d user -s "$KEYCHAIN_PATH" login.keychain-db

log "Certificate imported."

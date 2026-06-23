#!/usr/bin/env bash
# Remove the temporary signing keychain. Safe to run always.
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

security delete-keychain "$KEYCHAIN_PATH" 2>/dev/null || true
log "Keychain cleanup done."

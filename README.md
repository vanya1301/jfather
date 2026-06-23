# jfather

A fast, modern desktop app to view and edit large JSON, with formatting,
escaping, tree visualization, search, and collection-query querying.

## Run

```bash
uv sync
uv run python main.py
```

## Install (macOS)

Download `jfather-macos.dmg` from the
[Releases](../../releases) page, open it, and drag **jfather** onto the
**Applications** folder.

If the build is **signed + notarized** (Developer ID secrets configured in CI),
it just opens — no warnings.

If it is **not notarized** (free/unsigned builds), macOS Gatekeeper shows
*"Apple could not verify…"* on first launch. Approve it once:

1. Try to open the app (the warning appears — click **Done**).
2. Open **System Settings → Privacy & Security**.
3. Scroll to the message about *jfather* and click **Open Anyway**.
4. Confirm. The app launches normally from then on.

To remove the warning entirely, the app must be notarized — see
[macOS signing & notarization](#macos-signing--notarization).

## Features

- Single warm **dark theme** with native scrollbars (no light/theme toggle).
- Grouped glyph **toolbar** (FILE / TRANSFORM / SETTINGS, with Close at the far
  right).
- Multiple documents via the left sidebar (with a distinct background and a
  bottom **+ New** button; New / Open / Close, dirty markers).
- Dual-pane: syntax-highlighted text editor with a **line-number gutter** +
  data viewer.
- Viewer shows a **table** for arrays of objects and a **tree** otherwise. The
  table is **sortable** and **resizable**, with monospace cells and JSON
  tooltips on nested cells.
- **Focus / drill-in**: double-click a node or table row to re-root the viewer
  and query scope; **breadcrumb pills** navigate back, with a drill-in hint at
  the root.
- Format, Minify, Escape, Unescape (selection-aware).
- **Query builder** with Structured (field / lookup / value dropdowns) and Text
  (tokens with autocomplete) modes; runs against the focused array (Run is
  disabled with a hint until the focused value is an array). Lists: `a,b,c`.
  Ranges: `lo..hi`.
  - Requires `collection-query>=0.2.0`. Supported lookups include `contains`,
    `startswith`, `endswith`, `in`, `in_range`, `lt`/`lte`/`gt`/`gte`, `not`,
    `exists`, `isnull`, `regex`, and case-insensitive variants (`icontains`,
    `istartswith`, `iendswith`, `iexact`, `iregex`).
  - Unknown lookups report a clear error in the results pane instead of
    silently returning nothing.
  - Per-row remove (**−**) / add (**＋**) controls, a **Copy** button for the
    results, and a result **count**; the status bar shows the match count after
    a query runs.
  - The structured **value** field suggests distinct values seen in the focused
    array for the chosen field (still accepts free text for lists/ranges).
  - Syntax-highlighted query **results**.

### Nested queries

Queries always run against the **focused array**, and you can reach into nested
data two ways:

- **Nested field paths** with `__` (double underscore). Segments are walked as
  dict keys; the last segment is a lookup only if it is a known lookup name.
  The field box is editable and also **suggests nested paths** (e.g.
  `address__city`, `address__geo__lat`):

  ```text
  address__city=Paris
  address__city__icontains=par
  address__geo__lat__gte=48
  ```

- **Drill-in scoping**: double-click a node or table row to re-root the viewer
  (and the query scope) onto a nested array, then query its items. Breadcrumb
  pills navigate back. For `{"users": [ … ]}`, drill into `users` to query the
  user objects.

Combining conditions: multiple **Filter** rows are AND-ed; **Exclude** rows
remove matches; there is no OR/grouped boolean logic — use `in` (e.g.
`status__in=active,pending`) or run separate queries for OR-like needs.
- In-editor **"Find in file…"** bar; data **search** across the active tree or
  table.
- Cross-platform shortcuts: Close (Ctrl/Cmd+W), Save (Ctrl/Cmd+S),
  Format (Ctrl/Cmd+Shift+F), Run query (Ctrl/Cmd+Return), Find (Ctrl/Cmd+F).

## Test

```bash
QT_QPA_PLATFORM=offscreen uv run pytest -v
```

## Building and Releasing

### Creating a Release

1. Tag the release:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. GitHub Actions will automatically:
   - Run tests on all platforms
   - Build a macOS `.app`, sign it, (optionally) notarize it, and package a DMG
   - Build the Linux executable
   - Create a GitHub Release with all assets

3. Users can download installers from the GitHub Releases page

### Manual Build

To build locally:

```bash
uv pip install pyinstaller
uv run pyinstaller jfather.spec
```

Executables will be in the `dist/` directory.

On macOS you can run the full packaging pipeline locally with the same scripts
CI uses (they no-op gracefully without signing secrets):

```bash
./scripts/macos/sign-app.sh      # ad-hoc sign (or Developer ID if env set)
./scripts/macos/build-dmg.sh     # produces dist/jfather-macos.dmg
```

### macOS signing & notarization

Signing/notarization logic lives in `scripts/macos/` so it is testable locally;
the CI workflow only invokes those scripts. The pipeline auto-detects whether
signing secrets are present:

- **No secrets** → app is **ad-hoc signed** + packaged as a DMG. Installs fine,
  but Gatekeeper shows a one-time warning (see [Install (macOS)](#install-macos)).
- **Secrets present** → app is **Developer ID signed**, **notarized**, and
  **stapled** → installs with **zero warnings**.

To enable full notarization (requires a paid Apple Developer account), add these
repository **Secrets**:

| Secret | Description |
| --- | --- |
| `MACOS_CERTIFICATE` | base64 of your Developer ID Application `.p12` |
| `MACOS_CERTIFICATE_PWD` | password for the `.p12` |
| `MACOS_SIGN_IDENTITY` | e.g. `Developer ID Application: Name (TEAMID)` |
| `KEYCHAIN_PWD` | any random string (temp keychain password) |
| `NOTARY_KEY` | base64 of your App Store Connect API key `.p8` |
| `NOTARY_KEY_ID` | the API key ID |
| `NOTARY_ISSUER_ID` | the App Store Connect issuer ID |

No workflow edits are needed when adding the account later — just set the
secrets and the same pipeline switches to the signed + notarized path.

### Update Mechanism

The app automatically checks for updates on startup (once per hour). Users can also manually check via Help > Check for Updates...

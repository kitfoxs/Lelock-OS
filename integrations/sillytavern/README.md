# Lelock OS — experimental SillyTavern extension

This is the **Lelock-maintained** UI extension, not an official SillyTavern distribution.
It contains code for recalled context, proposed workspace files with human controls,
and card/lore sync. Import-path repairs do not certify the daemon or those workflows.

**Blocked for end-to-end use:** the public launch omitted the current Python package,
including the bridge implementation. Recover and review it first. In particular, verify
loopback binding, authentication/approved origins, memory-consent enforcement, exact
one-time approval, and character/scope isolation before connecting personal data.
Loopback binding alone is not authentication or browser-origin protection.

## Install the extension subdirectory — not the repository root

The monorepo root has no SillyTavern extension manifest. Do **not** paste the whole
Lelock repository into the one-click extension installer and expect it to locate
`integrations/sillytavern/` automatically.

For local development, with SillyTavern stopped, copy **the contents of this directory**
into a new directory named `lelock-os` at:

```text
<SillyTavern>/public/scripts/extensions/third-party/lelock-os/
    manifest.json
    index.js
    settings.html
    style.css
    README.md
```

Alternatively, after checking that the destination does not already exist, use a
symlink (replace the two absolute paths with your actual checkouts):

```sh
mkdir -p /absolute/path/SillyTavern/public/scripts/extensions/third-party
ln -s /absolute/path/Lelock-OS/integrations/sillytavern \
  /absolute/path/SillyTavern/public/scripts/extensions/third-party/lelock-os
```

Do not use `ln -sf` or overwrite an existing installation. Keep the folder name
`lelock-os`, which the settings-template path expects. Per-user extensions are another
SillyTavern option; whichever storage location is used, the browser serves third-party
extensions under `/scripts/extensions/third-party/`.

The repaired imports resolve from that URL to `/scripts/extensions.js`, `/script.js`,
and the corresponding `/scripts/` tool/slash-command modules. The supplied 1.19.0 source
was used for static path/export checks, not a live compatibility certification.

## Verification before first use

1. Reload SillyTavern and inspect the browser console/network panel. The module and
   `settings.html` must load, and the activation hook must render one settings panel.
2. With a recovered, audited **synthetic** Lelock home, check the actual
   `./project/lelock serve --help` interface and run the loopback service as documented
   by its code. Do not expose it to the Internet or treat a green badge as a security audit.
3. Exercise one recall, one card sync, and one new-file proposal: inspect the exact content,
   reject it and verify no write, then approve a separate proposal and read back its bytes.
4. Verify refused paths, replayed approvals, malformed requests, memory failures, and
   cross-character memory isolation. Record the actual versions and results.

The extension currently sends HTTP/JSON requests to the configured daemon and relies
on its response contract. That contract must be verified against recovered backend code;
no authentication scheme or server behavior was guessed in this repair.

Official extension-layout reference:
https://docs.sillytavern.app/for-contributors/writing-extensions/

#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$HERE/../.."
# The reviewed Rakazo checkout must already have its pinned dependencies installed.
# Do not use npx to fetch a different tool on each launch.
exec pnpm exec tsx integrations/lelock-v03/entry.mjs

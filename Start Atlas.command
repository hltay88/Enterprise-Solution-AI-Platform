#!/bin/bash
# Double-click this file in Finder (or drag it to the Dock) to start Project Atlas.
# First run may ask macOS to allow Terminal to run the script — click OK / Open.

set -euo pipefail
cd "$(dirname "$0")"
chmod +x start-atlas.sh stop-atlas.sh 2>/dev/null || true
./start-atlas.sh
echo
echo "Press Return to close this window..."
read -r _

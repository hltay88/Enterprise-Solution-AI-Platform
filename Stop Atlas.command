#!/bin/bash
# Double-click this file in Finder (or drag it to the Dock) to stop Project Atlas.

set -euo pipefail
cd "$(dirname "$0")"
chmod +x start-atlas.sh stop-atlas.sh 2>/dev/null || true
./stop-atlas.sh
echo
echo "Press Return to close this window..."
read -r _

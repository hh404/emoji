#!/bin/zsh
set -euo pipefail

workflow_dir=${0:A:h}
exec /usr/bin/python3 "$workflow_dir/scripts/search_emoji.py" "${1:-}"

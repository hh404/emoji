#!/bin/zsh
set -euo pipefail

root_dir=${0:A:h}
output_path="$root_dir/Emoji-Search.alfredworkflow"

cd "$root_dir"
zip -qryFS "$output_path" info.plist README.md run-search.sh scripts resources -x '*/__pycache__/*'
print "Created $output_path"

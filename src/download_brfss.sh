#!/usr/bin/env bash
# Download BRFSS annual SAS transport files from CDC into data/raw/.
set -euo pipefail
cd "$(dirname "$0")/../data/raw"
base=https://www.cdc.gov/brfss/annual_data
declare -A files=(
  [2006]=CDBRFS06XPT.zip [2007]=CDBRFS07XPT.zip [2008]=CDBRFS08XPT.zip [2009]=CDBRFS09XPT.zip
  [2022]=LLCP2022XPT.zip [2023]=LLCP2023XPT.zip [2024]=LLCP2024XPT.zip [2025]=LLCP2025XPT.zip
)
for y in "${!files[@]}"; do
  f=${files[$y]}
  [ -f "$f" ] || curl -sS --retry 4 -o "$f" "$base/$y/files/$f"
  unzip -o -q "$f"
done
ls -la

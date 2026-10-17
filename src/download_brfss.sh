#!/usr/bin/env bash
# Download BRFSS annual SAS transport files from CDC into data/raw/.
set -euo pipefail
cd "$(dirname "$0")/../data/raw"
base=https://www.cdc.gov/brfss/annual_data
declare -A files=(
  [2006]=CDBRFS06XPT.zip [2007]=CDBRFS07XPT.zip [2008]=CDBRFS08XPT.zip [2009]=CDBRFS09XPT.zip
  [2010]=CDBRFS10XPT.zip [2011]=LLCP2011XPT.ZIP [2012]=LLCP2012XPT.ZIP [2013]=LLCP2013XPT.ZIP
  [2014]=LLCP2014XPT.ZIP [2015]=LLCP2015XPT.zip [2016]=LLCP2016XPT.zip
  [2022]=LLCP2022XPT.zip [2023]=LLCP2023XPT.zip [2024]=LLCP2024XPT.zip [2025]=LLCP2025XPT.zip
)
for y in "${!files[@]}"; do
  f=${files[$y]}
  [ -f "$f" ] || curl -sS --retry 4 -o "$f" "$base/$y/files/$f"
  unzip -o -q "$f"
done
for f in *.XPT\ ; do [ -e "$f" ] && mv "$f" "${f% }"; done  # some CDC files carry a trailing space
ls -la

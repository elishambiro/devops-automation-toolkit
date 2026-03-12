#!/bin/bash
# find_large_files.sh
# Finds files larger than a given size threshold under a directory.
# Usage: ./find_large_files.sh --dir /var --min-size 100M --top 20

set -euo pipefail

SEARCH_DIR="."
MIN_SIZE="100M"
TOP_N=20
EXCLUDE_DIRS=("/proc" "/sys" "/dev")

while [[ $# -gt 0 ]]; do
  case $1 in
    --dir)      SEARCH_DIR="$2"; shift 2 ;;
    --min-size) MIN_SIZE="$2";   shift 2 ;;
    --top)      TOP_N="$2";      shift 2 ;;
    *) shift ;;
  esac
done

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "========================================"
echo "  Large File Finder"
echo "  Directory: $SEARCH_DIR"
echo "  Min size:  $MIN_SIZE"
echo "  Top:       $TOP_N results"
echo "========================================"
echo ""

# Build exclude args
EXCLUDE_ARGS=()
for dir in "${EXCLUDE_DIRS[@]}"; do
  EXCLUDE_ARGS+=(-not -path "${dir}/*")
done

echo -e "${YELLOW}Scanning... (this may take a moment)${NC}"
echo ""

printf "%-15s %-60s\n" "SIZE" "PATH"
echo "$(printf '─%.0s' {1..75})"

find "$SEARCH_DIR" -type f "${EXCLUDE_ARGS[@]}" -size +"$MIN_SIZE" \
  -printf "%s\t%p\n" 2>/dev/null \
  | sort -rn \
  | head -n "$TOP_N" \
  | awk '{
      size=$1
      path=$2
      if (size >= 1073741824)      printf "%-15s %s\n", sprintf("%.1f GB", size/1073741824), path
      else if (size >= 1048576)    printf "%-15s %s\n", sprintf("%.1f MB", size/1048576), path
      else                         printf "%-15s %s\n", sprintf("%.1f KB", size/1024), path
    }'

echo ""
TOTAL=$(find "$SEARCH_DIR" -type f "${EXCLUDE_ARGS[@]}" -size +"$MIN_SIZE" 2>/dev/null | wc -l)
echo -e "${GREEN}Total files larger than $MIN_SIZE: $TOTAL${NC}"

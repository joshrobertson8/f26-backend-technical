#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -gt 1 ]; then
    echo "Usage: ./setup/setup.sh [option]" >&2
    exit 2
fi

case "${1:-}" in
    ""|python-fastapi|javascript-express|typescript-express|javascript-nextjs|typescript-nextjs|java-spring-boot|c) ;;
    -h|--help)
        echo "Run ./setup/setup.sh to choose a language from the menu."
        echo "Options: python-fastapi, javascript-express, typescript-express, javascript-nextjs, typescript-nextjs, java-spring-boot, c"
        exit 0
        ;;
    *)
        echo "Unknown option. Run ./setup/setup.sh to choose from the menu." >&2
        exit 2
        ;;
esac

SETUP="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "$SETUP/.." && pwd)"
TOOLS="$SETUP/.tools"
mkdir -p "$TOOLS"

PYTHON=""
for candidate in python3.12 python3.13 python3.11 python3.10 python3.9 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        if "$candidate" -c 'import sys; sys.exit(0 if (3, 9) <= sys.version_info[:2] < (3, 14) else 1)' 2>/dev/null; then
            PYTHON="$(command -v "$candidate")"
            break
        fi
    fi
done


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


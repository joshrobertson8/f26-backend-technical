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

if [ -z "$PYTHON" ]; then
    if ! command -v curl >/dev/null 2>&1 && ! command -v wget >/dev/null 2>&1; then
        SUDO=()
        if [ "$(id -u)" -ne 0 ]; then
            if ! command -v sudo >/dev/null 2>&1; then
                echo "Installing tools needs administrator access. Install sudo or ask an administrator to help." >&2
                exit 1
            fi
            SUDO=(sudo)
        fi

        if command -v apt-get >/dev/null 2>&1; then
            "${SUDO[@]}" apt-get update
            "${SUDO[@]}" apt-get install -y curl ca-certificates
        elif command -v dnf >/dev/null 2>&1; then
            "${SUDO[@]}" dnf install -y curl ca-certificates
        elif command -v yum >/dev/null 2>&1; then
            "${SUDO[@]}" yum install -y curl ca-certificates
        elif command -v pacman >/dev/null 2>&1; then
            "${SUDO[@]}" pacman -S --needed --noconfirm curl ca-certificates
        elif command -v zypper >/dev/null 2>&1; then
            "${SUDO[@]}" zypper --non-interactive install curl ca-certificates
        elif command -v apk >/dev/null 2>&1; then
            "${SUDO[@]}" apk add --no-cache curl ca-certificates
        else
            echo "Could not install curl. Install curl or wget, then rerun setup." >&2
            exit 1
        fi
    fi

    export UV_INSTALL_DIR="$TOOLS/uv"
    export UV_NO_MODIFY_PATH=1
    export UV_PYTHON_INSTALL_DIR="$TOOLS/python"
    export UV_PYTHON_BIN_DIR="$TOOLS/bin"
    export PATH="$UV_PYTHON_BIN_DIR:$PATH"


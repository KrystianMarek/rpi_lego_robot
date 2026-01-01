#!/usr/bin/env bash
# K.O.C Robot - Client Setup Script
#
# Sets up the desktop client environment for running the GUI controller.
# Supports Linux, macOS, and Windows (via WSL or Git Bash).
#
# Usage:
#   ./scripts/setup-client.sh
#
# After setup:
#   source .venv/bin/activate
#   python gui.py

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

main() {
    log_info "K.O.C Robot - Client Setup"
    print_env_info

    # Check platform
    local platform
    platform=$(detect_platform)

    if [[ "$platform" == "arm32" ]] || [[ "$platform" == "arm64" ]]; then
        log_warn "Running on ARM - this script is intended for desktop clients"
        log_warn "For Raspberry Pi server setup, use: ./scripts/setup-server.sh"
        read -p "Continue anyway? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    # Install uv
    install_uv

    # Setup virtual environment
    # Use Python 3.14 (latest) - uv will download if not available
    setup_venv "3.14"

    # Activate venv
    activate_venv

    # Install Python dependencies
    log_info "Installing Python dependencies..."
    uv pip install -r "$PROJECT_ROOT/requirements/client.txt"

    log_info ""
    log_info "=== Client Setup Complete ==="
    log_info ""
    log_info "To activate the environment:"
    log_info "  source .venv/bin/activate"
    log_info ""
    log_info "To start the GUI:"
    log_info "  python gui.py"
    log_info ""
    log_info "To set robot IP (optional):"
    log_info "  export ROBOT_IP=192.168.10.187"
    log_info "  # Or create .env file with: ROBOT_IP=192.168.10.187"
    log_info ""
}

main "$@"


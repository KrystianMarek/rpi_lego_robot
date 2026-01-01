#!/usr/bin/env bash
# K.O.C Robot - Common Setup Functions
# Source this file from setup-client.sh and setup-server.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project root (relative to scripts/ directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect platform: x86_64, armv7l, aarch64
detect_platform() {
    local arch
    arch=$(uname -m)
    case "$arch" in
        x86_64)
            echo "x86_64"
            ;;
        armv7l|armv6l)
            echo "arm32"
            ;;
        aarch64|arm64)
            echo "arm64"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# Check if running on Raspberry Pi
is_raspberry_pi() {
    if [[ -f /proc/device-tree/model ]]; then
        grep -qi "raspberry" /proc/device-tree/model 2>/dev/null && return 0
    fi
    return 1
}

# Install uv (ultra-fast Python package manager)
install_uv() {
    if command -v uv &>/dev/null; then
        log_info "uv is already installed: $(uv --version)"
        return 0
    fi

    log_info "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Add to PATH for current session
    export PATH="$HOME/.local/bin:$PATH"

    if command -v uv &>/dev/null; then
        log_info "uv installed successfully: $(uv --version)"
    else
        log_error "Failed to install uv"
        return 1
    fi
}

# Setup Python virtual environment using uv
setup_venv() {
    local python_version="${1:-3.14}"
    local venv_path="${PROJECT_ROOT}/.venv"

    if [[ -d "$venv_path" ]]; then
        log_info "Virtual environment already exists at $venv_path"
        return 0
    fi

    log_info "Setting up Python $python_version via uv..."

    # uv can download and install Python versions automatically
    # This works even if the version isn't installed on the system
    if ! uv python list 2>/dev/null | grep -q "$python_version"; then
        log_info "Downloading Python $python_version..."
        uv python install "$python_version" || {
            log_warn "Failed to install Python $python_version, trying system Python"
            uv venv "$venv_path"
            log_info "Virtual environment created with system Python"
            return 0
        }
    fi

    log_info "Creating virtual environment with Python $python_version..."
    uv venv "$venv_path" --python "$python_version"

    log_info "Virtual environment created at $venv_path"
}

# Activate virtual environment
activate_venv() {
    local venv_path="${PROJECT_ROOT}/.venv"

    if [[ ! -d "$venv_path" ]]; then
        log_error "Virtual environment not found. Run setup script first."
        return 1
    fi

    # shellcheck disable=SC1091
    source "$venv_path/bin/activate"
    log_info "Virtual environment activated"
}

# Initialize git submodules
init_submodules() {
    cd "$PROJECT_ROOT"

    log_info "Initializing git submodules..."
    git submodule init
    git submodule update

    log_info "Submodules initialized"
}

# Fix Raspbian Stretch APT sources (deprecated)
fix_apt_sources_stretch() {
    if ! grep -qi "stretch" /etc/os-release 2>/dev/null; then
        return 0  # Not Stretch, skip
    fi

    log_warn "Raspbian Stretch detected - APT sources may need updating"
    log_warn "Stretch reached end-of-life. Consider upgrading to Bullseye/Bookworm."

    local sources_list="/etc/apt/sources.list"

    if grep -q "archive.debian.org" "$sources_list"; then
        log_info "APT sources already updated to use archive"
        return 0
    fi

    log_info "Updating APT sources to use Debian archive..."

    # Backup original
    sudo cp "$sources_list" "${sources_list}.backup.$(date +%Y%m%d)"

    # Update to archive mirrors
    sudo tee "$sources_list" > /dev/null << 'EOF'
# Debian Archive - Stretch (EOL)
# These are archive mirrors for the deprecated Stretch release
deb http://archive.debian.org/debian stretch main contrib non-free
deb http://archive.debian.org/debian-security stretch/updates main contrib non-free

# Raspberry Pi archive
deb http://legacy.raspbian.org/raspbian/ stretch main contrib non-free rpi
EOF

    # Disable signature checking for archived repos (they're not updated)
    sudo tee /etc/apt/apt.conf.d/99no-check-valid-until > /dev/null << 'EOF'
Acquire::Check-Valid-Until "false";
EOF

    log_info "APT sources updated. Running apt-get update..."
    sudo apt-get update
}

# Get Python version string (e.g., "3.11")
python_version() {
    python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
}

# Copy udev rules for hardware access
install_udev_rules() {
    log_info "Installing udev rules..."

    local rules_dir="/etc/udev/rules.d"

    # Kinect
    if [[ -f "${PROJECT_ROOT}/dependencies/66-kinect.rules" ]]; then
        sudo cp "${PROJECT_ROOT}/dependencies/66-kinect.rules" "${rules_dir}/"
        log_info "Installed Kinect udev rules"
    fi

    # I2C
    if [[ -f "${PROJECT_ROOT}/dependencies/55-i2c.rules" ]]; then
        sudo cp "${PROJECT_ROOT}/dependencies/55-i2c.rules" "${rules_dir}/"
        log_info "Installed I2C udev rules"
    fi

    # NCS (Movidius)
    if [[ -f "${PROJECT_ROOT}/dependencies/ncsdk/api/src/97-usbboot.rules" ]]; then
        sudo cp "${PROJECT_ROOT}/dependencies/ncsdk/api/src/97-usbboot.rules" "${rules_dir}/"
        log_info "Installed NCS udev rules"
    fi

    # Reload udev rules
    sudo udevadm control --reload-rules
    sudo udevadm trigger

    log_info "udev rules installed and reloaded"
}

# Print environment info
print_env_info() {
    echo ""
    echo "=== Environment Information ==="
    echo "Platform: $(detect_platform)"
    echo "Raspberry Pi: $(is_raspberry_pi && echo 'Yes' || echo 'No')"
    echo "Python: $(python3 --version 2>/dev/null || echo 'Not found')"
    echo "uv: $(uv --version 2>/dev/null || echo 'Not installed')"
    echo "Project root: $PROJECT_ROOT"
    echo "==============================="
    echo ""
}


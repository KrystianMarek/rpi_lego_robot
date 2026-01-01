#!/usr/bin/env bash
# K.O.C Robot - Server Setup Script
#
# Sets up the Raspberry Pi server environment with all dependencies:
# - System packages (OpenCV, libusb, etc.)
# - Python packages (via uv)
# - BrickPi driver (from submodule)
# - libfreenect/Kinect driver (from submodule)
# - Intel NCS SDK (from submodule, legacy device)
#
# Usage:
#   ./scripts/setup-server.sh
#
# After setup:
#   source .venv/bin/activate
#   python server.py

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

# Install system dependencies via apt
install_system_dependencies() {
    log_info "Installing system dependencies..."

    # Fix APT sources if on Stretch
    fix_apt_sources_stretch

    sudo apt-get update

    # Build essentials
    sudo apt-get install -y build-essential cmake git pkg-config

    # OpenCV dependencies
    sudo apt-get install -y \
        libgtk2.0-dev \
        libavcodec-dev \
        libavformat-dev \
        libswscale-dev \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libdc1394-22-dev \
        libtbb2 \
        libtbb-dev

    # Python development headers
    sudo apt-get install -y python3-dev python3-numpy

    # Kinect / USB dependencies
    sudo apt-get install -y libusb-1.0-0-dev cython3

    # NCS dependencies
    sudo apt-get install -y libudev-dev

    log_info "System dependencies installed"
}

# Install OpenCV (for ARM, build from source; for x86, use pip)
install_opencv() {
    local platform
    platform=$(detect_platform)

    if [[ "$platform" == "x86_64" ]]; then
        log_info "Using pre-built OpenCV from pip..."
        uv pip install opencv-python
        return 0
    fi

    # On ARM, we may need to build from source or use system package
    log_info "On ARM platform - checking for OpenCV..."

    # Try system package first (much faster)
    if sudo apt-get install -y python3-opencv 2>/dev/null; then
        log_info "Installed OpenCV from system packages"
        return 0
    fi

    log_warn "Building OpenCV from source (this will take a while)..."

    local build_dir="${PROJECT_ROOT}/tmp/opencv_build"
    mkdir -p "$build_dir"
    cd "$build_dir"

    # Download OpenCV 3.4.x (compatible with older systems)
    if [[ ! -f "opencv.zip" ]]; then
        curl -L https://github.com/opencv/opencv/archive/3.4.3.zip -o opencv.zip
        unzip opencv.zip
    fi

    cd opencv-3.4.3
    mkdir -p build
    cd build

    cmake -D CMAKE_BUILD_TYPE=RELEASE \
          -D CMAKE_INSTALL_PREFIX=/usr/local \
          -D INSTALL_PYTHON_EXAMPLES=OFF \
          -D BUILD_EXAMPLES=OFF ..

    # Increase swap for build (RPi has limited RAM)
    log_info "Increasing swap for build..."
    sudo sed -i 's/CONF_SWAPSIZE=100/CONF_SWAPSIZE=1024/g' /etc/dphys-swapfile
    sudo /etc/init.d/dphys-swapfile restart

    make -j$(nproc)
    sudo make install

    # Restore swap
    sudo sed -i 's/CONF_SWAPSIZE=1024/CONF_SWAPSIZE=100/g' /etc/dphys-swapfile
    sudo /etc/init.d/dphys-swapfile restart

    cd "$PROJECT_ROOT"
    log_info "OpenCV installed from source"
}

# Install BrickPi driver from submodule
install_brickpi() {
    log_info "Installing BrickPi driver..."

    local brickpi_path="${PROJECT_ROOT}/dependencies/BrickPi/Software/BrickPi_Python"

    if [[ ! -d "$brickpi_path" ]]; then
        log_error "BrickPi submodule not found. Run: git submodule update --init"
        return 1
    fi

    # Hack for Raspberry Pi 3 serial port
    sed -i 's/ttyAMA0/ttyS0/g' "$brickpi_path/BrickPi.py"

    uv pip install "$brickpi_path"

    log_info "BrickPi driver installed"
}

# Install libfreenect (Kinect driver) from submodule
install_libfreenect() {
    log_info "Installing libfreenect (Kinect driver)..."

    local freenect_path="${PROJECT_ROOT}/dependencies/libfreenect"

    if [[ ! -d "$freenect_path" ]]; then
        log_error "libfreenect submodule not found. Run: git submodule update --init"
        return 1
    fi

    cd "$freenect_path"
    mkdir -p build
    cd build

    cmake -D BUILD_PYTHON3=ON -D BUILD_CV=ON ..
    make -j$(nproc)
    sudo make install

    # Link freenect to venv
    local venv_site_packages
    venv_site_packages=$("${PROJECT_ROOT}/.venv/bin/python" -c "import site; print(site.getsitepackages()[0])")
    local system_freenect="/usr/local/lib/python3/dist-packages/freenect.so"

    if [[ -f "$system_freenect" ]]; then
        ln -sf "$system_freenect" "$venv_site_packages/freenect.so"
    fi

    cd "$PROJECT_ROOT"
    log_info "libfreenect installed"
}

# Install Intel NCS SDK from submodule
install_ncsdk() {
    log_info "Installing Intel NCS SDK (legacy device)..."

    local ncsdk_path="${PROJECT_ROOT}/dependencies/ncsdk"

    if [[ ! -d "$ncsdk_path" ]]; then
        log_error "NCSDK submodule not found. Run: git submodule update --init"
        return 1
    fi

    # The install.sh script handles the full installation
    # URL has been patched to use working mirror
    cd "$ncsdk_path"

    log_info "Running NCSDK install script..."
    log_warn "This downloads firmware from mirror: https://downloads.bl4ckb0x.de/..."

    ./install.sh

    cd "$PROJECT_ROOT"
    log_info "NCS SDK installed"
}

main() {
    log_info "K.O.C Robot - Server Setup (Raspberry Pi)"
    print_env_info

    # Warn if not on ARM
    local platform
    platform=$(detect_platform)

    if [[ "$platform" == "x86_64" ]]; then
        log_warn "Not running on ARM - this script is intended for Raspberry Pi"
        read -p "Continue anyway? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    # Initialize git submodules
    init_submodules

    # Install system dependencies
    install_system_dependencies

    # Install uv
    install_uv

    # Setup virtual environment
    # Use Python 3.11 for RPi - balance of features vs native library compatibility
    # Note: Native libs (libfreenect, BrickPi) may have issues with 3.14
    setup_venv "3.11"

    # Activate venv
    activate_venv

    # Install Python dependencies
    log_info "Installing Python dependencies..."
    uv pip install -r "$PROJECT_ROOT/requirements/server.txt"

    # Install native dependencies
    install_opencv
    install_brickpi
    install_libfreenect

    # Install NCS SDK (optional, may fail if no device)
    if lsusb | grep -q "03e7:2150"; then
        log_info "NCS device detected, installing SDK..."
        install_ncsdk
    else
        log_warn "No NCS device detected, skipping SDK installation"
        log_warn "To install later: cd dependencies/ncsdk && ./install.sh"
    fi

    # Install udev rules
    install_udev_rules

    log_info ""
    log_info "=== Server Setup Complete ==="
    log_info ""
    log_info "To activate the environment:"
    log_info "  source .venv/bin/activate"
    log_info ""
    log_info "To start the server:"
    log_info "  python server.py"
    log_info ""
    log_info "To verify hardware:"
    log_info "  lsusb                    # Check USB devices"
    log_info "  python -c 'import freenect; print(\"Kinect OK\")'  # Test Kinect"
    log_info "  python -c 'import BrickPi; print(\"BrickPi OK\")'  # Test BrickPi"
    log_info ""
}

main "$@"


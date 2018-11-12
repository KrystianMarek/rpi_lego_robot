#!/usr/bin/env bash
set -e

install_system_dependencies () {

    sudo apt-get update && sudo apt-get -y upgrade

    # opencv
    sudo apt-get install -y build-essential
    sudo apt-get install -y cmake git libgtk2.0-dev pkg-config libavcodec-dev libavformat-dev libswscale-dev
    sudo apt-get install -y python-dev python3-dev python-numpy python3-numpy libtbb2 libtbb-dev libjpeg-dev libpng-dev libtiff-dev libdc1394-22-dev

    # kinect
    sudo apt-get install -y libusb-1.0-0-dev cython cython3
    sudo cp dependencies/66-kinect.rules /etc/udev/rules.d/66-kinect.rules

    # i2c
    sudo cp dependencies/55-i2c.rules /etc/udev/rules.d/55-i2c.rules
}

# https://www.pyimagesearch.com/2017/09/04/raspbian-stretch-install-opencv-3-python-on-your-raspberry-pi/
install_opencv () {
    base_dir=$1
    site_packages_dir=$2

    cd ${base_dir}

    mkdir -p tmp
    cd tmp
    curl -L https://github.com/opencv/opencv/archive/3.4.3.zip -o opencv.zip
    unzip opencv.zip
    cd opencv-3.4.3
    mkdir build
    cd build
    cmake -D CMAKE_BUILD_TYPE=RELEASE \
    -D CMAKE_INSTALL_PREFIX=/usr/local \
    -D INSTALL_PYTHON_EXAMPLES=ON \
    -D BUILD_EXAMPLES=ON ..

    sudo sed -i 's/CONF_SWAPSIZE=100/CONF_SWAPSIZE=1024/g' /etc/dphys-swapfile
    sudo /etc/init.d/dphys-swapfile stop
    sudo /etc/init.d/dphys-swapfile start

    make -j4

    sudo make install

    ln -s /usr/local/lib/python$(python_version)/site-packages/cv2*.so ${site_packages_dir}/cv2.so

    cd ${base_dir}
}

python_version () {
    python -V | cut -d ' ' -f 2 |cut -d '.' -f 1,2
}

install_brickpi () {
    # Hack BrickPi code to work with reaspberry pi3
    #cd ${base_dir}/dependencies/BrickPi/Software/BrickPi_Python
    sed -i 's/ttyAMA0/ttyS0/g' dependencies/BrickPi/Software/BrickPi_Python/BrickPi.py
    #python setup.py install
    pip install dependencies/BrickPi/Software/BrickPi_Python/
}

install_libfreenect () {
    base_dir=$1
    site_packages_dir=$2

    cd ${base_dir}/dependencies/libfreenect
    mkdir -p build
    cd build
    cmake -D BUILD_PYTHON3=ON -D BUILD_CV=ON ..
    make -j4
    sudo make install
    cd ${base_dir}

    ln -s /usr/local/lib/python$(python_version)/site-packages/freenect.so ${site_packages_dir}/freenect.so
}

main () {
    base_dir=$(realpath ./)
    site_packages_dir=$1

    git submodule init
    git submodule update

    pip install numpy smbus2 pyzmq pyaml netifaces

    install_system_dependencies

    if [ $(uname -p) = "x86_64" ]; then
        sudo apt-get install -y libopencv-dev
        pip install opencv-python pyqt5
    else
        install_opencv ${base_dir} ${site_packages_dir}
    fi

    install_brickpi

    install_libfreenect ${base_dir} ${site_packages_dir}
}

main $1
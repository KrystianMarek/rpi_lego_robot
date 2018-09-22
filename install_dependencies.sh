#!/usr/bin/env bash

install_system_dependencies () {

    sudo apt-get update && sudo apt-get -y upgrade

    # opencv
    sudo apt-get install -y build-essential cmake pkg-config unzip curl
    sudo apt-get install -y libjpeg-dev libtiff5-dev libjasper-dev libpng12-dev
    sudo apt-get install -y libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
    sudo apt-get install -y libxvidcore-dev libx264-dev
    sudo apt-get install -y libgtk2.0-dev libgtk-3-dev
    sudo apt-get install -y libatlas-base-dev gfortran
    sudo apt-get install -y python2.7-dev

    # kinect
    sudo apt-get install -y libfreenect-dev
}

# https://www.pyimagesearch.com/2017/09/04/raspbian-stretch-install-opencv-3-python-on-your-raspberry-pi/
install_opencv () {
    base_dir=$1
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

    cd ${base_dir}
}

main () {
    base_dir=$(realpath ./)

    pip install numpy

    install_system_dependencies

    if [ $(uname -p) = "x86_64" ]; then
        pip install opencv-python
    else
        install_opencv ${base_dir}
    fi

    # Hack BrickPi code to work with reaspberry pi3
    cd ${base_dir}/dependencies/BrickPi/Software/BrickPi_Python
    sed -i 's/ttyAMA0/ttyS0/g' BrickPi.py
    python setup.py install

    # Install libfreenect
    cd ${base_dir}dependencies/libfreenect/wrappers/python
    python setup.py install
    cd ${base_dir}
}

#main
install_opencv $(realpath ./)
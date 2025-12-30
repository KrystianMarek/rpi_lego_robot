#!/bin/bash

project_dir=$(basename $(pwd))
rsync -a --exclude 'dependencies/BrickPi' --exclude 'dependencies/libfreenect' . pi@192.168.10.187:/home/pi/"${project_dir}"

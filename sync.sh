#!/bin/bash

project_dir=$(basename $(pwd))
rsync -a --exclude 'dependencies/BrickPi' --exclude 'dependencies/libfreenect' . pi@10.123.45.3:/home/pi/"${project_dir}"

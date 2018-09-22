#!/bin/bash

project_dir=$(basename $(pwd))
rsync -a ./* pi@10.123.45.3:/home/pi/"${project_dir}"

#!/bin/bash

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${script_dir}/.local/env"

project_dir=$(basename "${script_dir}")

rsync -ah --progress --delete \
    --exclude '.git' \
    --exclude '*.pyc' \
    --exclude '__pycache__' \
    --exclude '.venv' \
    --exclude '.local' \
    --exclude 'testing' \
    --exclude 'doc' \
    --exclude 'pictures' \
    --exclude 'dependencies/ncappzoo' \
    --exclude 'dependencies/ncsdk/docs' \
    --exclude 'dependencies/ncsdk/examples' \
    "${script_dir}/" pi@${ROBOT_IP}:/home/pi/"${project_dir}"

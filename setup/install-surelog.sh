#!/bin/sh

set -e

# Get directory of script
src_path=$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)

# These dependencies are up-to-date with instructions from the INSTALL.md from the commit we are pinned to below
sudo apt-get install -y build-essential cmake git pkg-config tclsh swig uuid-dev libgoogle-perftools-dev python3 python3-orderedmultidict python3-psutil python3-dev default-jre lcov
pip3 install orderedmultidict

mkdir -p deps
cd deps

git clone $(python3 ${src_path}/_tools.py --tool surelog --field git-url) surelog
cd surelog
git checkout $(python3 ${src_path}/_tools.py --tool surelog --field git-commit)
git submodule update --init --recursive

make
sudo make install

cd -

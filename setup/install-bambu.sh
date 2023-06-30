#!/bin/sh

set -e

# Get directory of script
src_path=$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)

sudo apt-get install -y autoconf autoconf-archive automake libtool g++ \
    libbdd-dev libboost-all-dev libmpc-dev libmpfr-dev \
    libxml2-dev liblzma-dev libmpfi-dev zlib1g-dev libicu-dev bison doxygen flex \
    graphviz iverilog verilator make libsuitesparse-dev libglpk-dev libgmp-dev \
    libfl-dev
sudo apt-get install -y gcc-9 g++-9 gcc-10 g++-10 gcc-9-plugin-dev gcc-10-plugin-dev \
    gcc-9-multilib gcc-10-multilib g++-9-multilib g++-10-multilib gfortran-9 gfortran-9-multilib \
    gfortran-10 gfortran-10-multilib libclang-11-dev clang-11 clang-12 libclang-12-dev

mkdir -p deps
cd deps

git clone $(python3 ${src_path}/_tools.py --tool bambu --field git-url) bambu
cd bambu
git checkout $(python3 ${src_path}/_tools.py --tool bambu --field git-commit)

if [ ! -z ${PREFIX} ]; then
    args=--prefix="$PREFIX"
else
    args=--prefix=/opt/panda

    sudo mkdir -p /opt/panda
    sudo chown $USER:$USER /opt/panda
fi

make -f Makefile.init

mkdir obj
cd obj

../configure --enable-release --disable-flopoco --with-opt-level=2 $args
make -j$(nproc)
make install

cd -

if [ -z ${PREFIX} ]; then
    echo "Please add \"export PATH="/opt/panda/bin:\$PATH"\" to your .bashrc"
fi

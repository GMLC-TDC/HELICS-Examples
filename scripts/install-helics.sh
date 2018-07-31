#!/bin/bash
# Script for checking out and building a copy of HELICS on CI servies (Travis)

# Get the os name
if [[ "$TRAVIS" == "true" ]]; then
    if [[ "$TRAVIS_OS_NAME" == "linux" ]]; then
        os_name="Linux"
    elif [[ "$TRAVIS_OS_NAME" == "osx" ]]; then
        os_name="Darwin"
    fi
else
    os_name="$(uname -s)"
fi

# Setup build flags using environment variables (set elsewhere, travis.yml or install-ci-dependencies.sh)
OPTION_FLAGS_ARR=()
OPTION_FLAGS_ARR+=("-DBUILD_C_SHARED_LIB=ON" "-DBUILD_CXX_SHARED_LIB=ON" "-DBUILD_PYTHON_INTERFACE=ON" "-DBUILD_JAVA_INTERFACE=ON")
OPTION_FLAGS_ARR+=("-DBUILD_HELICS_TESTS=OFF" "-DBUILD_HELICS_EXAMPLES=OFF")
OPTION_FLAGS_ARR+=("-DPYTHON_LIBRARY=${PYTHON_LIB_PATH}" "-DPYTHON_INCLUDE_DIR=${PYTHON_INCLUDE_PATH}")
OPTION_FLAGS_ARR+=("-DCMAKE_INSTALL_PREFIX=${CI_DEPENDENCY_DIR}/helics")

if [[ "$USE_SWIG" == 'false' ]] ; then HELICS_OPTION_FLAGS+=("-DDISABLE_SWIG=ON") ; fi
if [[ "$BUILD_TYPE" ]]; then OPTION_FLAGS_ARR+=("-DCMAKE_BUILD_TYPE=${BUILD_TYPE}") ; fi
if [[ "$USE_MPI" ]]; then OPTION_FLAGS_ARR+=("-DMPI_ENABLE=ON") ; fi
if [[ "$USE_MPI" ]]; then CC=${CI_DEPENDENCY_DIR}/mpi/bin/mpicc ; CXX=${CI_DEPENDENCY_DIR}/mpi/bin/mpic++ ; fi
HELICS_OPTION_FLAGS=${OPTION_FLAGS_ARR[@]}

#git clone helics... master, develop branch? for now, ignore the cached install of helics and always rebuild it for fresh updates
rm -rf ${CI_DEPENDENCY_DIR}/helics
git clone --single-branch -b develop https://github.com/GMLC-TDC/HELICS-src
pushd HELICS-src

# Create directories for building HELICS
mkdir -p build
cd build

# Build HELICS
HELICS_DEPENDENCY_FLAGS+="-DZeroMQ_INSTALL_PATH=${CI_DEPENDENCY_DIR}/zmq -DBOOST_INSTALL_PATH=${CI_DEPENDENCY_DIR}/boost"
cmake .. ${HELICS_DEPENDENCY_FLAGS} ${HELICS_OPTION_FLAGS} -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache
make ${MAKEFLAGS}
make install

export HELICS_INSTALL_PATH=${CI_DEPENDENCY_DIR}/helics

# Return to original directory
popd

# Update some environment variables for running HELICS executables
export PATH="${HELICS_INSTALL_PATH}/bin:${PATH}"
if [[ "$os_name" == "Linux" ]]; then
    export LD_LIBRARY_PATH=${HELICS_INSTALL_PATH}/lib64:${HELICS_INSTALL_PATH}/lib:$LD_LIBRARY_PATH
elif [[ "$os_name" == "Darwin" ]]; then
    export DYLD_LIBRARY_PATH=${HELICS_INSTALL_PATH}/lib64:${HELICS_INSTALL_PATH}/lib:$DYLD_LIBRARY_PATH
fi

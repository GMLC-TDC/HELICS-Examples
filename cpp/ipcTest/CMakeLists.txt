# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Copyright (c) 2017-2019, Battelle Memorial Institute; Lawrence Livermore
# National Security, LLC; Alliance for Sustainable Energy, LLC.
# See the top-level NOTICE for additional details.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

cmake_minimum_required(VERSION 3.4)

project(ipcTest-cpp)

if(NOT CMAKE_CXX_STANDARD)
    set(CMAKE_CXX_STANDARD 14)
endif()

find_package(HELICS 2 REQUIRED)
find_package(Threads REQUIRED)

add_executable(ipcTest1-cpp ipcTest1.cpp common.hpp)
target_link_libraries(ipcTest1-cpp HELICS::helics-static Threads::Threads)

add_executable(ipcTest2-cpp ipcTest2.cpp common.hpp)
target_link_libraries(ipcTest2-cpp HELICS::helics-static Threads::Threads)

set_target_properties(ipcTest1-cpp ipcTest2-cpp PROPERTIES FOLDER cpp/ipc)

##############################################################################
# Copyright (c) 2018,
# Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
#All rights reserved. See LICENSE file and DISCLAIMER for more details.
##############################################################################

cmake_minimum_required(VERSION 3.4)

project(ipcTest-cpp)

if(NOT CMAKE_CXX_STANDARD)
    set(CMAKE_CXX_STANDARD 14)
endif()

find_package(HELICS 2 REQUIRED)
find_package(Threads REQUIRED)

add_executable(ipcTest1-cpp ipcTest1.cpp common.hpp)
target_link_libraries(ipcTest1-cpp HELICS::helics-shared Threads::Threads)

add_executable(ipcTest2-cpp ipcTest2.cpp common.hpp)
target_link_libraries(ipcTest2-cpp HELICS::helics-shared Threads::Threads)

set_target_properties(ipcTest1-cpp ipcTest2-cpp PROPERTIES FOLDER cpp/ipc)

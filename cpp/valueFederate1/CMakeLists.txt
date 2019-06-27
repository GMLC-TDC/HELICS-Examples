##############################################################################
# Copyright © 2018,
# Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
#All rights reserved. See LICENSE file and DISCLAIMER for more details.
##############################################################################

cmake_minimum_required(VERSION 3.4)

project(valueFederate1-cpp)

if(NOT CMAKE_CXX_STANDARD)
    set(CMAKE_CXX_STANDARD 14)
endif()

find_package(HELICS 2 REQUIRED)

add_executable(valueFed-cpp valueFed.cpp)
target_link_libraries(valueFed-cpp HELICS::helics_apps)

set_target_properties(valueFed-cpp PROPERTIES FOLDER cpp/federates)

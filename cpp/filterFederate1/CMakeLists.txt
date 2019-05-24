##############################################################################
# Copyright © 2018,
# Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
#All rights reserved. See LICENSE file and DISCLAIMER for more details.
##############################################################################

cmake_minimum_required(VERSION 3.4)

project(filterFederate1-cpp)

if(NOT CMAKE_CXX_STANDARD)
    set(CMAKE_CXX_STANDARD 14)
endif()

find_package(HELICS 2 REQUIRED)

add_executable(filterFed-cpp filterFed.cpp)
target_link_libraries(filterFed-cpp HELICS::helics_apps)

set_target_properties(filterFed-cpp PROPERTIES FOLDER cpp/federates)

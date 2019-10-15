# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Copyright (c) 2017-2019, Battelle Memorial Institute; Lawrence Livermore
# National Security, LLC; Alliance for Sustainable Energy, LLC.
# See the top-level NOTICE for additional details.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

cmake_minimum_required(VERSION 3.4)

project(messageFederate1-cpp)

if(NOT CMAKE_CXX_STANDARD)
    set(CMAKE_CXX_STANDARD 14)
endif()

find_package(HELICS 2 REQUIRED)

add_executable(messageFed-cpp messageFed.cpp)
target_link_libraries(messageFed-cpp HELICS::helics_apps)

add_executable(messageFedObj-cpp messageFedObj.cpp)
target_link_libraries(messageFedObj-cpp HELICS::helics_apps)

set_target_properties(messageFed-cpp messageFedObj-cpp PROPERTIES FOLDER cpp/federates)

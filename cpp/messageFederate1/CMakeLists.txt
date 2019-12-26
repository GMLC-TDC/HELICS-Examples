##############################################################################
# Copyright (c) 2018,
# Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
#All rights reserved. See LICENSE file and DISCLAIMER for more details.
##############################################################################

cmake_minimum_required(VERSION 3.4)

project(messageFederate1-cpp)

if(NOT CMAKE_CXX_STANDARD)
    set(CMAKE_CXX_STANDARD 14)
endif()

find_package(HELICS 2 REQUIRED)

add_executable(messageFed-cpp messageFed.cpp)
target_link_libraries(messageFed-cpp HELICS::helics-apps-shared)

add_executable(messageFedObj-cpp messageFedObj.cpp)
target_link_libraries(messageFedObj-cpp HELICS::helics-apps-shared)

set_target_properties(messageFed-cpp messageFedObj-cpp PROPERTIES FOLDER cpp/federates)

##############################################################################
# Copyright © 2018,
# Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
#All rights reserved. See LICENSE file and DISCLAIMER for more details.
##############################################################################

cmake_minimum_required(VERSION 3.4)

project(messageFederate1)

find_package(HELICS REQUIRED)

add_executable(messageFed messageFed.cpp)
target_link_libraries(messageFed HELICS::helics-static)

add_executable(messageFedObj messageFedObj.cpp)
target_link_libraries(messageFedObj HELICS::helics-static)

set_target_properties(messageFed messageFedObj PROPERTIES FOLDER cpp/federates)

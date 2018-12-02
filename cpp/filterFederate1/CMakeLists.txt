##############################################################################
# Copyright © 2018,
# Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
#All rights reserved. See LICENSE file and DISCLAIMER for more details.
##############################################################################

cmake_minimum_required(VERSION 3.4)

project(filterFederate1)

find_package(HELICS REQUIRED)

add_executable(filterFed filterFed.cpp)
target_link_libraries(filterFed HELICS::helics-static)

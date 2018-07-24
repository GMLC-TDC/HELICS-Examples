##############################################################################
# Copyright © 2018,
# Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
#All rights reserved. See LICENSE file and DISCLAIMER for more details.
##############################################################################

cmake_minimum_required(VERSION 3.4)

project(comboFederate1)

find_package(HELICS REQUIRED)

add_executable(comboFed comboFed.cpp)
target_link_libraries(comboFed HELICS::helics_apps-static)

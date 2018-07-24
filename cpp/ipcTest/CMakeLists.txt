##############################################################################
# Copyright © 2018,
# Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
#All rights reserved. See LICENSE file and DISCLAIMER for more details.
##############################################################################

cmake_minimum_required(VERSION 3.4)

project(ipcTest)

find_package(HELICS REQUIRED)

add_executable(ipcTest1 ipcTest1.cpp common.hpp)
target_link_libraries(ipcTest1 HELICS::helics_apps-static)

add_executable(ipcTest2 ipcTest2.cpp common.hpp)
target_link_libraries(ipcTest2 HELICS::helics_apps-static)

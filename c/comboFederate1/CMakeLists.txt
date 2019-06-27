##############################################################################
# Copyright © 2018,
# Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
#All rights reserved. See LICENSE file and DISCLAIMER for more details.
##############################################################################

cmake_minimum_required(VERSION 3.4)

project(comboFederate1-c C)

find_package(HELICS 2 REQUIRED)

add_executable(comboFed-c comboFed.c)
target_link_libraries(comboFed-c HELICS::helicsSharedLib)
set_target_properties(comboFed-c PROPERTIES FOLDER c/federates)

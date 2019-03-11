##############################################################################
# Copyright © 2018,
# Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
#All rights reserved. See LICENSE file and DISCLAIMER for more details.
##############################################################################

cmake_minimum_required(VERSION 3.4)

project(nonlings C)

find_package(HELICS REQUIRED)

add_executable(nonlings_fed1 nonlings_fed1.c)
target_link_libraries(nonlings_fed1 HELICS::helicsSharedLib)

add_executable(nonlings_fed2 nonlings_fed2.c)
target_link_libraries(nonlings_fed2 HELICS::helicsSharedLib)

set_target_properties(nonlings_fed1 nonlings_fed2 PROPERTIES FOLDER c/nonlings)
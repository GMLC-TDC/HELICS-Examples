##############################################################################
# Copyright (c) 2018,
# Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
#All rights reserved. See LICENSE file and DISCLAIMER for more details.
##############################################################################

cmake_minimum_required(VERSION 3.4)

project(nonlings-c C)

find_package(HELICS 2 REQUIRED)

add_executable(nonlings_fed1-c nonlings_fed1.c)
target_link_libraries(nonlings_fed1-c HELICS::helicsSharedLib)

add_executable(nonlings_fed2-c nonlings_fed2.c)
target_link_libraries(nonlings_fed2-c HELICS::helicsSharedLib)

set_target_properties(nonlings_fed1-c nonlings_fed2-c PROPERTIES FOLDER c/nonlings)

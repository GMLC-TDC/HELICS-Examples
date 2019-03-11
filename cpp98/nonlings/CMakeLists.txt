##############################################################################
# Copyright © 2018,
# Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
#All rights reserved. See LICENSE file and DISCLAIMER for more details.
##############################################################################

cmake_minimum_required(VERSION 3.4)

project(nonlings_cpp CXX)

find_package(HELICS REQUIRED)

add_executable(nonlings_fed1_cpp nonlings_fed1.cpp)
target_link_libraries(nonlings_fed1_cpp HELICS::helicsCpp98)

add_executable(nonlings_fed2_cpp nonlings_fed2.cpp)
target_link_libraries(nonlings_fed2_cpp HELICS::helicsCpp98)

set_property(TARGET nonlings_fed1_cpp PROPERTY CXX_STANDARD 98)
set_property(TARGET nonlings_fed2_cpp PROPERTY CXX_STANDARD 98)

set_target_properties(nonlings_fed1_cpp nonlings_fed2_cpp PROPERTIES FOLDER cpp98)
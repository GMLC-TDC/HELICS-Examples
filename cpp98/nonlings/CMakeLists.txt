# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Copyright (c) 2017-2019, Battelle Memorial Institute; Lawrence Livermore
# National Security, LLC; Alliance for Sustainable Energy, LLC.
# See the top-level NOTICE for additional details.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

cmake_minimum_required(VERSION 3.4)

project(nonlings-cpp98 CXX)

find_package(HELICS 2 REQUIRED)

add_executable(nonlings_fed1-cpp nonlings_fed1.cpp)
target_link_libraries(nonlings_fed1-cpp HELICS::helicsCpp98)

add_executable(nonlings_fed2-cpp nonlings_fed2.cpp)
target_link_libraries(nonlings_fed2-cpp HELICS::helicsCpp98)

set_property(TARGET nonlings_fed1-cpp PROPERTY CXX_STANDARD 98)
set_property(TARGET nonlings_fed2-cpp PROPERTY CXX_STANDARD 98)

set_target_properties(nonlings_fed1-cpp nonlings_fed2-cpp PROPERTIES FOLDER cpp98)

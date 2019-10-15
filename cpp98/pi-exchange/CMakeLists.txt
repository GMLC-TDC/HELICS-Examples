# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Copyright (c) 2017-2019, Battelle Memorial Institute; Lawrence Livermore
# National Security, LLC; Alliance for Sustainable Energy, LLC.
# See the top-level NOTICE for additional details.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

cmake_minimum_required(VERSION 3.4)

project(pi_exchange-cpp CXX)

find_package(HELICS 2 REQUIRED)

add_executable(pi_receiver-cpp pi_receiver.cpp)
target_link_libraries(pi_receiver-cpp HELICS::helicsCpp98)

add_executable(pi_sender-cpp pi_sender.cpp)
target_link_libraries(pi_sender-cpp HELICS::helicsCpp98)

add_executable(pi_receiver2-cpp pi_receiver2.cpp)
target_link_libraries(pi_receiver2-cpp HELICS::helicsCpp98)

add_executable(pi_sender2-cpp pi_sender2.cpp)
target_link_libraries(pi_sender2-cpp HELICS::helicsCpp98)

set_target_properties(pi_receiver-cpp pi_receiver2-cpp pi_sender-cpp pi_sender2-cpp PROPERTIES FOLDER cpp98/pi_exchange)

set_property(TARGET pi_receiver-cpp PROPERTY CXX_STANDARD 98)
set_property(TARGET pi_receiver2-cpp PROPERTY CXX_STANDARD 98)
set_property(TARGET pi_sender-cpp PROPERTY CXX_STANDARD 98)
set_property(TARGET pi_sender2-cpp PROPERTY CXX_STANDARD 98)

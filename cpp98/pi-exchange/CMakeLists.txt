##############################################################################
# Copyright © 2018,
# Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
#All rights reserved. See LICENSE file and DISCLAIMER for more details.
##############################################################################

cmake_minimum_required(VERSION 3.4)

project(pi_exchange CXX)

find_package(HELICS REQUIRED)

add_executable(pi_receiver_cpp pi_receiver.cpp)
target_link_libraries(pi_receiver_cpp HELICS::helicsCpp98)

add_executable(pi_sender_cpp pi_sender.cpp)
target_link_libraries(pi_sender_cpp HELICS::helicsCpp98)

add_executable(pi_receiver2_cpp pi_receiver2.cpp)
target_link_libraries(pi_receiver2_cpp HELICS::helicsCpp98)

add_executable(pi_sender2_cpp pi_sender2.cpp)
target_link_libraries(pi_sender2_cpp HELICS::helicsCpp98)

set_target_properties(pi_receiver_cpp pi_receiver2_cpp pi_sender_cpp pi_sender2_cpp PROPERTIES FOLDER cpp98/pi_exchange)

set_property(TARGET pi_receiver_cpp PROPERTY CXX_STANDARD 98)
set_property(TARGET pi_receiver2_cpp PROPERTY CXX_STANDARD 98)
set_property(TARGET pi_sender_cpp PROPERTY CXX_STANDARD 98)
set_property(TARGET pi_sender2_cpp PROPERTY CXX_STANDARD 98)

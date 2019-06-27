##############################################################################
# Copyright © 2018,
# Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
#All rights reserved. See LICENSE file and DISCLAIMER for more details.
##############################################################################

cmake_minimum_required(VERSION 3.4)

project(pi_exchange-c C)

find_package(HELICS 2 REQUIRED)

add_executable(pi_receiver-c pi_receiver.c)
target_link_libraries(pi_receiver-c HELICS::helicsSharedLib)

add_executable(pi_sender-c pi_sender.c)
target_link_libraries(pi_sender-c HELICS::helicsSharedLib)

add_executable(pi_receiver2-c pi_receiver2.c)
target_link_libraries(pi_receiver2-c HELICS::helicsSharedLib)

add_executable(pi_sender2-c pi_sender2.c)
target_link_libraries(pi_sender2-c HELICS::helicsSharedLib)

set_target_properties(pi_receiver-c pi_receiver2-c pi_sender-c pi_sender2-c PROPERTIES FOLDER c/pi_exchange)

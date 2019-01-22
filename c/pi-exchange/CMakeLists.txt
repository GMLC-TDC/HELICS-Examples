##############################################################################
# Copyright © 2018,
# Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
#All rights reserved. See LICENSE file and DISCLAIMER for more details.
##############################################################################

cmake_minimum_required(VERSION 3.4)

project(pi_exchange C)

find_package(HELICS REQUIRED)

add_executable(pi_receiver pi_receiver.c)
target_link_libraries(pi_receiver HELICS::helicsSharedLib)

add_executable(pi_sender pi_sender.c)
target_link_libraries(pi_sender HELICS::helicsSharedLib)

add_executable(pi_receiver2 pi_receiver2.c)
target_link_libraries(pi_receiver2 HELICS::helicsSharedLib)

add_executable(pi_sender2 pi_sender2.c)
target_link_libraries(pi_sender2 HELICS::helicsSharedLib)

set_target_properties(pi_receiver pi_receiver2 pi_sender pi_sender2 PROPERTIES FOLDER c/pi_exchange)

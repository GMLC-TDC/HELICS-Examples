# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Copyright (c) 2017-2019, Battelle Memorial Institute; Lawrence Livermore
# National Security, LLC; Alliance for Sustainable Energy, LLC.
# See the top-level NOTICE for additional details.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

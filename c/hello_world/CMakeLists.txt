# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Copyright (c) 2017-2019, Battelle Memorial Institute; Lawrence Livermore
# National Security, LLC; Alliance for Sustainable Energy, LLC.
# See the top-level NOTICE for additional details.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

cmake_minimum_required(VERSION 3.4)

project(hello_world-c C)

find_package(HELICS 2 REQUIRED)

add_executable(hello_world_receiver-c hello_world_receiver.c)
target_link_libraries(hello_world_receiver-c HELICS::helicsSharedLib)

add_executable(hello_world_sender-c hello_world_sender.c)
target_link_libraries(hello_world_sender-c HELICS::helicsSharedLib)

set_target_properties(hello_world_sender-c hello_world_receiver-c PROPERTIES FOLDER c/hello_world)

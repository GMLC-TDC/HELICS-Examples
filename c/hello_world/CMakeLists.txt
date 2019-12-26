##############################################################################
# Copyright (c) 2018,
# Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
#All rights reserved. See LICENSE file and DISCLAIMER for more details.
##############################################################################

cmake_minimum_required(VERSION 3.4)

project(hello_world-c C)

find_package(HELICS 2 REQUIRED)

add_executable(hello_world_receiver-c hello_world_receiver.c)
target_link_libraries(hello_world_receiver-c HELICS::helicsSharedLib)

add_executable(hello_world_sender-c hello_world_sender.c)
target_link_libraries(hello_world_sender-c HELICS::helicsSharedLib)

set_target_properties(hello_world_sender-c hello_world_receiver-c PROPERTIES FOLDER c/hello_world)

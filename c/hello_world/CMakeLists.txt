##############################################################################
# Copyright © 2018,
# Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
#All rights reserved. See LICENSE file and DISCLAIMER for more details.
##############################################################################

cmake_minimum_required(VERSION 3.4)

project(hello_world C)

find_package(HELICS REQUIRED)

add_executable(hello_world_receiver hello_world_receiver.c)
target_link_libraries(hello_world_receiver HELICS::helicsSharedLib)

add_executable(hello_world_sender hello_world_sender.c)
target_link_libraries(hello_world_sender HELICS::helicsSharedLib)

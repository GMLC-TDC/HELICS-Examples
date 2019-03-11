##############################################################################
# Copyright © 2018,
# Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
#All rights reserved. See LICENSE file and DISCLAIMER for more details.
##############################################################################

cmake_minimum_required(VERSION 3.4)

project(messageFederate1 C)

find_package(HELICS REQUIRED)

add_executable(messageFed_c messageFed.c)
target_link_libraries(messageFed_c HELICS::helicsSharedLib)

set_target_properties(messageFed_c PROPERTIES FOLDER c/federates)
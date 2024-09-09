# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Copyright (c) 2017-2019, Battelle Memorial Institute; Lawrence Livermore
# National Security, LLC; Alliance for Sustainable Energy, LLC.
# See the top-level NOTICE for additional details.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

cmake_minimum_required(VERSION 3.4)

project(comboFederate1-c C)

find_package(HELICS 2 REQUIRED)

add_executable(comboFed-c comboFed.c)
target_link_libraries(comboFed-c HELICS::helicsSharedLib)
set_target_properties(comboFed-c PROPERTIES FOLDER c/federates)

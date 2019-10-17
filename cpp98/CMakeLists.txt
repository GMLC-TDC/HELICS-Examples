# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Copyright (c) 2017-2019, Battelle Memorial Institute; Lawrence Livermore
# National Security, LLC; Alliance for Sustainable Energy, LLC.
# See the top-level NOTICE for additional details.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

cmake_minimum_required(VERSION 3.4)
cmake_policy(VERSION 3.4)

project (HELICS_CPP_EXAMPLES VERSION 2.1.0)


get_directory_property(hasParent PARENT_DIRECTORY)
if(NOT hasParent)
    set_property(GLOBAL PROPERTY USE_FOLDERS ON)
    include(GNUInstallDirs)
endif()

# -----------------------------------------------------------------------------
# CMAKE Subdirectories
# -----------------------------------------------------------------------------

add_subdirectory(nonlings)
add_subdirectory(pi-exchange)

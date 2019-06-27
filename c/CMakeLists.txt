#
# Copyright © 2017-2018, Battelle Memorial Institute; Lawrence Livermore National
# Security, LLC; Alliance for Sustainable Energy, LLC All rights reserved. See LICENSE
# file and DISCLAIMER for more details.
#

cmake_minimum_required(VERSION 3.4)
cmake_policy(VERSION 3.4)

project (HELICS-C-EXAMPLES VERSION 2.1.0)


get_directory_property(hasParent PARENT_DIRECTORY)
if(NOT hasParent)
	set_property(GLOBAL PROPERTY USE_FOLDERS ON)
	include(GNUInstallDirs)
endif()

# -----------------------------------------------------------------------------
# CMAKE Subdirectories
# -----------------------------------------------------------------------------

add_subdirectory(comboFederate1)
add_subdirectory(hello_world)
add_subdirectory(nonlings)

add_subdirectory(messageFederate1)
add_subdirectory(pi-exchange)

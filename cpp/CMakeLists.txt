#
# Copyright © 2017-2018, Battelle Memorial Institute; Lawrence Livermore National
# Security, LLC; Alliance for Sustainable Energy, LLC All rights reserved. See LICENSE
# file and DISCLAIMER for more details.
#

cmake_minimum_required(VERSION 3.4)
cmake_policy(VERSION 3.4)

project (HELICS_CPP_EXAMPLES VERSION 2.0.0)


get_directory_property(hasParent PARENT_DIRECTORY)
if(hasParent)
  
else()
  set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${PROJECT_SOURCE_DIR}/../config/"  "${PROJECT_SOURCE_DIR}/config/")

	set_property(GLOBAL PROPERTY USE_FOLDERS ON)

	include(GNUInstallDirs)
endif()

# -----------------------------------------------------------------------------
# CMAKE Subdirectories
# -----------------------------------------------------------------------------

add_subdirectory(comboFederate1)
add_subdirectory(filterFederate1)
add_subdirectory(ipcTest)

add_subdirectory(messageFederate1)
add_subdirectory(valueFederate1)
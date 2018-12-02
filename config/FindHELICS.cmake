##############################################################################
# Copyright © 2018,
# Battelle Memorial Institute; Lawrence Livermore National Security, LLC; Alliance for Sustainable Energy, LLC
#All rights reserved. See LICENSE file and DISCLAIMER for more details.
##############################################################################

IF (MSVC)
	set(HELICS_PATH_HINTS
		C:/local/helics_2_0_0
		)
		
  if(DEFINED HELICS_INSTALL_PATH)
    set(HELICS_INSTALL_PATH "${HELICS_INSTALL_PATH}" CACHE PATH "path to the helics installation" FORCE)
  else()
    set(${var} "C:/local/helics_2_0_0" CACHE PATH "path to the helics installation")
  endif()

ELSE(MSVC)
  if(DEFINED HELICS_INSTALL_PATH)
    set(HELICS_INSTALL_PATH "${HELICS_INSTALL_PATH}" CACHE PATH "path to the helics installation" FORCE)
  else()
    set(${var} "/usr/bin" CACHE PATH "path to the helics installation")
  endif()

ENDIF(MSVC)

set(HELICS_CMAKE_SUFFIXES 
	lib/cmake/HELICS/
			cmake/HELICS/)
	
find_package(HELICS 2 NO_MODULE
	HINTS 
		${HELICS_INSTALL_PATH}
		$ENV{HELICS_INSTALL_PATH}
		${HELICS_PATH_HINTS}
	PATH_SUFFIXES ${HELICS_CMAKE_SUFFIXES}
	)
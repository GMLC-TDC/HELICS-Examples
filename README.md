# HELICS-Examples

[![Build Status](https://dev.azure.com/HELICS-test/HELICS-Examples/_apis/build/status/GMLC-TDC.HELICS-Examples?branchName=master)](https://dev.azure.com/HELICS-test/HELICS-Examples/_build/latest?definitionId=2?branchName=master)

Examples for using HELICS with a variety of the supported programming languages

All C and C++ examples can be build through CMAKE.  They can be build from individual folders or by running CMAKE on the main folder

On Windows and systems with HELICS installed in a non-system search path, the `HELICS_DIR` environment variable can be set to the folder HELICS was installed to (the one containing `bin`, `include`, and `lib`/`lib64` subfolders). Alternatives to this include adding the HELICS install folder to your `PATH` environment variable, or setting the `CMAKE_PREFIX_PATH` to the HELICS install folder (either as an environment variable, or using the `-DCMAKE_PREFIX_PATH=value` CMake
argument.

## Source Repo

The HELICS source code is hosted on GitHub: [https://github.com/GMLC-TDC/HELICS](https://github.com/GMLC-TDC/HELICS)

## Release
HELICS-Examples is distributed under the terms of the BSD-3 clause license. All new
contributions must be made under this license. [LICENSE](LICENSE)

SPDX-License-Identifier: BSD-3-Clause

portions of the code written by LLNL with release number
LLNL-CODE-739319


# OSMSES HELICS Tutorial Example

This example was as OSMSES 2024 HELICS tutorial presented by Trevor Hardy. It provides a series of simple Python-based models for a battery and charger that start as solo Python scripts and progress to an integrated HELICS co-simulation. The file names indicate the point in the progression:

- `*_solo.py` - Initial models that each run solo without any interaction between the two. 
- `*_cosim_incomplete.py` - Starting point for the in-class version of the exercise. The body of the code is the same as the `*._solo.py` with the file's docstring listing the required HELICS APIs that need to be incorporated.
- `*_cosim_complete.py` - Completed working version of the corresponding `*_cosim_incomplete.py` files
- `*_cosim_complete_pythonic.py` - Same as `*_cosim_complete.py` but using the HELICS Pythonic APIs
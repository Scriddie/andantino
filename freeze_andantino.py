# https://pythonprogramming.net/converting-pygame-executable-cx_freeze/
# cmd argument: build

import cx_Freeze

executables = [cx_Freeze.Executable("controller.py", base = "Win32GUI")]

# maybe include other packages as well just to be sure?
cx_Freeze.setup(
    name = "andantino",
    options = {"build_exe": {"packages": ["pygame"]}},
    executables = executables
)

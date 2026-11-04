#!/bin/bash
# Template for envvars.sh (copy this file to envvars.sh and adjust the variables below)

# depending on your shell and os you need to use .zshrc, .bashrc, .bash_profile, etc.
export BASHRC="~/.zshrc"

# you can find this path by looking at the content added by conda init into your BASHRC file
export CONDA_SH="/opt/miniconda3/etc/profile.d/conda.sh"

# optional: where the tested repositories (and all downloaded/converted data inside them) live.
# Default: the dependencies/ submodules of this checkout. Set it to keep that state outside the
# checkout; missing repositories are then cloned there by `update-repos`.
# export SDC_WORKSPACE="/path/to/workspace"

# optional: number of pytest-xdist workers per test suite in `run-tests` (default: auto = one per CPU).
# Each worker imports the full stack, so on a many-core machine `auto` can need a lot of memory.
# export SDC_PYTEST_WORKERS=4

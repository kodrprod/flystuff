#!/bin/bash
# ===========================================================================
# One-step setup for the drone delivery simulation on a Mac.
#
# You can either:
#   (a) double-click this file in Finder, OR
#   (b) run it from Terminal with:   bash setup_mac.command
#
# It creates a private Python environment (a "virtual environment") inside this
# folder and installs the required packages into it. It does not touch the rest
# of your system.
# ===========================================================================

set -e  # stop on the first error

# Always work from the folder this script lives in.
cd "$(dirname "$0")"

echo "=============================================================="
echo " Drone Delivery Simulation — setup"
echo "=============================================================="

# 1. Check Python 3 exists.
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 was not found."
    echo "Install Python 3 first (see the README, section 1), then run this again."
    exit 1
fi
echo "Using: $(python3 --version)"

# 2. Create the virtual environment (only if it does not already exist).
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment in .venv ..."
    python3 -m venv .venv
else
    echo "Virtual environment .venv already exists — reusing it."
fi

# 3. Activate it and install the dependencies.
source .venv/bin/activate
echo "Upgrading pip ..."
python -m pip install --upgrade pip >/dev/null
echo "Installing required packages (this can take a minute) ..."
pip install -r requirements.txt

echo ""
echo "=============================================================="
echo " Setup complete!"
echo ""
echo " To run the simulation, copy-paste these two lines in Terminal:"
echo "     cd \"$(pwd)\""
echo "     source .venv/bin/activate && python main.py"
echo "=============================================================="

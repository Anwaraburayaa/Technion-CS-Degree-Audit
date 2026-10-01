#!/usr/bin/env bash
# run_tests.sh — runs all the project's tests with pytest.
# Usage (from anywhere):  ./run_tests.sh
# Extra pytest options are passed through, e.g.:  ./run_tests.sh -k duplicate

set -e                                              # stop immediately if any command fails

cd "$(dirname "$0")"                                # go to the folder this script is in (the project root), so paths like data/ work

if [ -f venv/bin/activate ]; then                   # does the project's virtual environment exist?
    source venv/bin/activate                        # yes → turn it on, so we use the project's Python and pytest
else                                                # no venv folder found
    echo "venv not found. Create it with: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"  # explain how to fix it
    exit 1                                          # stop with an error code
fi

python -m pytest -v "$@"                            # run all tests in tests/; -v shows each test name; "$@" adds any options you typed

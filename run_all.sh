#!/usr/bin/env bash
# Runs every stage in order. Stops at the first failure rather than carrying on
# with a half-built file. Works in Git Bash on Windows.
set -e
echo "== 1/6 profile ==";   python src/01_profile.py
echo "== 2/6 filter ==";    python src/02_filter.py
echo "== 3/6 sql ==";       python src/03_load_sqlite.py
echo "== 4/6 features ==";  python src/04_text_features.py
echo "== 5/6 model ==";     python src/05_model.py
echo "== 6/6 figures ==";   python src/06_build_figures.py
echo
echo "Done. Open docs/index.html in a browser to check the dashboard."

# Python PyPI Package Analyzer

This project is a simple tool that **retrieves**, **downloads**, **extracts**, and **analyzes** Python packages from [PyPI](https://pypi.org/).  
It automatically identifies a package’s **latest version**, downloads its distribution file (`.whl` or `.tar.gz`), extracts its contents, and tries to extract **dependency** information from it.

## Features
- Fetch package metadata from PyPI.
- Automatically download `.whl` or `.tar.gz` files (prefers `.whl` if available).
- Extract package files safely into a temporary directory.
- Search for dependencies by parsing:
  - `METADATA` files (inside `.whl` distributions),
  - `setup.py` (looking for `install_requires`),
  - `requirements.txt`.
- Clean up temporary files after analysis.

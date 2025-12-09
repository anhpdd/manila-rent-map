# Configuration file for Philippine Rental Price project

import os
from pathlib import Path

# Get the project root directory (assuming config.py is in src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Input data paths
INPUT_FILE = PROJECT_ROOT / "data" / "property_details_combined_20251209_202026.csv"
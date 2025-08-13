#!/usr/bin/env python3
"""Test script for The Odds API integration."""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set the API key for testing
os.environ['THEODDS_API_KEY'] = '7f368349a729ac04ca1251f6ecda8d81'

from scrapers.theodds import test_theodds_api

if __name__ == "__main__":
    test_theodds_api()

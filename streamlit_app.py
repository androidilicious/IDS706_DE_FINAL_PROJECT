"""
Main entry point for Streamlit Cloud deployment.
This file should be in the root directory.
"""

# Import the dashboard app
import sys
from pathlib import Path

# Add dashboard directory to path
dashboard_path = Path(__file__).parent / "dashboard"
sys.path.insert(0, str(dashboard_path))

# Import and run the app
from dashboard.app import *

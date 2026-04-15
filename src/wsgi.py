import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)  # ← current_dir, not parent_dir

from app import create_app
app = create_app()
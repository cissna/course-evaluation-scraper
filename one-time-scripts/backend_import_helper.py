import sys
import os

# Add the backend directory to the Python path to allow imports
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

# Now you can import backend modules like:
# from scraper_service import some_function
# from analysis import some_other_function
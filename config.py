import os
from pathlib import Path

# Try to load environment variables, but don't fail if .env doesn't exist
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, that's okay
    pass

# API Endpoints (all free)
FDA_BASE_URL = "https://api.fda.gov/drug/"
USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1/"
RXNAV_BASE_URL = "https://rxnav.nlm.nih.gov/REST/"
OPENFOOD_BASE_URL = "https://world.openfoodfacts.org/api/v0/"

# Database settings
DATABASE_PATH = "data/dietrx.db"
CACHE_EXPIRY_HOURS = 24

# Fuzzy matching thresholds
FUZZY_MATCH_THRESHOLD = 80  # Minimum similarity score
MAX_SUGGESTIONS = 5

# Streamlit settings (not used in config, moved to app.py)
PAGE_TITLE = "DietRx Enhanced"
PAGE_ICON = "💊"
LAYOUT = "wide"

# API Keys (if needed - most of these APIs are free without keys)
USDA_API_KEY = os.getenv("USDA_API_KEY", "")  # Optional but recommended
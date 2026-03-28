import os
from dotenv import load_dotenv

load_dotenv()

# Database
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "faers")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# FAERS data range to download
START_YEAR = int(os.getenv("FAERS_START_YEAR", 2022))
END_YEAR = int(os.getenv("FAERS_END_YEAR", 2024))
QUARTERS = [int(q) for q in os.getenv("FAERS_QUARTERS", "1,2,3,4").split(",")]

# Paths
DATA_RAW_DIR = "data/raw"
DATA_PROCESSED_DIR = "data/processed"
REFERENCE_DIR = "data/reference"
KAGGLE_REFERENCE_DIR = os.getenv("KAGGLE_REFERENCE_DIR", f"{REFERENCE_DIR}/kaggle")

# Optional explicit file paths (overrides auto-discovery when set)
REFERENCE_BRAND_GENERIC_FILE = os.getenv("REFERENCE_BRAND_GENERIC_FILE", "")
REFERENCE_MEDDRA_SOC_FILE = os.getenv("REFERENCE_MEDDRA_SOC_FILE", "")

# Signal detection thresholds (Evans et al. 2001 criteria)
PRR_THRESHOLD = 2.0          # PRR must be >= 2
CHI2_THRESHOLD = 4.0         # Chi-squared must be >= 4 (approx p < 0.05)
MIN_CASE_COUNT = 3           # At least 3 cases required
ROR_CI_LOWER_THRESHOLD = 1.0 # Lower bound of 95% CI must be > 1

# Drug name cleaning
DOSAGE_PATTERN = r'\d+\.?\d*\s*(mg|ml|mcg|ug|g|%|iu|units?|tablet|cap|capsule)s?'
FUZZY_MATCH_THRESHOLD = 85   # Minimum score for fuzzy brand->generic mapping

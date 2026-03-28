import os
import zipfile
import requests
from tqdm import tqdm
from src.config import START_YEAR, END_YEAR, QUARTERS, DATA_RAW_DIR

# FAERS ASCII data download URL pattern
# Files are named like: faers_ascii_2023Q1.zip
FAERS_BASE_URL = "https://fis.fda.gov/content/Exports/faers_ascii_{year}q{quarter}.zip"

def get_all_quarters() -> list[tuple[int, int]]:
    """Return all (year, quarter) combinations in the configured range."""
    result = []
    for year in range(START_YEAR, END_YEAR + 1):
        for q in QUARTERS:
            result.append((year, q))
    return result


def download_quarter(year: int, quarter: int, force: bool = False) -> str:
    """
    Download a single FAERS quarterly ZIP file.
    Returns the local path to the downloaded ZIP.
    Skips download if file already exists unless force=True.
    """
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    filename = f"faers_ascii_{year}q{quarter}.zip"
    local_path = os.path.join(DATA_RAW_DIR, filename)

    if os.path.exists(local_path) and not force:
        print(f"  [SKIP] {filename} already exists.")
        return local_path

    url = FAERS_BASE_URL.format(year=year, quarter=quarter)
    print(f"  [DOWNLOAD] {url}")

    response = requests.get(url, stream=True, timeout=120)
    if response.status_code == 404:
        # Try alternate URL format (FDA occasionally changes naming)
        url_alt = f"https://fis.fda.gov/content/Exports/faers_ascii_{year}Q{quarter}.zip"
        response = requests.get(url_alt, stream=True, timeout=120)

    if response.status_code != 200:
        raise RuntimeError(f"Failed to download {url}: HTTP {response.status_code}")

    total = int(response.headers.get("content-length", 0))
    with open(local_path, "wb") as f, tqdm(total=total, unit="B", unit_scale=True) as bar:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            bar.update(len(chunk))

    return local_path


def extract_quarter(zip_path: str, year: int, quarter: int) -> str:
    """
    Extract the ZIP into data/raw/{year}Q{quarter}/.
    Returns the extraction directory path.
    """
    extract_dir = os.path.join(DATA_RAW_DIR, f"{year}Q{quarter}")
    os.makedirs(extract_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)

    print(f"  [EXTRACT] Extracted to {extract_dir}")
    return extract_dir


def download_all_quarters(force: bool = False) -> list[str]:
    """
    Download and extract all quarters in the configured range.
    Returns list of extracted directory paths.
    """
    dirs = []
    for year, quarter in get_all_quarters():
        print(f"\n[Quarter {year}Q{quarter}]")
        try:
            zip_path = download_quarter(year, quarter, force=force)
            extract_dir = extract_quarter(zip_path, year, quarter)
            dirs.append((f"{year}Q{quarter}", extract_dir))
        except Exception as e:
            print(f"  [ERROR] Could not download {year}Q{quarter}: {e}")
    return dirs

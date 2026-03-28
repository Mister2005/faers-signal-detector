import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Download Kaggle reference datasets into data/reference/kaggle")
    parser.add_argument("--dataset", required=True, help="Kaggle dataset slug: owner/dataset-name")
    parser.add_argument(
        "--out-dir",
        default="data/reference/kaggle",
        help="Output directory for downloaded CSV files",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except Exception as exc:
        raise SystemExit(
            "Kaggle package is not available. Install dependencies first with: pip install -r requirements.txt"
        ) from exc

    api = KaggleApi()
    api.authenticate()
    api.dataset_download_files(args.dataset, path=str(out_dir), unzip=True)

    csv_files = sorted(out_dir.glob("*.csv"))
    print(f"Downloaded {len(csv_files)} CSV files into {out_dir}")
    for f in csv_files:
        print(f"- {f.name}")


if __name__ == "__main__":
    main()

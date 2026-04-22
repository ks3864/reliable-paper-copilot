"""Download a versioned sample paper package into the local data directory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.request import urlretrieve


def load_manifest(package_dir: Path) -> dict:
    manifest_path = package_dir / "manifest.json"
    with manifest_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def fetch_sample_package(package_dir: Path, output_dir: Path) -> Path:
    manifest = load_manifest(package_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{manifest['package_id']}.pdf"
    urlretrieve(manifest["paper_url"], output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "package_dir",
        nargs="?",
        default="sample_packages/attention-is-all-you-need",
        help="Path to the sample package directory",
    )
    parser.add_argument(
        "--output-dir",
        default="data/raw",
        help="Directory where the downloaded PDF should be stored",
    )
    args = parser.parse_args()

    output_path = fetch_sample_package(Path(args.package_dir), Path(args.output_dir))
    print(output_path)


if __name__ == "__main__":
    main()

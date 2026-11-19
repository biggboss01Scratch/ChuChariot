"""Extract registered PDF crops locally. Requires Poppler pdftoppm and Pillow."""

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from PIL import Image


def extract_clips(pdf, manifest, output):
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    if digest != manifest["source_sha256"]["source:001"]:
        raise ValueError("PDF changed; verify clip coordinates against the new version")
    by_page = defaultdict(list)
    for item in manifest["items"]:
        if item["kind"] == "source_clip":
            by_page[item["pdf_page"]].append(item)
    output.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory() as temp:
        prefix = Path(temp) / "page"
        for page, clips in by_page.items():
            subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-scale-to", "1800",
                            "-singlefile", "-png", str(pdf), str(prefix)], check=True)
            with Image.open(prefix.with_suffix(".png")) as image:
                for clip in clips:
                    if tuple(clip["page_size_px"]) != image.size:
                        raise ValueError(f"Unexpected page size for {clip['id']}: {image.size}")
                    image.crop(clip["rect_px"]).save(output / clip["filename"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    extract_clips(args.pdf, json.loads(args.manifest.read_text(encoding="utf-8")), args.output)

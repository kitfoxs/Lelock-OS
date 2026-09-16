#!/usr/bin/env python3
"""Fetch pinned upstream archives from the official Lelock OS release.
Verifies exact SHA-256 checksums from project/resources/source-lock.json.
Standard library only: no external dependencies required.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
PACKET = PROJECT.parent
RELEASE_BASE = "https://github.com/kitfoxs/Lelock-OS/releases/download/v0.1.0-alpha"


def verify_sha256(path: Path, expected: str) -> bool:
    if not path.is_file():
        return False
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == expected


def download_file(url: str, dest: Path, expected_sha256: str) -> None:
    temp_dest = dest.with_name(dest.name + ".part")
    print(f"Downloading {dest.name} from {url} ...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Lelock-OS-Fetcher/1.0"})
        with urllib.request.urlopen(req) as resp, temp_dest.open("wb") as out:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = (downloaded / total) * 100
                    mb = downloaded / (1024 * 1024)
                    sys.stdout.write(f"\r  [{mb:.1f} MB / {total / (1024*1024):.1f} MB] ({pct:.1f}%)")
                    sys.stdout.flush()
            if total > 0:
                sys.stdout.write("\n")
    except Exception as exc:
        if temp_dest.exists():
            temp_dest.unlink()
        raise RuntimeError(f"Failed downloading {url}: {exc}") from exc

    digest = hashlib.sha256()
    with temp_dest.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != expected_sha256:
        temp_dest.unlink()
        raise RuntimeError(
            f"Checksum mismatch for {dest.name}!\n  Expected: {expected_sha256}\n  Actual:   {actual}"
        )
    temp_dest.rename(dest)
    print(f"  Verified SHA-256 for {dest.name}: OK")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--all",
        action="store_true",
        help="Also fetch optional SoulTavern archive (already vendored in src/lelock/_vendor).",
    )
    args = parser.parse_args()

    lock_file = PROJECT / "resources/source-lock.json"
    if not lock_file.is_file():
        print(f"Error: missing {lock_file}", file=sys.stderr)
        return 1

    lock = json.loads(lock_file.read_text("utf-8"))
    upstream_dir = PACKET / "upstream"
    upstream_dir.mkdir(parents=True, exist_ok=True)

    targets = ["hermes", "mempalace"]
    if args.all:
        targets.append("soultavern")

    success = True
    for key in targets:
        info = lock["sources"][key]
        filename = info["file"]
        expected_sha256 = info["sha256"]
        target_path = upstream_dir / filename

        if target_path.is_file():
            if verify_sha256(target_path, expected_sha256):
                print(f"Already present and verified: {filename}")
                continue
            else:
                print(f"Existing file {filename} checksum mismatch. Re-downloading...")

        url = f"{RELEASE_BASE}/{filename}"
        try:
            download_file(url, target_path, expected_sha256)
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            success = False

    if not success:
        return 1

    print("\nAll required upstream archives are present and verified!")
    print("Next step: run 'python3 project/scripts/bootstrap.py --allow-network'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

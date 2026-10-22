#!/usr/bin/env python3
"""Build a MiSTer Downloader database for thekoalakoa's Paprium core.

The release zip installs into _Console. This database installs the same core
under _Custom Cores and keeps the upstream launcher from being used.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import posixpath
import re
import sys
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
DB_ID = "thekoalakoa/Paprium_MiSTer"
UPSTREAM = "thekoalakoa/Paprium_MiSTer"
RBF_DEST = "_Custom Cores/Cores/Paprium.rbf"
MGL_DEST = "_Custom Cores/Paprium.mgl"
RBF_IN_ZIP = "_Console/Paprium.rbf"
GAME_FOLDER = "games/Paprium"
ASSET_NAME = re.compile(r"Paprium_MiSTer_.+\.zip$")
USER_AGENT = "paprium-koala-db"
TAG_DICTIONARY = {
    "console": 0,
    "consolecores": 0,
    "genesis": 1,
    "megadrive": 1,
    "paprium": 2,
}
TAGS = [0, 1, 2]


def repository_slug() -> str:
    from_env = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if from_env:
        return from_env
    slug = (ROOT / "github_repository.txt").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", slug):
        raise SystemExit(
            "Set github_repository.txt to owner/paprium-koala-db, "
            "or export GITHUB_REPOSITORY."
        )
    return slug


def raw_url(repository: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{repository}/main/{path}"


def md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def http_get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def parent_folders(paths: list[str]) -> list[str]:
    found: set[str] = set()
    for path in paths:
        parent = posixpath.dirname(path)
        while parent:
            found.add(parent)
            parent = posixpath.dirname(parent)
    return sorted(found)


def member_path(info: zipfile.ZipInfo) -> str:
    return info.filename.replace("\\", "/")


def choose_release_zip(assets: list[dict[str, Any]], fetch: Callable[[str], bytes]) -> tuple[str, bytes]:
    matches = []
    for asset in assets:
        name = str(asset.get("name") or "")
        url = str(asset.get("browser_download_url") or "")
        if ASSET_NAME.fullmatch(name) and url.startswith("https://"):
            matches.append(url)

    if len(matches) != 1:
        raise RuntimeError("Latest release must contain one Paprium_MiSTer_*.zip")
    url = matches[0]
    return url, fetch(url)


def read_member(archive_data: bytes, path: str) -> bytes:
    with zipfile.ZipFile(io.BytesIO(archive_data)) as archive:
        for info in archive.infolist():
            if member_path(info) == path:
                return archive.read(info)
    raise RuntimeError(f"Missing {path} in the release zip")


def launcher_bytes() -> bytes:
    return (ROOT / "Paprium.mgl").read_bytes().replace(b"\r\n", b"\n")


def build_database(
    *,
    repository: str,
    tag: str,
    archive_url: str,
    archive_data: bytes,
    rbf_path: str,
    rbf_data: bytes,
    mgl_data: bytes,
    timestamp: int,
) -> dict[str, Any]:
    rbf_folders = {
        path: {"arc_id": "release", "tags": TAGS}
        for path in parent_folders([RBF_DEST])
    }
    direct_folders = parent_folders([MGL_DEST]) + parent_folders([GAME_FOLDER]) + [GAME_FOLDER]
    return {
        "v": 1,
        "db_id": DB_ID,
        "db_url": raw_url(repository, "dist/db.json"),
        "timestamp": timestamp,
        "files": {
            MGL_DEST: {
                "hash": md5(mgl_data),
                "overwrite": True,
                "size": len(mgl_data),
                "tags": TAGS,
                "url": raw_url(repository, "Paprium.mgl"),
            }
        },
        "folders": {
            path: {"tags": TAGS}
            for path in sorted(set(direct_folders))
        },
        "tag_dictionary": dict(sorted(TAG_DICTIONARY.items())),
        "archives": {
            "release": {
                "format": "zip",
                "extract": "selective",
                "description": f"Installing Paprium {tag}",
                "archive_file": {
                    "hash": md5(archive_data),
                    "size": len(archive_data),
                    "url": archive_url,
                },
                "summary_inline": {
                    "files": {
                        RBF_DEST: {
                            "arc_at": rbf_path,
                            "arc_id": "release",
                            "hash": md5(rbf_data),
                            "overwrite": True,
                            "size": len(rbf_data),
                            "tags": TAGS,
                        }
                    },
                    "folders": dict(sorted(rbf_folders.items())),
                },
            }
        },
    }


def content_without_timestamp(database: dict[str, Any]) -> dict[str, Any]:
    content = dict(database)
    content.pop("timestamp", None)
    return content


def write_json(path: Path, database: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(database, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def publish(database: dict[str, Any]) -> bool:
    output = ROOT / "dist" / "db.json"
    if output.is_file():
        previous = json.loads(output.read_text(encoding="utf-8"))
        if content_without_timestamp(previous) == content_without_timestamp(database):
            database = previous
            changed = False
        else:
            changed = True
    else:
        changed = True

    if changed:
        write_json(output, database)

    ini = (
        f"[{database['db_id']}]\n"
        f"db_url = {database['db_url']}\n"
    )
    (ROOT / "downloader_paprium_koala.ini").write_text(ini, encoding="utf-8", newline="\n")
    return changed


def latest_release() -> dict[str, Any]:
    payload = http_get(f"https://api.github.com/repos/{UPSTREAM}/releases/latest")
    release = json.loads(payload)
    if not isinstance(release, dict):
        raise RuntimeError("Unexpected GitHub release response")
    return release


def main() -> int:
    repository = repository_slug()
    release = latest_release()
    assets = release.get("assets") or []
    if not isinstance(assets, list):
        raise RuntimeError("Release assets are missing")
    archive_url, archive_data = choose_release_zip(assets, http_get)
    database = build_database(
        repository=repository,
        tag=str(release.get("tag_name") or "latest"),
        archive_url=archive_url,
        archive_data=archive_data,
        rbf_path=RBF_IN_ZIP,
        rbf_data=read_member(archive_data, RBF_IN_ZIP),
        mgl_data=launcher_bytes(),
        timestamp=int(time.time()),
    )
    changed = publish(database)
    print(f"{DB_ID} -> dist/db.json ({'updated' if changed else 'unchanged'})")
    print(database["db_url"])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)

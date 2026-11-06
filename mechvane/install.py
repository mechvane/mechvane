"""Download and locate the pinned SolidCraft CLI release, for `mechvane setup`.

The release archive for this platform is downloaded once into the Mechvane cache directory and
checked against a pinned SHA256. Lookup order for the CLI: $SOLIDCRAFT_CLI, the cached download,
then `solidcraft-cli` on PATH.
"""

import hashlib
import os
import platform
import shutil
import stat
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

VERSION = "0.30.1"
BASE_URL = f"https://github.com/tangency-labs/solidcraft/releases/download/v{VERSION}/"

if sys.platform == "win32" and os.environ.get("LOCALAPPDATA"):
    CACHE = Path(os.environ["LOCALAPPDATA"]) / "mechvane"
else:
    CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "mechvane"

# Release assets per (system, machine), SHA256 from the GitHub release.
ASSETS = {
    ("linux", "x86_64"): (f"solidcraft-{VERSION}-linux-x86_64.tar.gz",
                          "2be163c618e7ccd9523d997ebd9f5094c310e968a80560b2840db1e1a8c0d482"),
    ("linux", "aarch64"): (f"solidcraft-{VERSION}-linux-aarch64.tar.gz",
                           "6bd69ad0fea2bf7b7e856914389812c60146aa952a9c0d7c91bc0f1cd317ccb1"),
    ("windows", "x86_64"): (f"solidcraft-{VERSION}-windows-x64-portable.zip",
                            "14392c9d96f21a6bcd606d565bd676703be46c01fccf8956da2e8a89ab1f1d21"),
    ("windows", "aarch64"): (f"solidcraft-{VERSION}-windows-arm64-portable.zip",
                             "9bf6c7c05c2ad0ea20c364bd8ef9f7e770d9baf41d1b8eb5f0aaf061ce38dad5"),
    ("darwin", "universal"): (f"solidcraft-cli-{VERSION}-macos-universal.zip",
                              "1effd9b38bc7f8a67ef7a7c8bec49df6453b307e9f1476b638e2c4f70208dc2f"),
}

MACHINES = {"amd64": "x86_64", "x64": "x86_64", "x86_64": "x86_64", "arm64": "aarch64", "aarch64": "aarch64"}


def platform_key() -> tuple[str, str]:
    system = platform.system().lower()
    if system == "darwin":
        return ("darwin", "universal")
    return (system, MACHINES.get(platform.machine().lower(), platform.machine().lower()))


def exe_name() -> str:
    return "solidcraft-cli.exe" if sys.platform == "win32" else "solidcraft-cli"


def install_dir() -> Path:
    system, machine = platform_key()
    return CACHE / f"solidcraft-cli-{VERSION}-{system}-{machine}"


def cached_cli() -> Path | None:
    """The CLI from a previous `mechvane setup`, or None."""
    root = install_dir()
    if not root.is_dir():
        return None
    return next((p for p in sorted(root.rglob(exe_name())) if p.is_file()), None)


def find_cli() -> str:
    """Executable to start for `solidcraft-cli mcp`."""
    env = os.environ.get("SOLIDCRAFT_CLI")
    if env:
        return env
    cached = cached_cli()
    if cached:
        return str(cached)
    return shutil.which("solidcraft-cli") or "solidcraft-cli"


def _download(url: str, target: Path, sha256: str, log=print) -> None:
    """Stream url into target, checking the SHA256 before the file is kept."""
    tmp = target.with_name(target.name + ".part")
    digest = hashlib.sha256()
    with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while chunk := r.read(1 << 20):
            f.write(chunk)
            digest.update(chunk)
            done += len(chunk)
            if total and done % (16 << 20) < (1 << 20):
                log(f"  {done >> 20} / {total >> 20} MB")
    if digest.hexdigest() != sha256:
        tmp.unlink()
        raise RuntimeError(f"{target.name}: SHA256 {digest.hexdigest()} does not match the pinned {sha256}")
    tmp.replace(target)


def _safe_members(names, asset: str) -> None:
    for name in names:
        if name.startswith(("/", "\\")) or ".." in Path(name.replace("\\", "/")).parts:
            raise RuntimeError(f"{asset}: unsafe path {name}")


def _extract(archive: Path, target: Path, asset: str) -> None:
    if asset.endswith(".zip"):
        with zipfile.ZipFile(archive) as z:
            _safe_members(z.namelist(), asset)
            z.extractall(target)
        return
    with tarfile.open(archive) as t:
        members = t.getmembers()
        _safe_members([m.name for m in members], asset)
        for m in members:
            if (m.issym() or m.islnk()) and (m.linkname.startswith("/") or ".." in Path(m.linkname).parts):
                raise RuntimeError(f"{asset}: unsafe link {m.name} -> {m.linkname}")
        extra = {"filter": "data"} if hasattr(tarfile, "data_filter") else {}
        t.extractall(target, members=members, **extra)


def install_cli(log=print) -> Path:
    """Download and unpack the pinned CLI for this platform unless it is already cached."""
    cached = cached_cli()
    if cached:
        return cached
    key = platform_key()
    if key not in ASSETS:
        raise RuntimeError(f"no SolidCraft {VERSION} CLI release for {key[0]} {key[1]}; "
                           "install solidcraft-cli yourself and put it on PATH or set SOLIDCRAFT_CLI")
    asset, sha256 = ASSETS[key]
    CACHE.mkdir(parents=True, exist_ok=True)
    archive = CACHE / asset
    if not archive.is_file():
        log(f"Downloading {asset} ...")
        _download(BASE_URL + asset, archive, sha256, log=log)
    target = install_dir()
    tmp = target.with_name(target.name + ".unpack")
    shutil.rmtree(tmp, ignore_errors=True)
    _extract(archive, tmp, asset)
    shutil.rmtree(target, ignore_errors=True)
    tmp.rename(target)
    archive.unlink()
    cli = cached_cli()
    if cli is None:
        raise RuntimeError(f"{asset}: no {exe_name()} in the archive")
    if sys.platform != "win32":
        for exe in cli.parent.iterdir():
            if exe.is_file():
                exe.chmod(exe.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return cli

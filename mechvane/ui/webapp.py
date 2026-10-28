"""The SolidCraft web app, served from the Mechvane UI server for the "Model" mode.

The release asset is downloaded once into a cache directory and checked against a pinned SHA256;
it is never checked into the repository. Set MECHVANE_SOLIDCRAFT_WEB to an unpacked build to use
that instead.
"""

import hashlib
import io
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path

from ..install import CACHE

VERSION = "0.25.1"
ASSET = f"solidcraft-web-{VERSION}.zip"
URL = f"https://github.com/tangency-labs/solidcraft/releases/download/v{VERSION}/{ASSET}"
SHA256 = "9a7b8ae8851d7f5777855b03818a4f349b3671b77a14e4e5ec153a902c66c5f9"

MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".wasm": "application/wasm",
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".json": "application/json",
    ".webmanifest": "application/manifest+json",
    ".ttf": "font/ttf",
    ".txt": "text/plain; charset=utf-8",
    ".md": "text/plain; charset=utf-8",
}


def webapp_dir(download: bool = True) -> Path | None:
    """Directory holding the unpacked web build (index.html), downloading it if needed."""
    env = os.environ.get("MECHVANE_SOLIDCRAFT_WEB")
    if env:
        return Path(env)
    target = CACHE / f"solidcraft-web-{VERSION}"
    if (target / "index.html").is_file():
        return target
    if not download:
        return None
    with urllib.request.urlopen(URL, timeout=120) as r:
        data = r.read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != SHA256:
        raise RuntimeError(f"{ASSET}: SHA256 {digest} does not match the pinned {SHA256}")
    tmp = CACHE / f".unpack-{VERSION}"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in z.namelist():
            if name.startswith("/") or ".." in Path(name).parts:
                raise RuntimeError(f"{ASSET}: unsafe path {name}")
        z.extractall(tmp)
    shutil.rmtree(target, ignore_errors=True)
    (tmp / f"solidcraft-web-{VERSION}").rename(target)
    shutil.rmtree(tmp, ignore_errors=True)
    return target


def resolve(rel: str) -> Path | None:
    """File of the web build for a path below /sc/, or None when outside it or missing."""
    root = webapp_dir(download=False)
    if root is None:
        return None
    root = root.resolve()
    target = (root / (rel or "index.html")).resolve()
    if root not in target.parents and target != root:
        return None
    return target if target.is_file() else None


def mime(path: Path) -> str:
    return MIME.get(path.suffix, "application/octet-stream")

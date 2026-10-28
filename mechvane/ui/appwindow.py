"""Open the web UI in its own app window and add a start menu entry.

The app window is a Chromium-based browser (Chrome, Edge, Chromium, Brave) started with `--app=<url>`
and a profile of its own, so it shows no tabs or address bar and keeps its size and position. When
that window is closed, the UI server stops too. Without such a browser the UI opens in the default
browser instead.
"""

import os
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

from .. import install

STATIC = Path(__file__).resolve().parent / "static"
# A browser process that ends this soon handed the window to an instance that was already open
HANDOFF_S = 3.0


def _windows_candidates() -> list[Path]:
    roots = [os.environ.get(k) for k in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")]
    rel = [r"Google\Chrome\Application\chrome.exe", r"Microsoft\Edge\Application\msedge.exe",
           r"BraveSoftware\Brave-Browser\Application\brave.exe", r"Chromium\Application\chrome.exe"]
    return [Path(root) / r for r in rel for root in roots if root]


def _mac_candidates() -> list[Path]:
    apps = ["Google Chrome", "Microsoft Edge", "Chromium", "Brave Browser"]
    return [Path(f"/Applications/{a}.app/Contents/MacOS/{a}") for a in apps]


LINUX_NAMES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
               "microsoft-edge", "microsoft-edge-stable", "brave-browser"]


def find_browser() -> str | None:
    """Path of a Chromium-based browser: $MECHVANE_BROWSER, else the first one installed."""
    if os.environ.get("MECHVANE_BROWSER"):
        return os.environ["MECHVANE_BROWSER"]
    if sys.platform == "win32":
        found = [p for p in _windows_candidates() if p.is_file()]
    elif sys.platform == "darwin":
        found = [p for p in _mac_candidates() if p.is_file()]
    else:
        found = [Path(w) for w in map(shutil.which, LINUX_NAMES) if w]
    return str(found[0]) if found else None


def app_command(browser: str, url: str) -> list[str]:
    profile = install.CACHE / "app-profile"
    return [browser, f"--app={url}", f"--user-data-dir={profile}", "--window-size=1400,900",
            "--no-first-run", "--no-default-browser-check"]


def open_window(url: str, on_close=None) -> bool:
    """Open url in an app window; on_close() runs when the user closes it. False: opened a browser tab."""
    browser = find_browser()
    if browser:
        try:
            proc = subprocess.Popen(app_command(browser, url), stdin=subprocess.DEVNULL,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            proc = None
        if proc is not None:
            started = time.monotonic()
            try:
                rc = proc.wait(timeout=HANDOFF_S)
            except subprocess.TimeoutExpired:
                rc = None
            if rc is None:
                if on_close:
                    threading.Thread(target=lambda: (proc.wait(), on_close()), daemon=True).start()
                return True
            if rc == 0 and time.monotonic() - started < HANDOFF_S:
                return True  # handed to the app window that was already open; the server keeps running
    webbrowser.open(url)
    return False


def _icon(name: str) -> Path:
    """Copy an icon out of the package into the cache, so the entry survives a reinstall."""
    install.CACHE.mkdir(parents=True, exist_ok=True)
    target = install.CACHE / name
    shutil.copyfile(STATIC / name, target)
    return target


def _launcher() -> str:
    """Python without a console window on Windows."""
    exe = Path(sys.executable)
    if sys.platform == "win32" and (exe.parent / "pythonw.exe").is_file():
        return str(exe.parent / "pythonw.exe")
    return str(exe)


def desktop_entry(folder: Path, icon: Path) -> str:
    return ("[Desktop Entry]\nType=Application\nName=Mechvane\n"
            "Comment=Parametric CAD: you and your agent on the same model\n"
            f"Exec=\"{_launcher()}\" -m mechvane ui \"{folder}\"\nIcon={icon}\n"
            "Terminal=false\nCategories=Graphics;Engineering;\n")


def create_shortcut(folder: Path) -> Path:
    """Start menu entry that opens the UI for folder. Returns the file written."""
    folder.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        programs = Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs"
        link = programs / "Mechvane.lnk"
        # Values go in through the environment, so paths with quotes or spaces need no escaping
        env = dict(os.environ, MV_LINK=str(link), MV_TARGET=_launcher(), MV_ARGS=f'-m mechvane ui "{folder}"',
                   MV_ICON=str(_icon("mechvane.ico")), MV_DIR=str(folder))
        script = ("$s = (New-Object -ComObject WScript.Shell).CreateShortcut($env:MV_LINK); "
                  "$s.TargetPath = $env:MV_TARGET; $s.Arguments = $env:MV_ARGS; "
                  "$s.IconLocation = $env:MV_ICON; $s.WorkingDirectory = $env:MV_DIR; "
                  "$s.Description = 'Mechvane'; $s.Save()")
        subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                       env=env, check=True, capture_output=True, timeout=60)
        return link
    if sys.platform == "darwin":
        raise RuntimeError("no start menu entry on macOS yet; run `mechvane ui` instead")
    apps = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "applications"
    apps.mkdir(parents=True, exist_ok=True)
    entry = apps / "mechvane.desktop"
    entry.write_text(desktop_entry(folder, _icon("logo.svg")), encoding="utf-8")
    return entry

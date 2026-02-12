"""Core features for offline wheel transfer through clipboard."""

from __future__ import annotations

import base64
import glob
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

__all__ = [
    "copy_wheels_to_clipboard",
    "download_wheels",
    "restore_to_temp_and_install",
]


_HEADER = "===MULTI_WHEEL_PACKAGE==="
_END = "===END==="
_NEXT = "---NEXT---"


def _copy_to_clipboard(text: str) -> None:
    """Copy text into the system clipboard."""
    system = platform.system()
    if system == "Windows":
        subprocess.run("clip", input=text.encode("utf-16le"), check=True)
    elif system == "Darwin":
        subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
    else:
        subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=text.encode("utf-8"),
            check=True,
        )


def _paste_from_clipboard() -> str:
    """Read text from the system clipboard."""
    system = platform.system()
    if system == "Windows":
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout

    if system == "Darwin":
        result = subprocess.run(["pbpaste"], capture_output=True, text=True, check=True)
        return result.stdout

    result = subprocess.run(
        ["xclip", "-selection", "clipboard", "-o"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def download_wheels(
    package_spec: str,
    dest_dir: str,
    include_deps: bool = True,
) -> list[str]:
    """Download wheel files for ``package_spec`` into ``dest_dir``."""
    os.makedirs(dest_dir, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "pip",
        "download",
        package_spec,
        "--only-binary=:all:",
        "--dest",
        dest_dir,
    ]
    if not include_deps:
        cmd.append("--no-deps")

    subprocess.run(cmd, check=True)

    wheels = sorted(glob.glob(os.path.join(dest_dir, "*.whl")))
    if not wheels:
        raise RuntimeError("No .whl files downloaded (possibly no wheel artifacts exist).")
    return wheels


def copy_wheels_to_clipboard(package_spec: str, include_deps: bool = True) -> str:
    """Download wheels and copy a base64 bundle into clipboard.

    Returns the generated payload text.
    """
    temp_dir = tempfile.mkdtemp(prefix="wheel_bundle_")
    wheels = download_wheels(package_spec, temp_dir, include_deps=include_deps)

    parts = [_HEADER, f"REQ: {package_spec}"]
    total_size = 0

    for i, path in enumerate(wheels):
        filename = os.path.basename(path)
        data = Path(path).read_bytes()
        total_size += len(data)
        b64 = base64.b64encode(data).decode("utf-8")

        parts.append(f"FILE: {filename}")
        parts.append(f"SIZE: {len(data)}")
        parts.append(f"DATA: {b64}")
        if i != len(wheels) - 1:
            parts.append(_NEXT)

    parts.append(_END)
    payload = "\n".join(parts)
    _copy_to_clipboard(payload)

    print("[OK] Copied wheels to clipboard")
    print(f"REQ: {package_spec}")
    print(f"Downloaded wheels: {len(wheels)} (include_deps={include_deps})")
    print(f"Total original size: {total_size / 1024 / 1024:.2f} MB")
    print(f"Total clipboard size: {len(payload) / 1024 / 1024:.2f} MB")

    return payload


def restore_to_temp_and_install(temp_dir: str = "temp", install_deps: bool = True) -> list[str]:
    """Restore wheels from clipboard into ``temp_dir`` and install offline.

    Returns restored wheel paths.
    """
    text = _paste_from_clipboard()
    if _HEADER not in text:
        raise ValueError("Invalid multi-wheel format: missing header")

    temp_path = Path(temp_dir)
    if temp_path.exists():
        shutil.rmtree(temp_path)
    temp_path.mkdir(parents=True, exist_ok=True)

    req = None
    for line in text.splitlines():
        item = line.strip()
        if item.startswith("REQ:"):
            req = item.split("REQ:", 1)[1].strip()
            break

    restored_paths: list[str] = []
    total_size = 0

    for block in text.split(_NEXT):
        chunk = block.strip()
        if not chunk:
            continue

        filename = None
        b64_data = None
        for line in chunk.splitlines():
            item = line.strip()
            if item.startswith("FILE:"):
                filename = item.split("FILE:", 1)[1].strip()
            elif item.startswith("DATA:"):
                b64_data = item.split("DATA:", 1)[1].strip()

        if not filename or not b64_data:
            continue

        data = base64.b64decode(b64_data)
        out_path = temp_path / filename
        out_path.write_bytes(data)

        restored_paths.append(str(out_path))
        total_size += len(data)

    if not restored_paths:
        raise ValueError("No wheels found in clipboard data")

    print(f"[OK] Restored {len(restored_paths)} wheels into '{temp_dir}'")
    print(f"Total size: {total_size / 1024 / 1024:.2f} MB")
    if req:
        print(f"REQ: {req}")

    print("[INFO] Installing offline...")
    common = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-index",
        "--find-links",
        str(temp_path),
    ]

    if install_deps:
        if req:
            subprocess.run([*common, req], check=True)
        else:
            subprocess.run([*common, *restored_paths], check=True)
    else:
        if len(restored_paths) == 1:
            subprocess.run([*common, restored_paths[0]], check=True)
        elif req:
            subprocess.run([*common, req, "--no-deps"], check=True)
        else:
            raise ValueError(
                "install_deps=False but cannot identify top-level wheel and REQ missing"
            )

    print("[OK] Installation complete.")
    return restored_paths

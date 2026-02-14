"""Core helpers for transferring wheel files through the system clipboard."""

from __future__ import annotations

import base64
import glob
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

__all__ = [
    "copy_wheels_to_clipboard",
    "restore_wheels_and_install",
    "restore_wheels_from_clipboard",
]


def copy_wheels_to_clipboard(
    package_spec: str, include_deps: bool = False
) -> dict[str, int | float]:
    """Download wheels and encode them into a clipboard payload."""
    temp_dir = tempfile.mkdtemp(prefix="wheel_bundle_")
    wheels = _download_wheels(package_spec, temp_dir, include_deps=include_deps)

    parts = [
        "===CLIPINSTALL_PACKAGE===",
        f"Package: {package_spec}",
        f"INCLUDE_DEPS: {str(include_deps).lower()}",
    ]
    total_size = 0

    for index, path in enumerate(wheels):
        filename = os.path.basename(path)
        data = Path(path).read_bytes()
        total_size += len(data)

        parts.append(f"FILE: {filename}")
        parts.append(f"SIZE: {len(data)}")
        parts.append(f"DATA: {base64.b64encode(data).decode('utf-8')}")
        if index != len(wheels) - 1:
            parts.append("---NEXT---")

    parts.append("===END===")
    text = "\n".join(parts)
    _copy_to_clipboard(text)

    return {
        "wheel_count": len(wheels),
        "original_size_mb": total_size / 1024 / 1024,
        "clipboard_size_mb": len(text) / 1024 / 1024,
    }


def restore_wheels_from_clipboard(
    temp_dir: str = "temp",
) -> tuple[str, bool, int, float]:
    """Restore wheel files from clipboard payload into *temp_dir*."""
    text = _paste_from_clipboard()
    if "===CLIPINSTALL_PACKAGE===" not in text:
        raise ValueError("Invalid package format: missing header")

    if os.path.exists(temp_dir) and not os.path.isdir(temp_dir):
        raise ValueError(f"Target path exists and is not a directory: {temp_dir}")

    os.makedirs(temp_dir, exist_ok=True)
    for wheel in glob.glob(os.path.join(temp_dir, "*.whl")):
        os.remove(wheel)

    pkg = None
    include_deps = False
    for line in text.splitlines():
        item = line.strip()
        if item.startswith("Package:"):
            pkg = item.split("Package:", 1)[1].strip()
        elif item.startswith("INCLUDE_DEPS:"):
            include_deps = item.split("INCLUDE_DEPS:", 1)[1].strip().lower() == "true"

    if pkg is None:
        raise ValueError("missing package spec")

    restored = 0
    total_size = 0

    for block in text.split("---NEXT---"):
        filename = None
        b64_data = None
        for line in block.splitlines():
            item = line.strip()
            if item.startswith("FILE:"):
                filename = item.split("FILE:", 1)[1].strip()
            elif item.startswith("DATA:"):
                b64_data = item.split("DATA:", 1)[1].strip()

        if not filename or not b64_data:
            continue

        data = base64.b64decode(b64_data)
        Path(temp_dir, filename).write_bytes(data)
        restored += 1
        total_size += len(data)

    if restored == 0:
        raise ValueError("No wheels found in clipboard data")

    return pkg, include_deps, restored, total_size / 1024 / 1024


def restore_wheels_and_install(
    temp_dir: str = "temp", force_reinstall: bool = True
) -> tuple[str, int, float]:
    """Restore wheels from clipboard and install them offline."""
    pkg, install_deps, restored, size_mb = restore_wheels_from_clipboard(
        temp_dir=temp_dir
    )
    _install_wheels(
        temp_dir=temp_dir,
        pkg=pkg,
        install_deps=install_deps,
        force_reinstall=force_reinstall,
    )
    return pkg, restored, size_mb


def _install_wheels(
    temp_dir: str,
    pkg: str,
    install_deps: bool = True,
    force_reinstall: bool = True,
) -> None:
    """Install restored wheel files from *temp_dir* without network."""
    common = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-index",
        "--find-links",
        temp_dir,
    ]
    if force_reinstall:
        common.append("--force-reinstall")

    if install_deps:
        subprocess.run([*common, pkg], check=True)

    wheels = sorted(glob.glob(os.path.join(temp_dir, "*.whl")))
    if len(wheels) == 1:
        subprocess.run([*common, wheels[0]], check=True)
    else:
        subprocess.run([*common, pkg, "--no-deps"], check=True)


def _copy_to_clipboard(text: str) -> None:
    """Copy text to the system clipboard."""
    system = platform.system()
    if system == "Windows":
        subprocess.run("clip", input=text.encode("utf-16le"), check=True)
    elif system == "Darwin":
        subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
    else:
        subprocess.run(
            ["xclip", "-selection", "clipboard"], input=text.encode("utf-8"), check=True
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
    elif system == "Darwin":
        result = subprocess.run(["pbpaste"], capture_output=True, text=True, check=True)
    else:
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o"],
            capture_output=True,
            text=True,
            check=True,
        )
    return result.stdout


def _download_wheels(
    package_spec: str, dest_dir: str, include_deps: bool = False
) -> list[str]:
    """Download wheel files for *package_spec* into *dest_dir*."""
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
        raise RuntimeError(
            "No .whl files downloaded (it may have fallen back to source)."
        )
    return wheels

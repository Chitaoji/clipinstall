"""
Core helpers for transferring wheel files through the system clipboard.

NOTE: this module is private. All functions and objects are available in the main
`clipinstall` namespace - use that instead.

"""

from __future__ import annotations

import base64
import glob
import io
import os
import platform
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

__all__ = [
    "copy_files_to_clipboard",
    "copy_wheels_to_clipboard",
    "restore_files_from_clipboard",
    "restore_payload_from_clipboard",
    "restore_wheels_and_install",
    "restore_wheels_from_clipboard",
]


def copy_wheels_to_clipboard(
    package_spec: str, include_deps: bool = False
) -> dict[str, int | float]:
    """Download wheels and encode them into a clipboard payload."""
    temp_dir = tempfile.mkdtemp(prefix="wheel_bundle_")
    package_spec, wheels = _download_wheels(
        package_spec, temp_dir, include_deps=include_deps
    )

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


def copy_files_to_clipboard(path_spec: str) -> dict[str, int | float | str]:
    """Archive a file/folder and encode it into a clipboard payload."""
    source = Path(path_spec).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Path not found: {source}")

    source_type = "dir" if source.is_dir() else "file"
    file_count = 0
    total_size = 0

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        if source.is_file():
            archive.write(source, arcname=source.name)
            file_count = 1
            total_size = source.stat().st_size
        else:
            root = source.parent
            for child in sorted(source.rglob("*")):
                arcname = str(child.relative_to(root))
                if child.is_dir():
                    archive.writestr(f"{arcname}/", "")
                    continue
                archive.write(child, arcname=arcname)
                file_count += 1
                total_size += child.stat().st_size

    zip_bytes = buffer.getvalue()
    payload = "\n".join(
        [
            "===CLIPINSTALL_COPY===",
            f"SOURCE: {source.name}",
            f"TYPE: {source_type}",
            f"FILE_COUNT: {file_count}",
            f"ZIP_DATA: {base64.b64encode(zip_bytes).decode('utf-8')}",
            "===END===",
        ]
    )
    _copy_to_clipboard(payload)

    return {
        "source": source.name,
        "source_type": source_type,
        "file_count": file_count,
        "original_size_mb": total_size / 1024 / 1024,
        "clipboard_size_mb": len(payload) / 1024 / 1024,
    }


def restore_wheels_from_clipboard(
    temp_dir: str = "temp",
) -> tuple[str, bool, int, float]:
    """Restore wheel files from clipboard payload into *temp_dir*."""
    text = _paste_from_clipboard()
    if "===CLIPINSTALL_COPY===" in text:
        raise ValueError(
            "Clipboard contains copied files/folders data, not package wheels. "
            "Use 'clipin paste' instead of 'clipin install'."
        )
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


def restore_files_from_clipboard(
    target_dir: str = "temp",
) -> tuple[str, str, int, float]:
    """Restore copied file/folder payload into *target_dir*."""
    text = _paste_from_clipboard()
    if "===CLIPINSTALL_COPY===" not in text:
        raise ValueError("Invalid copy format: missing header")

    source_name = ""
    source_type = "file"
    zip_b64 = None
    for line in text.splitlines():
        item = line.strip()
        if item.startswith("SOURCE:"):
            source_name = item.split("SOURCE:", 1)[1].strip()
        elif item.startswith("TYPE:"):
            source_type = item.split("TYPE:", 1)[1].strip()
        elif item.startswith("ZIP_DATA:"):
            zip_b64 = item.split("ZIP_DATA:", 1)[1].strip()

    if not zip_b64:
        raise ValueError("Invalid copy format: missing ZIP_DATA")

    os.makedirs(target_dir, exist_ok=True)
    zip_bytes = base64.b64decode(zip_b64)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        archive.extractall(path=target_dir)
        restored_files = len([name for name in archive.namelist() if not name.endswith("/")])

    return source_name, source_type, restored_files, len(zip_bytes) / 1024 / 1024


def restore_payload_from_clipboard(
    target_dir: str = "temp",
) -> dict[str, int | float | str | bool]:
    """Restore either wheels or copied files based on clipboard payload header."""
    text = _paste_from_clipboard()
    if "===CLIPINSTALL_PACKAGE===" in text:
        pkg, include_deps, restored, size_mb = restore_wheels_from_clipboard(
            temp_dir=target_dir
        )
        return {
            "payload_type": "package",
            "name": pkg,
            "include_deps": include_deps,
            "restored_count": restored,
            "size_mb": size_mb,
        }
    if "===CLIPINSTALL_COPY===" in text:
        source, source_type, restored, size_mb = restore_files_from_clipboard(
            target_dir=target_dir
        )
        return {
            "payload_type": "copy",
            "name": source,
            "source_type": source_type,
            "restored_count": restored,
            "size_mb": size_mb,
        }
    raise ValueError("Invalid clipboard format: unsupported header")


def restore_wheels_and_install(
    temp_dir: str = "temp",
    force_reinstall: bool = True,
    extract_module_files: bool = False,
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
    if extract_module_files:
        _extract_module_python_files(temp_dir=temp_dir, pkg=pkg)
    return pkg, restored, size_mb


def _install_wheels(
    temp_dir: str,
    pkg: str,
    install_deps: bool = True,
    force_reinstall: bool = True,
) -> None:
    """Install restored wheel files from *temp_dir* without network."""
    if force_reinstall:
        package_name = _extract_package_name(pkg)
        if _is_package_installed(package_name):
            subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", "-y", package_name],
                check=False,
            )

    common = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-index",
        "--find-links",
        temp_dir,
    ]

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
) -> tuple[str, list[str]]:
    """Download wheel files for *package_spec* into *dest_dir*."""
    local_path = Path(package_spec).expanduser()
    local_wheel = (
        local_path
        if local_path.is_file() and local_path.suffix.lower() == ".whl"
        else None
    )
    local_dir = local_path if local_path.is_dir() else None

    if local_dir is not None:
        package_spec = _build_latest_local_wheel(local_dir)

    os.makedirs(dest_dir, exist_ok=True)

    if local_wheel is not None:
        copied = Path(dest_dir, local_wheel.name)
        copied.write_bytes(local_wheel.read_bytes())

        name, version = _extract_name_and_version_from_wheel(local_wheel)
        package_spec = f"{name}=={version}"

        if include_deps:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "download",
                    package_spec,
                    "--only-binary=:all:",
                    "--dest",
                    dest_dir,
                ],
                check=True,
            )
    else:
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
    if local_dir is not None:
        name, version = _extract_name_and_version_from_wheel(Path(package_spec))
        package_spec = f"{name}=={version}"
    return package_spec, wheels


def _build_latest_local_wheel(package_dir: Path) -> str:
    """Build *package_dir* via install.py and return newest wheel in dist/."""
    install_script = package_dir / "install.py"
    if not install_script.is_file():
        raise RuntimeError(f"install.py not found in directory: {package_dir}")

    subprocess.run([sys.executable, str(install_script)], check=True, cwd=package_dir)

    dist_dir = package_dir / "dist"
    wheels = [path for path in dist_dir.glob("*.whl") if path.is_file()]
    if not wheels:
        raise RuntimeError(f"No .whl files found in dist directory: {dist_dir}")

    latest_wheel = max(wheels, key=lambda item: item.stat().st_mtime)
    return str(latest_wheel)


def _is_package_installed(package_name: str) -> bool:
    """Check whether *package_name* is already installed in current environment."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", package_name],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _extract_module_python_files(temp_dir: str, pkg: str) -> None:
    """Extract package .py module files into *temp_dir* for inspection/reuse."""
    package_name = _extract_package_name(pkg)
    normalized = package_name.lower().replace("-", "_")

    candidates = sorted(glob.glob(os.path.join(temp_dir, "*.whl")))
    target_wheel = next(
        (
            wheel
            for wheel in candidates
            if os.path.basename(wheel).lower().startswith(f"{normalized}-")
        ),
        None,
    )

    if target_wheel is None:
        return

    with zipfile.ZipFile(target_wheel) as archive:
        for member in archive.infolist():
            if member.is_dir() or not member.filename.endswith(".py"):
                continue
            if ".dist-info/" in member.filename:
                continue
            archive.extract(member, path=temp_dir)


def _extract_package_name(package_spec: str) -> str:
    """Extract package name from package spec text for pip uninstall."""
    match = re.match(r"^([A-Za-z0-9_.-]+)", package_spec.strip())
    if not match:
        raise ValueError(f"Invalid package spec: {package_spec}")
    return match.group(1)


def _extract_name_and_version_from_wheel(wheel_path: Path) -> tuple[str, str]:
    """Extract package name and version from a wheel filename."""
    parts = wheel_path.name.split("-")
    if len(parts) < 5:
        raise ValueError(f"Invalid wheel filename: {wheel_path.name}")

    name = parts[0].replace("_", "-")
    version = parts[1]
    return name, version

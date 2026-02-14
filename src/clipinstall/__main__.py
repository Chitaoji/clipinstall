"""CLI for clipinstall."""

from __future__ import annotations

import glob
import os
import shutil

import click

from .core import (
    copy_wheels_to_clipboard,
    restore_wheels_and_install,
    restore_wheels_from_clipboard,
)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def run() -> None:
    """Install Python packages through clipboard-transferred wheels."""


@run.command()
@click.argument("package_spec")
@click.option("--deps/--no-deps", "include_deps", default=False, show_default=True)
def copy(package_spec: str, include_deps: bool) -> None:
    """Download wheels for PACKAGE_SPEC and copy them into clipboard."""
    stats = copy_wheels_to_clipboard(
        package_spec=package_spec, include_deps=include_deps
    )
    click.echo("[OK] Copied wheels to clipboard")
    click.echo(f"Package: {package_spec}")
    click.echo(
        f"Downloaded wheels: {stats['wheel_count']} (include_deps={include_deps})"
    )
    click.echo(f"Total original size: {stats['original_size_mb']:.2f} MB")
    click.echo(f"Total clipboard size: {stats['clipboard_size_mb']:.2f} MB")


@run.command()
@click.option("--dir", "target_dir", default="temp", show_default=True)
@click.option("--clean/--no-clean", default=True, show_default=True)
@click.option("--force/--no-force", default=True, show_default=True)
def install(target_dir: str, clean: bool, force: bool) -> None:
    """Restore wheels from clipboard and install them offline."""
    target_dir_exists = os.path.isdir(target_dir)

    pkg, restored, size_mb = restore_wheels_and_install(
        temp_dir=target_dir, force_reinstall=force
    )
    click.echo(f"[OK] Restored {restored} wheels into '{target_dir}'")
    click.echo(f"Total size: {size_mb:.2f} MB")
    if pkg:
        click.echo(f"Package: {pkg}")
    click.echo("[OK] Installation complete.")

    if clean:
        if target_dir_exists:
            for wheel in glob.glob(os.path.join(target_dir, "*.whl")):
                os.remove(wheel)
            click.echo(
                f"[OK] Cleaned restored wheels from existing directory: {target_dir}"
            )
        else:
            shutil.rmtree(target_dir, ignore_errors=True)
            click.echo(f"[OK] Removed temp directory: {target_dir}")


@run.command()
@click.option("--dir", "target_dir", default="temp", show_default=True)
def paste(target_dir: str) -> None:
    """Restore wheels from clipboard into a folder without installing."""
    pkg, _, restored, size_mb = restore_wheels_from_clipboard(temp_dir=target_dir)
    click.echo(f"[OK] Restored {restored} wheels into '{target_dir}'")
    click.echo(f"Total size: {size_mb:.2f} MB")
    if pkg:
        click.echo(f"Package: {pkg}")
    click.echo("[OK] Paste complete (no installation performed).")

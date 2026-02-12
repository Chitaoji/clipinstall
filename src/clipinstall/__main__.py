"""CLI for clipinstall."""

from __future__ import annotations

import click

from .core import copy_wheels_to_clipboard, restore_wheels_and_install


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def run() -> None:
    """Install Python packages through clipboard-transferred wheels."""


@run.command("copy")
@click.argument("package_spec")
@click.option("--deps/--no-deps", "include_deps", default=False, show_default=True)
def copy_cmd(package_spec: str, include_deps: bool) -> None:
    """Download wheels for PACKAGE_SPEC and copy them into clipboard."""
    stats = copy_wheels_to_clipboard(
        package_spec=package_spec, include_deps=include_deps
    )
    click.echo("[OK] Copied wheels to clipboard")
    click.echo(f"REQ: {package_spec}")
    click.echo(
        f"Downloaded wheels: {stats['wheel_count']} (include_deps={include_deps})"
    )
    click.echo(f"Total original size: {stats['original_size_mb']:.2f} MB")
    click.echo(f"Total clipboard size: {stats['clipboard_size_mb']:.2f} MB")


@run.command("install")
@click.option("--temp-dir", default="temp", show_default=True)
def install_cmd(temp_dir: str) -> None:
    """Restore wheels from clipboard and install them offline."""
    req, restored, size_mb = restore_wheels_and_install(temp_dir=temp_dir)
    click.echo(f"[OK] Restored {restored} wheels into '{temp_dir}'")
    click.echo(f"Total size: {size_mb:.2f} MB")
    if req:
        click.echo(f"REQ: {req}")
    click.echo("[OK] Installation complete.")

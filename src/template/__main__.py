"""CLI for clipboard-based wheel transfer."""

from __future__ import annotations

import click

from .core import copy_wheels_to_clipboard, restore_to_temp_and_install


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def run() -> None:
    """Transfer wheel packages through clipboard for offline installation."""


@run.command("copy")
@click.argument("package_spec")
@click.option(
    "--no-deps",
    is_flag=True,
    default=False,
    help="Download only the top-level package wheel.",
)
def copy_cmd(package_spec: str, no_deps: bool) -> None:
    """Download wheel(s) and copy a transferable payload to clipboard."""
    copy_wheels_to_clipboard(package_spec, include_deps=not no_deps)


@run.command("install")
@click.option("--temp-dir", default="temp", show_default=True)
@click.option(
    "--no-deps",
    is_flag=True,
    default=False,
    help="Install without dependency resolution.",
)
def install_cmd(temp_dir: str, no_deps: bool) -> None:
    """Restore wheels from clipboard and install them offline."""
    restore_to_temp_and_install(temp_dir=temp_dir, install_deps=not no_deps)


if __name__ == "__main__":
    run()

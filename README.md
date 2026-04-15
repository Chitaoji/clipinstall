# clipinstall
Install packages on an offline machine through clipboard.

## Installation
```sh
$ pip install clipinstall
```

## Requirements
```txt
click
```

## Usage
```sh
# 1) Download the package and copy it to clipboard on an online machine
clipin download requests==2.32.3

# Optional: download with dependencies
clipin download requests==2.32.3 --deps

# Local build mode: if PACKAGE_SPEC is a folder, run install.py in it and copy
# the newest wheel under dist/
clipin download /path/to/your/project

# Direct wheel mode: copy an existing .whl file
clipin download /path/to/dist/your_pkg-1.0.0-py3-none-any.whl

# 2) (New) Copy a normal file/folder without package installation
clipin copy /path/to/file_or_folder

# Restore copied files/folders from clipboard on an offline machine
clipin paste --dir temp

# 3) Restore wheels from clipboard and install them on the target machine
clipin install

# Optional: specify the temp dir to store .whl files, the temp dir will be removed after 
# successful installation
clipin install --dir temp

# Optional: don't remove the temp files after installation
clipin install --no-clean

# Optional: extract module .py files from the installed package wheel into --dir
# (these files are kept and not removed)
clipin install --extract

# 4) Restore wheels from clipboard only (without installation)
clipin paste

# Optional: specify the dir to store .whl files
clipin paste --dir temp
```

## See Also
### Github repository
* https://github.com/Chitaoji/clipinstall/

### PyPI project
* https://pypi.org/project/clipinstall/

## License
This project falls under the BSD 3-Clause License.

## History
### v0.0.5
* `clipin install`:
    * New option `--extract/--no-extract` to extract package module
      `.py` files into `--dir` and keep them.

### next
* New command `clipin copy PATH` to copy a normal local file/folder through clipboard.
* `clipin paste` now supports both package wheel payloads and generic file/folder payloads.
* `clipin install` rejects generic file/folder payloads and asks to use `clipin paste`.

### v0.0.4
* Bugfix for `v0.0.3`.

### v0.0.3
* Removed `__version__`, use `importlib.metadata.version(__name__)` instead.

### v0.0.2
* Local build mode: can download from local folder now.
* `clipin install`:
    * New option `--force/--no-force` to reinstall the package if exists.

### v0.0.1
* New subcommand `clipin paste` to restore wheels from clipboard only (without installation).
* `clipin install`: 
    * renamed option `--temp-dir` to `--dir` for convenience.
    * new option `--clean/--no-clean` to determine whether temp files should be removed after installation.

### v0.0.0
* Initial release.

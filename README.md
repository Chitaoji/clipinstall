# clipinstall
Install packages through clipboard.

## Installation
```sh
*auto-generated*
```

## Requirements
```txt
*auto-generated*
```

## Usage
```sh
# 1) Download wheels and copy them to clipboard on an online machine (includes deps by default)
clip copy "requests==2.32.3"

# 2) Restore wheels from clipboard and install offline on the target machine
clip install --temp-dir temp

# Optional: copy only the top-level package wheel
clip copy "requests==2.32.3" --no-deps

# Optional: install without dependency resolution
clip install --no-deps
```

Notes:
- `clip copy` encodes wheel files into the clipboard text payload.
- `clip install` restores `.whl` files to a temporary directory and installs with `pip --no-index --find-links`.

## See Also
### Github repository
* *auto-generated*

### PyPI project
* *auto-generated*

## License
*auto-generated*

## History
### v0.0.0
* Initial release.

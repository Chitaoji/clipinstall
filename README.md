# clipinstall
Install packages through clipboard.

## Installation
```sh
$ pip install clipinstall
```

## Requirements
```txt
click
```

## Usage
### CLI Command
```sh
# 1) Online machine: download the package and copy it to clipboard
clip copy "requests==2.32.3"

# Optional: download with dependencies
clip copy "requests==2.32.3" --deps

# 2) Offline machine: restore wheels from clipboard and install them
clip install

# Optional: specify the temp dir to store .whl files
clip install --temp-dir temp
```

## See Also
### Github repository
* https://github.com/Chitaoji/clipinstall/

### PyPI project
* https://pypi.org/project/clipinstall/

## License
This project falls under the BSD 3-Clause License.

## History
### v0.0.0
* Initial release.

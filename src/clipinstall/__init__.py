"""
# clipinstall
Install packages on an offline machine through clipboard.

## Usage
### CLI Command
```sh
# 1) Download the package and copy it to clipboard on an online machine
clipin copy requests==2.32.3

# Optional: download with dependencies
clipin copy requests==2.32.3 --deps

# 2) Restore wheels from clipboard and install them on the target machine
clipin install

# Optional: specify the temp dir to store .whl files
clipin install --dir temp

# Optional: remove temp files after successful install
clipin install --clean

# 3) Restore wheels from clipboard only (no installation)
clipin paste

# Optional: specify destination dir when pasting only
clipin paste --dir temp
```

## See Also
### Github repository
* https://github.com/Chitaoji/clipinstall/

### PyPI project
* https://pypi.org/project/clipinstall/

## License
This project falls under the BSD 3-Clause License.

"""

from . import core
from .__version__ import __version__
from .core import *

__all__: list[str] = []
__all__.extend(core.__all__)

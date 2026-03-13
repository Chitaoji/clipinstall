"""
# clipinstall
Install packages on an offline machine through clipboard.

## Usage
```sh
# 1) Download the package and copy it to clipboard on an online machine
clipin copy requests==2.32.3

# Optional: download with dependencies
clipin copy requests==2.32.3 --deps

# Local build mode: if PACKAGE_SPEC is a folder, run install.py in it and copy
# the newest wheel under dist/
clipin copy /path/to/your/project

# Direct wheel mode: copy an existing .whl file
clipin copy /path/to/dist/your_pkg-1.0.0-py3-none-any.whl

# 2) Restore wheels from clipboard and install them on the target machine
clipin install

# Optional: specify the temp dir to store .whl files, the temp dir will be removed after
# successful installation
clipin install --dir temp

# Optional: don't remove the temp files after installation
clipin install --no-clean

# Optional: extract module .py files from the installed package wheel into --dir
# (these files are kept and not removed)
clipin install --extract

# 3) Restore wheels from clipboard only (without installation)
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

"""

from . import core
from .core import *

__all__: list[str] = []
__all__.extend(core.__all__)

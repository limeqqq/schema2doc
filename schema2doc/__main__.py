"""Allow running the package with `python -m schema2doc`."""

import sys

from .cli import main


if __name__ == "__main__":
    sys.exit(main())

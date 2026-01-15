import sys
from pathlib import Path

# Ensure repository root is on sys.path so imports like `utils.*` work when
# running tests without installing the project as a package.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import os
import sys
from pathlib import Path

# Ensure repository root is importable
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Default sane env for tests
os.environ.setdefault("OLYMPUS_DB_PATH", str(ROOT / ".data" / "olympus.db"))
os.makedirs(Path(os.environ["OLYMPUS_DB_PATH"]).parent, exist_ok=True)


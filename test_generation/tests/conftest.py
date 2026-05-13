import sys
from pathlib import Path

# Add repo root so that "from test_generation.src.xxx" imports work
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

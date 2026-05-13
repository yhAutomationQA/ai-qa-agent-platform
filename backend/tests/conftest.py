import sys
from pathlib import Path

# Add project root so that "from agents.src.xxx" imports work
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

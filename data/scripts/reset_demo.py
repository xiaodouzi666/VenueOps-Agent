from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "api"))

from app.tools.simulation_tools import reset_demo_data


if __name__ == "__main__":
    print(reset_demo_data())

from pathlib import Path
from typing import Any

import toml


def ensure_dir(path: Path):
    """Create directory recursively."""
    path.mkdir(parents=True, exist_ok=True)


def write_toml(path: Path, data: dict[str, Any]):
    """Write TOML dict to file, ensuring info comes before courses."""
    ensure_dir(path.parent)

    with open(path, "w", encoding="utf-8") as f:
        if "info" in data:
            info_data = {key: data["info"][key] for key in sorted(data["info"].keys())}
            toml.dump({"info": info_data}, f)
            f.write("\n")

        if "courses" in data:
            toml.dump({"courses": data["courses"]}, f)

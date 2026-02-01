from pathlib import Path
from typing import Any

import toml


def ensure_dir(path: Path):
    """Create directory recursively."""
    path.mkdir(parents=True, exist_ok=True)


def write_toml(path: Path, data: dict[str, Any]):
    """Write TOML dict to file, ensuring info comes before courses."""
    ensure_dir(path.parent)

    # We use a custom order: info first, then courses.
    # The toml library might not preserve order, so we write [info] manually
    # and then use dump for the rest to ensure it's valid TOML.

    with open(path, "w", encoding="utf-8") as f:
        if "info" in data:
            f.write("[info]\n")
            info_data = data["info"]
            # Sort keys for consistency
            for key in sorted(info_data.keys()):
                val = info_data[key]
                if isinstance(val, str):
                    f.write(f'{key} = "{val}"\n')
                else:
                    f.write(f"{key} = {val}\n")
            f.write("\n")

        if "courses" in data:
            # We only dump the courses part
            toml.dump({"courses": data["courses"]}, f)

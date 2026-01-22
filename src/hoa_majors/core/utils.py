import tomllib
from collections.abc import Generator
from pathlib import Path
from typing import Any

from hoa_majors.config import PLANS_SUBDIR


def normalize_course_code(code: str) -> str:
    """
    Normalize course code: trim whitespace, convert to uppercase, and remove trailing 'E' for consistency.
    """
    code = code.strip().upper()
    if code.endswith("E"):
        return code[:-1]
    return code


def iter_toml_files(data_dir: Path) -> Generator[tuple[Path, dict[str, Any]], None, None]:
    """遍历所有的 TOML 数据文件"""
    root = data_dir / PLANS_SUBDIR
    if not root.exists():
        return

    for f in root.rglob("*.toml"):
        try:
            with open(f, "rb") as fb:
                yield f, tomllib.load(fb)
        except Exception:
            continue

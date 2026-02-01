import tomllib
from pathlib import Path

from hoa_cli.config import logger


def load_lookup_table(data_dir: Path) -> dict:
    """Load the lookup_table.toml file"""
    lookup_path = data_dir / "lookup_table.toml"
    if not lookup_path.exists():
        logger.warning(f"Lookup table not found at {lookup_path}")
        return {}
    try:
        with open(lookup_path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        logger.error(f"Failed to load lookup table: {e}")
        return {}


def get_repo_id(plan_id: str, course_code: str, data_dir: Path) -> str:
    """
    获取课程对应的 OpenAuto 仓库 ID。

    逻辑：
    1. 如果 course_code 不在 lookup table 中 -> 返回 course_code
    2. 如果该 course_code 下存在 plan_id 对应的 key -> 返回该 value
    3. 如果该 course_code 下存在 DEFAULT key -> 返回 DEFAULT 对应的 value
    4. 否则 -> 返回 course_code
    """
    lookup = load_lookup_table(data_dir)

    if course_code not in lookup:
        return course_code

    mapping = lookup[course_code]

    if plan_id in mapping:
        return mapping[plan_id]
    elif "DEFAULT" in mapping:
        return mapping["DEFAULT"]
    else:
        return course_code


def run(args):
    """Entry point for the repo command"""
    repo_id = get_repo_id(args.plan_id, args.course_code, args.data_dir)
    print(repo_id)

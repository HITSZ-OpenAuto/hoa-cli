import argparse
import sys
from pathlib import Path

from hoa_cli.config import DEFAULT_DATA_DIR, logger
from hoa_cli.core.utils import iter_toml_files


def list_plans(data_dir: Path):
    plans = {}

    for _, data in iter_toml_files(data_dir):
        info = data.get("info", {})
        plan_id = info.get("plan_ID")
        if plan_id:
            plans[plan_id] = {
                "year": info.get("year", "N/A"),
                "major_code": info.get("major_code", "N/A"),
                "major_name": info.get("major_name", "N/A"),
                "school": info.get("school_name", "N/A"),
            }

    if not plans:
        logger.error("未找到任何培养方案数据。")
        sys.exit(1)

    # print(f"{'方案 ID (plan_ID)':<35} | {'年级':<5} | {'专业名称'}")
    # print("-" * 80)

    # 按年级和专业名称排序
    sorted_plans = sorted(plans.items(), key=lambda x: (x[1]["year"], x[1]["major_name"]))

    for pid, details in sorted_plans:
        print(f"{pid} {details['year']} {details['major_code']} {details['major_name']}")

    # print("-" * 80)
    # print(f"共计 {len(plans)} 个培养方案")


def main():
    parser = argparse.ArgumentParser(description="列出所有已抓取的培养方案")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="数据存储目录")
    args = parser.parse_args()

    list_plans(args.data_dir)


if __name__ == "__main__":
    main()

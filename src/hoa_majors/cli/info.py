import argparse
import sys
from pathlib import Path

from hoa_majors.config import DEFAULT_DATA_DIR, logger
from hoa_majors.core.utils import iter_toml_files


def get_course_info(plan_id: str, course_code: str, data_dir: Path):
    found_plan = False
    found_course = False

    for _, data in iter_toml_files(data_dir):
        if data.get("info", {}).get("plan_ID") == plan_id:
            found_plan = True
            for course in data.get("courses", []):
                if course.get("course_code") == course_code:
                    found_course = True
                    print(f"\n培养方案 {plan_id} 中的课程 {course_code} 详细信息:")
                    print("=" * 60)
                    # 打印核心字段
                    for key, value in course.items():
                        if key != "hours":
                            print(f"{key.replace('_', ' ').title():<25}: {value}")

                    # 打印学时子表
                    if "hours" in course:
                        print("-" * 60)
                        print("学时分配:")
                        for h_key, h_val in course["hours"].items():
                            print(f"  {h_key.title():<23}: {h_val}")
                    print("=" * 60)
                    break
            if found_course:
                break

    if not found_plan:
        logger.error(f"未找到 ID 为 {plan_id} 的培养方案")
        sys.exit(1)
    elif not found_course:
        logger.error(f"在培养方案 {plan_id} 中未找到课程 {course_code}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="获取培养方案中特定课程的详细信息")
    parser.add_argument("plan_id", help="培养方案 ID (fah)")
    parser.add_argument("course_code", help="课程代码")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="数据存储目录")
    args = parser.parse_args()

    get_course_info(args.plan_id, args.course_code, args.data_dir)


if __name__ == "__main__":
    main()

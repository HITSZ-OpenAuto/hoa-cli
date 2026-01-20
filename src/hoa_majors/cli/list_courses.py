import argparse
from pathlib import Path

from hoa_majors.config import DEFAULT_DATA_DIR
from hoa_majors.core.utils import iter_toml_files


def list_courses(plan_id: str, data_dir: Path):
    found = False

    for _, data in iter_toml_files(data_dir):
        if data.get("info", {}).get("plan_ID") == plan_id:
            found = True
            info = data.get("info", {})
            print(f"专业: {info.get('major_name')} ({info.get('year')} 年级)")
            print(f"方案 ID: {plan_id}")
            print(f"{'课程代码':<12} | {'课程名称'}")
            print("-" * 50)
            for course in data.get("courses", []):
                code = course.get("course_code", "N/A")
                name = course.get("course_name", "N/A")
                print(f"{code:<12} | {name}")
            break

    if not found:
        print(f"未找到 ID 为 {plan_id} 的培养方案")


def main():
    parser = argparse.ArgumentParser(description="列出特定培养方案的所有课程")
    parser.add_argument("plan_id", help="培养方案 ID (fah)")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="数据存储目录")
    args = parser.parse_args()

    list_courses(args.plan_id, args.data_dir)


if __name__ == "__main__":
    main()

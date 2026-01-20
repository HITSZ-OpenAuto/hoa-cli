import tomllib
from pathlib import Path

HEADER_COMMENT = '''"""
课程代码查找表

数据结构:
    LOOKUP_TABLE: dict[tuple[str, str], str]

    键 (Key): tuple[str, str]
        - 第一个元素: 课程代码 (course_code)，如 "COMP1003"
        - 第二个元素: 培养方案号 (plan_id/fah)
          - 空字符串 "" 表示该课程在所有培养方案中通用
          - 非空字符串表示特定专业的培养方案号

    值 (Value): str
        - 对应的 OpenAuto 仓库 ID (repo_id)

维护说明:
    - 此文件由 hoa_majors.cli.table 维护
"""

'''


def extract_courses(data_dir: Path) -> set[str]:
    all_courses = set()
    school_majors_path = data_dir / "SCHOOL_MAJORS"
    for toml_file in school_majors_path.rglob("*.toml"):
        try:
            with open(toml_file, "rb") as f:
                data = tomllib.load(f)
            if "courses" in data:
                for course in data["courses"]:
                    if "course_code" in course:
                        all_courses.add(course["course_code"])
        except Exception as e:
            print(f"处理文件 {toml_file} 时出错: {e}")
    return all_courses


def write_table(table: dict[tuple[str, str], str], output_file: Path):
    lines = [HEADER_COMMENT + "LOOKUP_TABLE: dict[tuple[str, str], str] = {"]
    for (course, plan), repo_id in sorted(table.items(), key=lambda x: x[0][0]):
        lines.append(f'    ("{course}", "{plan}"): "{repo_id}",')
    lines.append("}")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def init_table(data_dir: Path, output_file: Path):
    courses = extract_courses(data_dir)
    table = {(code, ""): code for code in courses}
    write_table(table, output_file)
    print(f"Initialized table with {len(courses)} courses at {output_file}")


def update_table(data_dir: Path, table_file: Path):
    if not table_file.exists():
        init_table(data_dir, table_file)
        return

    # Import existing table
    import importlib.util

    spec = importlib.util.spec_from_file_location("lookup_data", table_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    existing_table = getattr(module, "LOOKUP_TABLE", {})

    all_courses = extract_courses(data_dir)
    existing_courses = {course for course, _ in existing_table.keys()}
    new_courses = all_courses - existing_courses

    if not new_courses:
        print("No new courses found.")
        return

    for code in new_courses:
        existing_table[(code, "")] = code

    write_table(existing_table, table_file)
    print(f"Updated table with {len(new_courses)} new courses at {table_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate or update the lookup table.")
    parser.add_argument("action", choices=["init", "update"], help="Action to perform.")
    parser.add_argument(
        "--data-dir", type=Path, default=Path("data"), help="Directory where data is stored."
    )
    parser.add_argument("--output-file", type=Path, help="Path to the lookup table file.")
    args = parser.parse_args()

    table_file = args.output_file or args.data_dir / "lookup_table.py"

    if args.action == "init":
        init_table(args.data_dir, table_file)
    else:
        update_table(args.data_dir, table_file)


if __name__ == "__main__":
    main()

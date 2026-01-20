import argparse
from pathlib import Path

from hoa_majors.config import DEFAULT_DATA_DIR, logger
from hoa_majors.core.utils import iter_toml_files

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
    for _, data in iter_toml_files(data_dir):
        for course in data.get("courses", []):
            if "course_code" in course:
                all_courses.add(course["course_code"])
    return all_courses


def write_table(table: dict[tuple[str, str], str], output_file: Path):
    lines = [HEADER_COMMENT + "LOOKUP_TABLE: dict[tuple[str, str], str] = {"]
    # 按课程代码排序
    for (course, plan), repo_id in sorted(table.items(), key=lambda x: x[0][0]):
        lines.append(f'    ("{course}", "{plan}"): "{repo_id}",')
    lines.append("}")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def init_table(data_dir: Path, output_file: Path):
    courses = extract_courses(data_dir)
    table = {(code, ""): code for code in courses}
    write_table(table, output_file)
    logger.info(f"已初始化查找表，共 {len(courses)} 门课程: {output_file}")


def update_table(data_dir: Path, table_file: Path):
    if not table_file.exists():
        init_table(data_dir, table_file)
        return

    # 动态导入现有的查找表
    import importlib.util

    try:
        spec = importlib.util.spec_from_file_location("lookup_data", table_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        existing_table = getattr(module, "LOOKUP_TABLE", {})
    except Exception as e:
        logger.error(f"读取现有查找表失败: {e}")
        existing_table = {}

    all_courses = extract_courses(data_dir)
    existing_codes = {course for course, _ in existing_table.keys()}
    new_courses = all_courses - existing_codes

    if not new_courses:
        logger.info("未发现新课程。")
        return

    for code in new_courses:
        existing_table[(code, "")] = code

    write_table(existing_table, table_file)
    logger.info(f"已更新查找表，新增 {len(new_courses)} 门课程: {table_file}")


def main():
    parser = argparse.ArgumentParser(description="生成或更新课程查找表")
    parser.add_argument("action", choices=["init", "update"], help="执行的操作")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="数据存储目录")
    parser.add_argument("--output-file", type=Path, help="查找表输出文件路径")
    args = parser.parse_args()

    table_file = args.output_file or args.data_dir / "lookup_table.py"

    if args.action == "init":
        init_table(args.data_dir, table_file)
    else:
        update_table(args.data_dir, table_file)


if __name__ == "__main__":
    main()

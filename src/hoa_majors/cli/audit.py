import argparse
from collections import defaultdict
from pathlib import Path

from hoa_majors.config import DEFAULT_DATA_DIR, logger
from hoa_majors.core.utils import iter_toml_files, normalize_course_code


def scan(data_dir: Path):
    mapping = defaultdict(set)
    for _, data in iter_toml_files(data_dir):
        for c in data.get("courses", []):
            name = c.get("course_name")
            code = c.get("course_code")
            if name and code:
                mapping[name.strip()].add(normalize_course_code(code))
    return mapping


def report_conflicts(mapping: dict, output_file: Path):
    conflicts = {name: codes for name, codes in mapping.items() if len(codes) > 1}

    print("\n" + "=" * 20 + " 冲突审计结果 " + "=" * 20 + "\n")

    if not conflicts:
        print("没有发现同名但代码不同的课程。")
    else:
        for name in sorted(conflicts):
            print(f"{name}:")
            for c in sorted(conflicts[name]):
                print(f"    {c}")
            print()

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for name in sorted(conflicts):
            f.write(f"{name}:\n")
            for c in sorted(conflicts[name]):
                f.write(f"    {c}\n")
            f.write("\n")

    logger.info(f"审计报告已保存至: {output_file.resolve()}")


def main():
    parser = argparse.ArgumentParser(description="审计课程名称与代码的冲突")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="数据存储目录")
    parser.add_argument("--output", type=Path, help="保存冲突报告的路径")
    args = parser.parse_args()

    mapping = scan(args.data_dir)
    report_file = args.output or args.data_dir / "course_code_conflicts.txt"
    report_conflicts(mapping, report_file)


if __name__ == "__main__":
    main()

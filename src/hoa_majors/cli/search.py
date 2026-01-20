import argparse
from pathlib import Path

from hoa_majors.config import DEFAULT_DATA_DIR
from hoa_majors.core.utils import iter_toml_files, normalize_course_code


def locate(code: str, data_dir: Path):
    target = normalize_course_code(code)
    results = []

    for f, data in iter_toml_files(data_dir):
        for c in data.get("courses", []):
            if "course_code" in c:
                if normalize_course_code(c["course_code"]) == target:
                    results.append((f, c))
    return results


def main():
    parser = argparse.ArgumentParser(description="在数据中搜索课程代码")
    parser.add_argument("code", nargs="?", help="要搜索的课程代码")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="数据存储目录")
    args = parser.parse_args()

    code = args.code
    if not code:
        code = input("请输入课程代码: ").strip()

    results = locate(code, args.data_dir)
    print("\n" + "=" * 40 + "\n查询结果\n" + "=" * 40 + "\n")

    if not results:
        print("未找到该课程代码。")
    else:
        print(f"找到 {len(results)} 个匹配：\n")
        for path, course in results:
            print(f"文件: {path.name}")
            print(f"课程名称: {course.get('course_name', 'N/A')}")
            print(f"课程性质: {course.get('course_nature', 'N/A')}")
            print(f"学分: {course.get('credit', 'N/A')}")
            print("-" * 40)


if __name__ == "__main__":
    main()

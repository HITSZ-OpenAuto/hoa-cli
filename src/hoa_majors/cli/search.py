from pathlib import Path

import toml

from hoa_majors.core.utils import normalize_course_code


def load_courses(path: Path):
    try:
        data = toml.load(path)
    except Exception:
        return []
    out = []
    for c in data.get("courses", []):
        if "course_code" in c:
            out.append({"name": c.get("course_name", ""), "code": c["course_code"].strip()})
    return out


def locate(code: str, data_dir: Path):
    target = normalize_course_code(code)
    results = []
    root = data_dir / "SCHOOL_MAJORS"
    for f in root.rglob("*.toml"):
        for c in load_courses(f):
            if normalize_course_code(c["code"]) == target:
                results.append((f, c))
    return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Search for a course code in the data.")
    parser.add_argument("code", nargs="?", help="The course code to search for.")
    parser.add_argument(
        "--data-dir", type=Path, default=Path("data"), help="Directory where data is stored."
    )
    args = parser.parse_args()

    code = args.code
    if not code:
        code = input("请输入课程代码: ").strip()

    results = locate(code, args.data_dir)
    print("\n" + "=" * 30 + "\n查询结果\n" + "=" * 30 + "\n")
    if not results:
        print("未找到该课程代码。")
    else:
        print(f"找到 {len(results)} 个匹配：\n")
        for path, course in results:
            print(f"文件: {path}")
            print(f"课程名称: {course['name']}")
            print(f"原始代码: {course['code']}")
            print("-" * 30)


if __name__ == "__main__":
    main()

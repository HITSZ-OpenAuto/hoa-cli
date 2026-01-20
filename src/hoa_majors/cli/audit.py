from collections import defaultdict
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
        if "course_name" in c and "course_code" in c:
            out.append(
                {
                    "name": c["course_name"].strip(),
                    "code": c["course_code"].strip(),
                }
            )
    return out


def scan(data_dir: Path):
    mapping = defaultdict(set)
    root = data_dir / "SCHOOL_MAJORS"
    for toml_path in root.rglob("*.toml"):
        for c in load_courses(toml_path):
            mapping[c["name"]].add(normalize_course_code(c["code"]))
    return mapping


def report_conflicts(mapping: dict, output_file: Path):
    conflicts = {name: codes for name, codes in mapping.items() if len(codes) > 1}
    print("\n===== 检测结果 =====\n")
    if not conflicts:
        print("没有发现代码变更。")
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
    print(f"结果已写入: {output_file.resolve()}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Audit course codes for conflicts.")
    parser.add_argument(
        "--data-dir", type=Path, default=Path("data"), help="Directory where data is stored."
    )
    parser.add_argument("--output", type=Path, help="Path to save the conflict report.")
    args = parser.parse_args()

    mapping = scan(args.data_dir)
    report_file = args.output or args.data_dir / "course_code_conflicts.txt"
    report_conflicts(mapping, report_file)


if __name__ == "__main__":
    main()

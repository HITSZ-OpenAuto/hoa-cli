import toml
from pathlib import Path
from collections import defaultdict


# ----------------------------------------------------------
# CONFIG
# ----------------------------------------------------------

ROOT = Path("SCHOOL_MAJORS")
OUTPUT = Path("course_code_conflicts.txt")


# ----------------------------------------------------------
# Helpers
# ----------------------------------------------------------

def normalize(code: str) -> str:
    """
    Normalize course code.

    Only rule:
        remove trailing E
    """
    code = code.strip().upper()

    if code.endswith("E"):
        return code[:-1]
    return code


def load_courses(path: Path):
    """Load courses and return simplified dicts."""
    try:
        data = toml.load(path)
    except Exception as e:
        print("⚠ 无法解析:", path, e)
        return []

    out = []

    for c in data.get("courses", []):
        if "course_name" not in c or "course_code" not in c:
            continue
        out.append({
            "name": c["course_name"].strip(),
            "code": c["course_code"].strip(),
        })

    return out


# ----------------------------------------------------------
# Scanner
# ----------------------------------------------------------

def scan():
    mapping = defaultdict(set)

    for toml_path in ROOT.rglob("*.toml"):
        for c in load_courses(toml_path):
            mapping[c["name"]].add(normalize(c["code"]))

    return mapping


# ----------------------------------------------------------
# Output
# ----------------------------------------------------------

def output(mapping):
    conflicts = {
        name: codes
        for name, codes in mapping.items()
        if len(codes) > 1
    }

    print("\n===== 检测结果 =====\n")

    if not conflicts:
        print("没有发现代码变更。")
    else:
        for name in sorted(conflicts):
            print(name + ":")
            for c in sorted(conflicts[name]):
                print("   ", c)
            print()

    with open(OUTPUT, "w", encoding="utf-8") as f:
        for name in sorted(conflicts):
            f.write(name + ":\n")
            for c in sorted(conflicts[name]):
                f.write("   " + c + "\n")
            f.write("\n")

    print("结果已写入:", OUTPUT.resolve())


# ----------------------------------------------------------
# main
# ----------------------------------------------------------

if __name__ == "__main__":
    mapping = scan()
    output(mapping)

import toml
from pathlib import Path


ROOT = Path("SCHOOL_MAJORS")


# ----------------------------------------------------------
# Helpers
# ----------------------------------------------------------

def normalize(code: str) -> str:
    code = code.strip().upper()
    if code.endswith("E"):
        return code[:-1]
    return code


def load_courses(path):
    try:
        data = toml.load(path)
    except:
        return []

    out = []
    for c in data.get("courses", []):
        if "course_code" in c:
            out.append({
                "name": c.get("course_name", ""),
                "code": c["course_code"].strip()
            })
    return out


# ----------------------------------------------------------
# Search
# ----------------------------------------------------------

def locate(code):
    target = normalize(code)

    results = []

    for f in ROOT.rglob("*.toml"):
        for c in load_courses(f):
            if normalize(c["code"]) == target:
                results.append((f, c))

    return results


# ----------------------------------------------------------
# main
# ----------------------------------------------------------

if __name__ == "__main__":

    user = input("请输入课程代码: ").strip()
    results = locate(user)

    print("\n==============================")
    print("查询结果")
    print("==============================\n")

    if not results:
        print("未找到该课程代码。")
    else:
        print(f"找到 {len(results)} 个匹配：\n")
        for path, course in results:
            print("文件:", path)
            print("课程名称:", course["name"])
            print("原始代码:", course["code"])
            print("--------------------------------")


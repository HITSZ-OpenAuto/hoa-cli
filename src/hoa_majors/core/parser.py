from typing import Any

# 字段英文映射
FIELD_MAP = {
    "kcdm": "course_code",
    "xf": "credit",
    "khfsmc": "assessment_method",
    "kcmc": "course_name",
    "tjkkxnxq": "recommended_year_semester",
    "kzmc": "track",
    "kcxzmc": "course_nature",
    "kclbmc": "course_category",
    "kkyxmc": "offering_college",
}

# 学时字段
HOURS_MAP = {
    "zxs": ("xszxs", "total_hours"),
    "llxs": ("xsllxs", "theory"),
    "syxs": ("xssyxs", "lab"),
    "sjxs": ("2", "practice"),
    "xtxs": ("6", "exercise"),
    "sjxs2": ("8", "computer"),
    "fdxs": ("10", "tutoring"),
}


def parse_hours(raw_item: dict[str, Any]) -> dict[str, Any]:
    """
    Extract structured hours:
    - total_hours
    - [hours] table
    """
    result = {"hours": {}}

    # 总学时
    total_hours_key = HOURS_MAP["zxs"][0]
    if total_hours_key in raw_item:
        try:
            result["total_hours"] = int(raw_item[total_hours_key])
        except (ValueError, TypeError):
            result["total_hours"] = 0

    # 子学时
    xss = raw_item.get("xss", {})
    for code, (key, eng_name) in HOURS_MAP.items():
        if code == "zxs":
            continue

        if key in raw_item:
            try:
                result["hours"][eng_name] = int(raw_item[key])
            except (ValueError, TypeError):
                result["hours"][eng_name] = 0

        if isinstance(xss, dict) and key in xss:
            val = xss[key]
            if isinstance(val, str) and "周" in val:
                val = val.replace("周", "")
            try:
                result["hours"][eng_name] = int(val)
            except (ValueError, TypeError):
                pass

        if eng_name not in result["hours"]:
            result["hours"][eng_name] = 0

    return result


def normalize_course(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Convert raw JW item to normalized English-field dict.
    """
    course = {}

    for zh_key, en_key in FIELD_MAP.items():
        if zh_key in raw:
            course[en_key] = raw[zh_key]

    hours_block = parse_hours(raw)
    course.update(hours_block)

    return course

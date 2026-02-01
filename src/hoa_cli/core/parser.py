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

# 学时字段映射
# 格式: {英文名: (教务系统字段名, 类型码)}
# 如果类型码为 None，则直接从教务系统字段名读取
HOURS_CONFIG = {
    "total_hours": ("xszxs", None),
    "theory": ("xsllxs", "llxs"),
    "lab": ("xssyxs", "syxs"),
    "practice": ("2", "sjxs"),
    "exercise": ("6", "xtxs"),
    "computer": ("8", "sjxs2"),
    "tutoring": ("10", "fdxs"),
}


def parse_hours(raw_item: dict[str, Any]) -> dict[str, Any]:
    """
    Extract structured hours:
    - total_hours
    - [hours] table
    """
    result = {"hours": {}}
    xss = raw_item.get("xss", {})

    for eng_name, (jw_key, _) in HOURS_CONFIG.items():
        val = 0

        # 1. 尝试从直接字段获取
        if jw_key in raw_item:
            try:
                val = int(raw_item[jw_key])
            except (ValueError, TypeError):
                pass

        # 2. 尝试从 xss 嵌套字段获取
        if val == 0 and isinstance(xss, dict) and jw_key in xss:
            raw_val = xss[jw_key]
            if isinstance(raw_val, str) and "周" in raw_val:
                raw_val = raw_val.replace("周", "")
            try:
                val = int(raw_val)
            except (ValueError, TypeError):
                pass

        if eng_name == "total_hours":
            result["total_hours"] = val
        else:
            result["hours"][eng_name] = val

    return result


def normalize_course(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Convert raw JW item to normalized English-field dict.
    """
    course = {FIELD_MAP[zh]: raw[zh] for zh in FIELD_MAP if zh in raw}
    course.update(parse_hours(raw))
    return course

import argparse
import json
import sys
from pathlib import Path

from hoa_majors.config import DEFAULT_DATA_DIR, logger
from hoa_majors.core.utils import iter_toml_files


def _load_grades_summary(data_dir: Path) -> dict:
    """Load grades_summary.json if present; otherwise return empty dict."""

    path = data_dir / "grades_summary.json"
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"无法读取 {path.name}: {e}")
        return {}


def _print_grade_details(
    *,
    grades_summary: dict,
    course_code: str,
    year: str | None,
    major_code: str | None,
    major_name: str | None,
):
    """Append grade details for a course, if any match exists."""

    entry = grades_summary.get(course_code)
    if not isinstance(entry, dict):
        return

    year = (year or "").strip()
    major_code = (major_code or "").strip()
    major_name = (major_name or "").strip()

    # Selection order:
    # 1) year_major
    # 2) year_default
    # 3) default
    #
    # Note: upstream grades_summary.json uses year+major *name* (e.g. 2021_自动化).
    # The feature request mentions major code, so we try both code and name.
    year_major_keys: list[str] = []
    if year and major_code:
        year_major_keys.append(f"{year}_{major_code}")
    if year and major_name:
        year_major_keys.append(f"{year}_{major_name}")

    year_default_key = f"{year}_default" if year else ""

    grade_items = None
    for k in year_major_keys:
        if k in entry:
            grade_items = entry.get(k)
            break
    if grade_items is None and year_default_key and year_default_key in entry:
        grade_items = entry.get(year_default_key)
    if grade_items is None and "default" in entry:
        grade_items = entry.get("default")

    if not isinstance(grade_items, list) or not grade_items:
        return

    print("-" * 60)
    print("成绩构成")
    for item in grade_items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        percent = item.get("percent")
        percent_str = str(percent).strip() if percent is not None else ""
        if percent_str:
            print(f"{name}: {percent_str}")
        else:
            print(f"{name}")


def get_course_info(plan_id: str, course_code: str, data_dir: Path):
    found_plan = False
    found_course = False

    grades_summary = _load_grades_summary(data_dir)

    for _, data in iter_toml_files(data_dir):
        info = data.get("info", {})
        if info.get("plan_ID") == plan_id:
            found_plan = True
            for course in data.get("courses", []):
                if course.get("course_code") == course_code:
                    found_course = True
                    # 基本信息
                    print("\n基本信息")
                    field_order = [
                        ("course_code", "Course Code"),
                        ("credit", "Credit"),
                        ("assessment_method", "Assessment Method"),
                        ("course_name", "Course Name"),
                        ("recommended_year_semester", "Recommended Year Semester"),
                        ("course_nature", "Course Nature"),
                        ("course_category", "Course Category"),
                        ("offering_college", "Offering College"),
                        ("total_hours", "Total Hours"),
                    ]
                    label_width = 26
                    for k, label in field_order:
                        if k in course:
                            print(f"{label:<{label_width}} : {course.get(k)}")

                    # 学时分配
                    if "hours" in course:
                        print("-" * 60)
                        print("学时分配")
                        hour_order = [
                            ("theory", "Theory"),
                            ("lab", "Lab"),
                            ("practice", "Practice"),
                            ("exercise", "Exercise"),
                            ("computer", "Computer"),
                            ("tutoring", "Tutoring"),
                        ]
                        for h_key, h_label in hour_order:
                            if h_key in course["hours"]:
                                print(f"{h_label:<{label_width}} : {course['hours'].get(h_key)}")

                    # Append grade details if we can find a matching summary entry.
                    _print_grade_details(
                        grades_summary=grades_summary,
                        course_code=course_code,
                        year=info.get("year"),
                        major_code=info.get("major_code"),
                        major_name=info.get("major_name"),
                    )

                    print("=" * 60)
                    break
            if found_course:
                break

    if not found_plan:
        logger.error(f"未找到 ID 为 {plan_id} 的培养方案")
        sys.exit(1)
    elif not found_course:
        logger.error(f"在培养方案 {plan_id} 中未找到课程 {course_code}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="获取培养方案中特定课程的详细信息")
    parser.add_argument("plan_id", help="培养方案 ID (fah)")
    parser.add_argument("course_code", help="课程代码")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="数据存储目录")
    args = parser.parse_args()

    get_course_info(args.plan_id, args.course_code, args.data_dir)


if __name__ == "__main__":
    main()

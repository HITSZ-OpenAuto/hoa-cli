import argparse
import json
from pathlib import Path
from typing import Any

from hoa_cli.config import DEFAULT_DATA_DIR
from hoa_cli.core.fetcher import (
    fetch_postgrad_courses_by_group,
    get_postgrad_course_groups,
    get_postgrad_fah_list,
)
from hoa_cli.core.postgrad import (
    analyze_group_selection,
    build_postgrad_mapping,
    derive_postgrad_zyfx,
    merge_postgrad_courses,
)


def _summarize_major(bbh: str, major_code: str, major_entry: dict[str, Any]) -> dict[str, Any]:
    zyfx = derive_postgrad_zyfx(major_code)
    plans_summary: list[dict[str, Any]] = []
    raw_courses: list[dict[str, Any]] = []

    for plan in major_entry.get("plans", []):
        plan_id = str(plan.get("plan_id") or "").strip()
        bgid = str(plan.get("bgid") or "").strip()
        groups = get_postgrad_course_groups(plan_id, bgid=bgid)
        group_report = analyze_group_selection(groups)

        plan_summary = {
            "plan_id": plan_id,
            "plan_name": str(plan.get("name") or "").strip(),
            "group_count": len(groups),
            "excluded_group_count": len(group_report["excluded_ids"]),
            "leaf_group_count": len(group_report["leaf_ids"]),
            "excluded_group_names": [
                group_report["groups_by_id"][kzid]["kzmc"]
                for kzid in sorted(group_report["excluded_ids"])
                if kzid in group_report["groups_by_id"]
            ],
            "leaf_groups": [
                {
                    "kzid": kzid,
                    "kzmc": group_report["groups_by_id"][kzid]["kzmc"],
                }
                for kzid in group_report["leaf_ids"]
                if kzid in group_report["groups_by_id"]
            ],
        }

        plan_course_count = 0
        for leaf_group in plan_summary["leaf_groups"]:
            courses = fetch_postgrad_courses_by_group(
                plan_id, leaf_group["kzid"], zyfx=zyfx, bgid=bgid
            )
            plan_course_count += len(courses)
            raw_courses.extend(courses)
        plan_summary["raw_course_count"] = plan_course_count
        plans_summary.append(plan_summary)

    merged_courses = merge_postgrad_courses(
        raw_courses, major_code=major_code, logger_prefix=f"[{bbh}] "
    )
    return {
        "major_code": major_code,
        "major_name": major_entry.get("major_name", ""),
        "school_name": major_entry.get("school_name", ""),
        "plan_count": len(major_entry.get("plans", [])),
        "raw_course_count": len(raw_courses),
        "merged_course_count": len(merged_courses),
        "plans": plans_summary,
    }


def main():
    parser = argparse.ArgumentParser(description="对异常研究生专业做逐个课组/课程分析")
    parser.add_argument("--bbh", required=True, help="版本号，如 202509")
    parser.add_argument(
        "--major-codes",
        nargs="+",
        required=True,
        help="要分析的专业代码列表，如 081301 1405 0873",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="可选：将分析结果写入 JSON 文件",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="保留与项目其他脚本一致的参数语义",
    )
    args = parser.parse_args()

    raw_items = get_postgrad_fah_list(args.bbh)
    mapping = build_postgrad_mapping(raw_items)

    report: dict[str, Any] = {"bbh": args.bbh, "majors": {}}
    for major_code in args.major_codes:
        entry = mapping.get(major_code)
        if not entry:
            report["majors"][major_code] = {"error": "major_code not found"}
            continue
        report["majors"][major_code] = _summarize_major(args.bbh, major_code, entry)

    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()

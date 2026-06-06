import json
import tomllib
from pathlib import Path
from typing import Any

from hoa_cli.config import DEFAULT_DATA_DIR, PLANS_SUBDIR, logger
from hoa_cli.core.fetcher import (
    fetch_postgrad_courses_by_group,
    get_postgrad_course_groups,
    get_postgrad_fah_list,
)
from hoa_cli.core.postgrad import (
    build_postgrad_mapping,
    derive_postgrad_zyfx,
    merge_postgrad_courses,
    select_leaf_group_ids,
    should_exclude_course_item,
)
from hoa_cli.core.writer import write_toml


def build_postgrad_mappings(bbhs: list[str], output_path: Path) -> dict[str, dict]:
    """Fetch and persist postgrad major mappings for the given bbh values."""
    all_mappings: dict[str, dict] = {}

    for bbh in bbhs:
        logger.info(f"正在处理研究生版本: {bbh}")
        raw_plans = get_postgrad_fah_list(bbh)
        all_mappings[bbh] = build_postgrad_mapping(raw_plans)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_mappings, f, ensure_ascii=False, indent=2)

    return all_mappings


def load_postgrad_mappings(mapping_path: Path) -> dict[str, dict]:
    """Load the persisted postgrad mapping JSON."""
    if not mapping_path.exists():
        logger.error(f"研究生映射文件不存在: {mapping_path}")
        return {}

    with open(mapping_path, encoding="utf-8") as f:
        loaded = json.load(f)

    return loaded if isinstance(loaded, dict) else {}


def _clean_filename_component(value: str) -> str:
    return value.replace("/", "-").replace("\\", "-").strip()


def _build_postgrad_info(bbh: str, major_entry: dict[str, object]) -> dict[str, object]:
    plans = major_entry.get("plans", [])
    source_plan_ids: list[str] = []
    source_plan_names: list[str] = []

    if isinstance(plans, list):
        for plan in plans:
            if not isinstance(plan, dict):
                continue
            plan_id = str(plan.get("plan_id") or "").strip()
            plan_name = str(plan.get("name") or "").strip()
            if plan_id and plan_id not in source_plan_ids:
                source_plan_ids.append(plan_id)
            if plan_name and plan_name not in source_plan_names:
                source_plan_names.append(plan_name)

    return {
        "study_level": "postgrad",
        "entry_year": bbh[:4],
        "year_month": bbh,
        "major_code": str(major_entry.get("major_code") or "").strip(),
        "major_name": str(major_entry.get("major_name") or "").strip(),
        "school_name": str(major_entry.get("school_name") or "").strip(),
        "source_plan_IDs": source_plan_ids,
        "source_plan_names": source_plan_names,
    }


def _target_postgrad_path(data_dir: Path, bbh: str, major_entry: dict[str, object]) -> Path:
    base_dir = data_dir / PLANS_SUBDIR
    major_name = _clean_filename_component(str(major_entry.get("major_name") or "").strip())
    major_code = str(major_entry.get("major_code") or "").strip()
    if not major_name:
        major_name = major_code
    filename = f"{bbh}_研_{major_name}.toml"
    target_path = base_dir / filename

    if target_path.exists():
        try:
            with open(target_path, "rb") as f:
                existing = tomllib.load(f)
            existing_info = existing.get("info", {})
            if (
                existing_info.get("study_level") == "postgrad"
                and existing_info.get("year_month") == bbh
                and existing_info.get("major_code") == major_code
            ):
                return target_path
        except Exception:
            pass

        filename = f"{bbh}_研_{major_name}_{major_code}.toml"
        target_path = base_dir / filename

    return target_path


def _collect_courses_for_major(major_entry: dict[str, object]) -> list[dict]:
    major_code = str(major_entry.get("major_code") or "").strip()
    zyfx = derive_postgrad_zyfx(major_code)
    all_raw_courses: list[dict] = []
    plans = major_entry.get("plans", [])

    if not isinstance(plans, list):
        return []

    for plan in plans:
        if not isinstance(plan, dict):
            continue

        plan_id = str(plan.get("plan_id") or "").strip()
        bgid = str(plan.get("bgid") or "").strip()
        if not plan_id:
            continue

        course_groups = get_postgrad_course_groups(plan_id, bgid=bgid)
        leaf_group_ids = select_leaf_group_ids(course_groups)
        logger.info(f"研究生培养方案 {plan_id} 筛得叶子课组 {len(leaf_group_ids)} 个")

        for leaf_group_id in leaf_group_ids:
            raw_courses = fetch_postgrad_courses_by_group(
                plan_id, leaf_group_id, zyfx=zyfx, bgid=bgid
            )
            # 第二层过滤：课程级 kzmc 检查。第一层 select_leaf_group_ids 已按
            # 课组名排除了应跳过的分支，但 API 返回的课组树中存在扁平"选修课"
            # 叶子节点——其课组名不含排除关键词，却被用作各学科模块选修课程的
            # 总入口，取回的课程条目 kzmc 仍为"XX模块：…选修课程清单"，必须
            # 在课程级再过滤一次。
            kept_courses = [
                course for course in raw_courses if not should_exclude_course_item(course)
            ]
            all_raw_courses.extend(kept_courses)

    return all_raw_courses


def crawl_postgrad_major(
    *, bbh: str, major_code: str, major_entry: dict[str, Any], data_dir: Path
) -> Path:
    """Generate or refresh the TOML for one postgrad major."""
    major_name = str(major_entry.get("major_name") or "").strip()
    logger.info(f"正在抓取研究生专业: {bbh} {major_code} {major_name}")
    major_entry["major_code"] = major_code
    raw_courses = _collect_courses_for_major(major_entry)
    merged_courses = merge_postgrad_courses(
        raw_courses, major_code=major_code, logger_prefix=f"[{bbh}] "
    )

    data = {
        "info": _build_postgrad_info(bbh, major_entry),
        "courses": merged_courses,
    }
    target_path = _target_postgrad_path(data_dir, bbh, major_entry)
    write_toml(target_path, data)
    return target_path


def crawl_postgrad_courses(
    mapping_path: Path,
    data_dir: Path,
    *,
    major_codes: set[str] | None = None,
    bbhs: set[str] | None = None,
):
    """Generate postgrad TOML files from a postgrad mapping file."""
    all_mappings = load_postgrad_mappings(mapping_path)
    if not all_mappings:
        return

    for bbh, majors in all_mappings.items():
        if bbhs and bbh not in bbhs:
            continue
        if not isinstance(majors, dict):
            continue

        for major_code, major_entry in majors.items():
            if major_codes and major_code not in major_codes:
                continue
            if not isinstance(major_entry, dict):
                continue

            crawl_postgrad_major(
                bbh=bbh,
                major_code=major_code,
                major_entry=major_entry,
                data_dir=data_dir,
            )


def run(bbhs: list[str], data_dir: Path, mapping_file: Path | None = None):
    mapping_path = mapping_file or (data_dir / "postgrad_mapping.json")
    logger.info(f"开始抓取研究生培养方案映射: {bbhs}")
    build_postgrad_mappings(bbhs, mapping_path)
    logger.info("开始抓取研究生课程详细数据")
    crawl_postgrad_courses(mapping_path, data_dir)
    logger.info("研究生抓取任务完成")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="抓取研究生培养方案与课程数据")
    parser.add_argument("--bbh", nargs="+", required=True, help="要抓取的版本号列表，如 202509")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="数据存储目录")
    parser.add_argument(
        "--mapping-file",
        type=Path,
        default=None,
        help="研究生映射文件输出路径，默认写入 {data_dir}/postgrad_mapping.json",
    )
    args = parser.parse_args()

    run(args.bbh, args.data_dir, mapping_file=args.mapping_file)


if __name__ == "__main__":
    main()

import json
import time
from pathlib import Path

import toml

from hoa_cli.config import DEFAULT_DATA_DIR, PLANS_SUBDIR, logger
from hoa_cli.core.fetcher import fetch_courses_by_fah, get_fah_list, get_major_list_by_dalei
from hoa_cli.core.parser import normalize_course
from hoa_cli.core.writer import write_toml


def generate_toml_for_fah(fah: str, info: dict | None = None) -> dict:
    raw_courses = fetch_courses_by_fah(fah)
    normalized = [normalize_course(item) for item in raw_courses]
    result = {"courses": normalized}
    if info:
        result["info"] = info
    return result


def crawl_majors(grades: list[str], output_path: Path) -> dict:
    """获取所有年级和专业的映射关系"""
    all_mappings = {}

    for grade in grades:
        logger.info(f"正在处理年级: {grade}")
        grade_mapping = {}
        fah_list = get_fah_list(grade)

        # 将 fah_list 转换为以 zydm 为键的字典，方便查找
        fah_dict = {item["zydm"]: item for item in fah_list}
        processed_zydms = set()

        for zydm, info in fah_dict.items():
            if zydm in processed_zydms:
                continue

            # 尝试查询是否为大类
            sub_majors = get_major_list_by_dalei(zydm)
            time.sleep(0.1)  # 稍微延迟避免频率限制

            major_entry = {
                "name": info["zymc"],
                "plan_ID": info["fah"],
                "school_name": info["yxmc"],
                "majors": [],
            }

            if sub_majors:
                for sub in sub_majors:
                    sub_zydm = sub["ZYDM"]
                    if sub_zydm in fah_dict:
                        sub_info = fah_dict[sub_zydm]
                        major_entry["majors"].append(
                            {
                                "name": sub["ZYMC"],
                                "major_ID": sub_zydm,
                                "plan_ID": sub_info["fah"],
                            }
                        )
                        processed_zydms.add(sub_zydm)

            grade_mapping[zydm] = major_entry
            processed_zydms.add(zydm)

        all_mappings[grade] = grade_mapping

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_mappings, f, ensure_ascii=False, indent=2)

    return all_mappings


def _process_single_plan(
    year: str,
    major_code: str,
    major_name: str,
    fah: str,
    school_name: str,
    base_dir: Path,
    parent_info: dict | None = None,
):
    """处理单个培养方案的抓取与保存"""
    degree = "本"
    clean_name = major_name.replace("/", "-").replace("\\", "-").strip()
    filename = f"{year}_{degree}_{clean_name}.toml"
    target_path = base_dir / filename

    # 处理文件名冲突
    if target_path.exists():
        try:
            existing_data = toml.load(target_path)
            if existing_data.get("info", {}).get("plan_ID") != fah:
                filename = f"{year}_{degree}_{clean_name}_{fah[:8]}.toml"
                target_path = base_dir / filename
        except Exception:
            pass

    info = {
        "year": year,
        "major_code": major_code,
        "major_name": major_name,
        "school_name": school_name,
        "plan_ID": fah,
    }
    if parent_info:
        info.update(parent_info)

    logger.info(f"正在抓取: {year} {major_name} ({fah})")
    try:
        data = generate_toml_for_fah(fah, info)
        write_toml(target_path, data)
    except Exception as e:
        logger.error(f"抓取 {major_name} 失败: {e}")


def crawl_courses(mapping_path: Path, data_dir: Path):
    """根据映射文件抓取所有课程数据"""
    if not mapping_path.exists():
        logger.error(f"映射文件不存在: {mapping_path}")
        return

    with open(mapping_path, encoding="utf-8") as f:
        all_majors = json.load(f)

    base_dir = data_dir / PLANS_SUBDIR

    for year, majors_dict in all_majors.items():
        for major_code, major_info in majors_dict.items():
            # 1. 处理主专业/大类
            fah = major_info.get("plan_ID")
            major_name = major_info.get("name")
            school_name = major_info.get("school_name", "")

            if fah and major_name:
                _process_single_plan(year, major_code, major_name, fah, school_name, base_dir)

            # 2. 处理下属子专业
            parent_info = {
                "parent_major_code": major_code,
                "parent_major_name": major_name,
            }
            for sub in major_info.get("majors", []):
                sub_fah = sub.get("plan_ID")
                sub_name = sub.get("name")
                sub_code = sub.get("major_ID")
                if sub_fah and sub_name:
                    _process_single_plan(
                        year, sub_code, sub_name, sub_fah, school_name, base_dir, parent_info
                    )


def main():
    import argparse

    parser = argparse.ArgumentParser(description="抓取培养方案与课程数据")
    parser.add_argument(
        "--grades",
        nargs="+",
        default=["2019", "2020", "2021", "2022", "2023", "2024", "2025"],
        help="要抓取的年级列表",
    )
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="数据存储目录")
    args = parser.parse_args()

    mapping_file = args.data_dir / "major_mapping.json"

    logger.info(f"开始抓取年级映射: {args.grades}")
    crawl_majors(args.grades, mapping_file)

    logger.info("开始抓取课程详细数据")
    crawl_courses(mapping_file, args.data_dir)
    logger.info("抓取任务完成")


if __name__ == "__main__":
    main()

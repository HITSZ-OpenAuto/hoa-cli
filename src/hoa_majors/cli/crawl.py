import json
import time
from pathlib import Path

from hoa_majors.core.fetcher import fetch_courses_by_fah, get_fah_list, get_major_list_by_dalei
from hoa_majors.core.parser import normalize_course
from hoa_majors.core.writer import write_toml


def generate_toml_for_fah(fah: str, info: dict | None = None) -> dict:
    raw_courses = fetch_courses_by_fah(fah)
    normalized = [normalize_course(item) for item in raw_courses]
    result = {}
    if info:
        result["info"] = info
    result["courses"] = normalized
    return result


def crawl_majors(grades: list[str], output_path: Path):
    result = {}
    for grade in grades:
        print(f"\n========== 处理年级: {grade} ==========")
        result[grade] = {}
        fah_list = get_fah_list(grade)
        no_dalei_list = []
        while fah_list:
            fah_first = fah_list[0]
            majors = get_major_list_by_dalei(fah_first["zydm"])
            time.sleep(0.3)
            if not majors:
                no_dalei_list.append(fah_first)
            else:
                result[grade][fah_first["zydm"]] = {
                    "name": fah_first["zymc"],
                    "plan_ID": fah_first["fah"],
                    "school_name": fah_first["yxmc"],
                    "majors": [],
                }
                for major in majors:
                    major_item = None
                    matched_fah = next((f for f in fah_list if f["zydm"] == major["ZYDM"]), None)
                    if matched_fah:
                        major_item = {
                            "name": major["ZYMC"],
                            "major_ID": major["ZYDM"],
                            "plan_ID": matched_fah["fah"],
                        }
                        fah_list.remove(matched_fah)
                    else:
                        matched_fah = next(
                            (f for f in no_dalei_list if f["zydm"] == major["ZYDM"]), None
                        )
                        if matched_fah:
                            major_item = {
                                "name": major["ZYMC"],
                                "major_ID": major["ZYDM"],
                                "plan_ID": matched_fah["fah"],
                            }
                            no_dalei_list.remove(matched_fah)
                    if major_item:
                        result[grade][fah_first["zydm"]]["majors"].append(major_item)
            fah_list = fah_list[1:]
        for no_dalei in no_dalei_list:
            result[grade][no_dalei["zydm"]] = {
                "name": no_dalei["zymc"],
                "plan_ID": no_dalei["fah"],
                "school_name": no_dalei["yxmc"],
                "majors": [],
            }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result


def crawl_courses(mapping_path: Path, data_dir: Path):
    with open(mapping_path, encoding="utf-8") as f:
        majors = json.load(f)

    warn_fp = open("data/warning.txt", "w", encoding="utf-8")

    def warning(msg: str):
        print(msg)
        warn_fp.write(msg + "\n")

    base_dir = data_dir / "SCHOOL_MAJORS"
    degree = "本"

    for year, majors_dict in majors.items():
        for major_code, major_info in majors_dict.items():
            major_name = major_info.get("name")
            fah = major_info.get("plan_ID")
            if not major_name:
                continue

            if fah:
                try:
                    clean_name = major_name.replace("/", "-").replace("\\", "-").strip()
                    filename = f"{year}_{degree}_{clean_name}.toml"
                    target_path = base_dir / filename

                    # Handle collisions
                    if target_path.exists():
                        # Read existing plan_ID to see if it's the same
                        try:
                            import toml

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
                        "school_name": major_info.get("school_name", ""),
                        "plan_ID": fah,
                    }
                    write_toml(target_path, generate_toml_for_fah(fah, info))
                except Exception as e:
                    warning(f"⚠ 大类 {major_name} 失败: {e}")

            for sub in major_info.get("majors", []):
                sub_fah = sub.get("plan_ID")
                sub_name = sub.get("name")
                if sub_fah and sub_name:
                    try:
                        clean_sub_name = sub_name.replace("/", "-").replace("\\", "-").strip()
                        sub_filename = f"{year}_{degree}_{clean_sub_name}.toml"
                        sub_target_path = base_dir / sub_filename

                        if sub_target_path.exists():
                            try:
                                import toml

                                existing_data = toml.load(sub_target_path)
                                if existing_data.get("info", {}).get("plan_ID") != sub_fah:
                                    sub_filename = (
                                        f"{year}_{degree}_{clean_sub_name}_{sub_fah[:8]}.toml"
                                    )
                                    sub_target_path = base_dir / sub_filename
                            except Exception:
                                pass

                        info = {
                            "year": year,
                            "parent_major_code": major_code,
                            "parent_major_name": major_name,
                            "major_code": sub.get("major_ID"),
                            "major_name": sub_name,
                            "school_name": major_info.get("school_name", ""),
                            "plan_ID": sub_fah,
                        }
                        write_toml(sub_target_path, generate_toml_for_fah(sub_fah, info))
                    except Exception as e:
                        warning(f"⚠ 子类 {sub_name} 失败: {e}")
    warn_fp.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Crawl majors and courses.")
    parser.add_argument(
        "--grades",
        nargs="+",
        default=["2019", "2020", "2021", "2022", "2023", "2024", "2025"],
        help="Grades to crawl.",
    )
    parser.add_argument(
        "--data-dir", type=Path, default=Path("data"), help="Directory to store data."
    )
    args = parser.parse_args()

    mapping_file = args.data_dir / "major_mapping.json"
    print(f"Crawling major mappings for {args.grades}...")
    crawl_majors(args.grades, mapping_file)
    print("Crawling courses...")
    crawl_courses(mapping_file, args.data_dir)


if __name__ == "__main__":
    main()

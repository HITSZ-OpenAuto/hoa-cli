import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

from hoa_cli.cli.crawl_postgrad import _build_postgrad_info, _collect_courses_for_major
from hoa_cli.core.postgrad import (
    analyze_group_selection,
    build_postgrad_mapping,
    derive_postgrad_degree_levels,
    extract_postgrad_module_code,
    is_international_postgrad_plan_name,
    is_postgrad_elective_module_name,
    merge_postgrad_courses,
    normalize_postgrad_module_name,
    select_leaf_group_ids,
    should_exclude_course_item,
)
from hoa_cli.core.writer import write_toml


class PostgradLogicTests(unittest.TestCase):
    def test_postgrad_module_name_helpers(self):
        raw_name = " MX 模块: 智能科学与技术学科硕士选修课程清单。 "

        self.assertEqual(
            normalize_postgrad_module_name(raw_name),
            "MX模块：智能科学与技术学科硕士选修课程清单",
        )
        self.assertTrue(is_postgrad_elective_module_name(raw_name))
        self.assertTrue(
            is_postgrad_elective_module_name("DV模块：集成电路科学与工程博士选修课清单")
        )
        self.assertEqual(
            normalize_postgrad_module_name("MD模块：机械工程学科硕士选修课清单"),
            "MD模块：机械工程学科硕士选修课程清单",
        )
        self.assertEqual(extract_postgrad_module_code(raw_name), "MX")
        self.assertEqual(derive_postgrad_degree_levels(raw_name), ["master"])

    def test_postgrad_module_name_helpers_do_not_match_broad_module_names(self):
        self.assertFalse(is_postgrad_elective_module_name("工程实践模块"))
        self.assertFalse(is_postgrad_elective_module_name("推荐选修课模块"))
        self.assertFalse(is_postgrad_elective_module_name("专业选修课程清单"))

    def test_international_postgrad_plan_name(self):
        self.assertTrue(
            is_international_postgrad_plan_name("计算机科学与技术-硕士培养方案(留学生)")
        )
        self.assertFalse(is_international_postgrad_plan_name("计算机科学与技术-硕士培养方案"))

    def test_postgrad_crawl_excludes_international_plans(self):
        major_entry = {
            "major_code": "0812",
            "major_name": "计算机科学与技术",
            "plans": [
                {
                    "plan_id": "DOMESTIC",
                    "name": "计算机科学与技术-硕士生培养方案",
                    "bgid": "BG-1",
                },
                {
                    "plan_id": "INTERNATIONAL",
                    "name": "计算机科学与技术-硕士生培养方案(留学生)",
                    "bgid": "BG-2",
                },
            ],
        }

        info = _build_postgrad_info("202509", major_entry)
        self.assertEqual(info["source_plan_IDs"], ["DOMESTIC"])
        self.assertEqual(info["source_plan_names"], ["计算机科学与技术-硕士生培养方案"])

        with (
            patch(
                "hoa_cli.cli.crawl_postgrad.get_postgrad_course_groups",
                return_value=[{"kzid": "leaf", "fkzid": "-1", "kzmc": "核心课"}],
            ) as mock_groups,
            patch(
                "hoa_cli.cli.crawl_postgrad.fetch_postgrad_courses_by_group",
                return_value=[{"kcdm": "COMP5001", "kzmc": "核心课"}],
            ) as mock_courses,
        ):
            courses = _collect_courses_for_major(major_entry)

        self.assertEqual([course["kcdm"] for course in courses], ["COMP5001"])
        mock_groups.assert_called_once_with("DOMESTIC", bgid="BG-1", strict=True)
        mock_courses.assert_called_once_with("DOMESTIC", "leaf", zyfx="", bgid="BG-1", strict=True)

    def test_build_postgrad_mapping_uses_major_code_and_skips_x_prefix(self):
        raw_items = [
            {
                "fah": "PLAN-A",
                "zydm": "0854",
                "zyfxdm": "085410",
                "zymc": "电子信息",
                "zyfxmc": "人工智能",
                "yxmc": "智能科学与工程学院",
                "famc": "方案 A",
                "bgid": "BG-A",
                "falxdm": "1",
            },
            {
                "fah": "PLAN-B",
                "zydm": "X001",
                "zymc": "应忽略",
                "yxmc": "测试学院",
                "famc": "方案 B",
                "falxdm": "1",
            },
        ]

        mapping = build_postgrad_mapping(raw_items)

        self.assertEqual(list(mapping), ["085410"])
        self.assertEqual(mapping["085410"]["major_name"], "电子信息（人工智能）")
        self.assertEqual(mapping["085410"]["school_name"], "智能科学与工程学院")
        self.assertEqual(mapping["085410"]["plans"][0]["plan_id"], "PLAN-A")

    def test_build_postgrad_mapping_falls_back_to_famc_major_name(self):
        raw_items = [
            {
                "fah": "PLAN-C",
                "zydm": "1405",
                "zymc": "",
                "zyfxmc": "",
                "yxmc": "智能科学与工程学院",
                "famc": "202509【1405】智能科学与技术-学术学位-博士生培养方案",
                "bgid": "BG-C",
                "falxdm": "1",
            }
        ]

        mapping = build_postgrad_mapping(raw_items)

        self.assertEqual(mapping["1405"]["major_name"], "智能科学与技术")

    def test_select_leaf_group_ids_excludes_named_branches_and_keyword_modules(self):
        groups = [
            {"kzid": "root", "fkzid": "-1", "kzmc": "根节点"},
            {"kzid": "keep-parent", "fkzid": "root", "kzmc": "公共学位课"},
            {"kzid": "keep-leaf", "fkzid": "keep-parent", "kzmc": "公共学位课（硕）"},
            {"kzid": "drop-parent", "fkzid": "root", "kzmc": "推荐选修课模块"},
            {"kzid": "drop-leaf", "fkzid": "drop-parent", "kzmc": "推荐选修课子模块"},
            {
                "kzid": "drop-module",
                "fkzid": "root",
                "kzmc": "MX模块：智能科学与技术学科硕士选修课程清单",
            },
        ]

        leaf_ids = select_leaf_group_ids(groups)
        report = analyze_group_selection(groups)

        self.assertEqual(leaf_ids, ["keep-leaf"])
        self.assertIn("drop-module", report["excluded_ids"])

    def test_merge_postgrad_courses_deduplicates_by_course_code(self):
        raw_courses = [
            {
                "fah": "PLAN-A",
                "kcdm": "GEIP4004",
                "xf": 2,
                "khfsmc": "考试",
                "kcmc": "新时代中国特色社会主义理论与实践",
                "tjkkxnxq": "秋季",
                "kzmc": "公共学位课（硕）",
                "kcxzmc": "学位课",
                "kclbmc": "公共学位课",
                "kkyxmc": "马克思主义学院",
                "xszxs": "32",
                "xsllxs": "32",
            },
            {
                "fah": "PLAN-B",
                "kcdm": "GEIP4004",
                "xf": 2,
                "khfsmc": "考试",
                "kcmc": "新时代中国特色社会主义理论与实践",
                "tjkkxnxq": "秋季",
                "kzmc": "公共学位课（博）",
                "kcxzmc": "学位课",
                "kclbmc": "公共学位课",
                "kkyxmc": "马克思主义学院",
                "xszxs": "32",
                "xsllxs": "32",
            },
        ]

        merged = merge_postgrad_courses(raw_courses, major_code="085410")

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["course_code"], "GEIP4004")
        self.assertEqual(merged[0]["source_plan_IDs"], ["PLAN-A", "PLAN-B"])
        self.assertEqual(merged[0]["source_tracks"], ["公共学位课（硕）", "公共学位课（博）"])

    def test_merge_postgrad_courses_does_not_warn_for_track_only_differences(self):
        raw_courses = [
            {
                "fah": "PLAN-A",
                "kcdm": "AUTO5001",
                "xf": 2,
                "kcmc": "线性系统理论",
                "tjkkxnxq": "秋季",
                "kzmc": "专业学位类别核心课",
                "kcxzmc": "学位课",
                "kclbmc": "学科核心课",
                "kkyxmc": "智能科学与工程学院",
                "xszxs": "32",
                "xsllxs": "32",
            },
            {
                "fah": "PLAN-B",
                "kcdm": "AUTO5001",
                "xf": 2,
                "kcmc": "线性系统理论",
                "tjkkxnxq": "秋季",
                "kzmc": "硕士层次核心课",
                "kcxzmc": "学位课",
                "kclbmc": "学科核心课",
                "kkyxmc": "智能科学与工程学院",
                "xszxs": "32",
                "xsllxs": "32",
            },
        ]

        with patch("hoa_cli.core.postgrad.logger.warning") as mock_warning:
            merged = merge_postgrad_courses(raw_courses, major_code="085406")

        self.assertEqual(len(merged), 1)
        mock_warning.assert_not_called()

    def test_should_exclude_course_item_uses_course_group_name(self):
        excluded_course = {"kzmc": "MT模块：航空宇航科学与技术学科硕士选修课程清单"}
        kept_course = {"kzmc": "学科核心课"}

        self.assertTrue(should_exclude_course_item(excluded_course))
        self.assertFalse(should_exclude_course_item(kept_course))

    def test_write_toml_supports_info_arrays(self):
        data = {
            "info": {
                "study_level": "postgrad",
                "source_plan_IDs": ["PLAN-A", "PLAN-B"],
            },
            "courses": [
                {
                    "course_code": "GEIP4004",
                    "hours": {"theory": 32, "lab": 0},
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.toml"
            write_toml(path, data)

            with open(path, "rb") as f:
                loaded = tomllib.load(f)

        self.assertEqual(loaded["info"]["source_plan_IDs"], ["PLAN-A", "PLAN-B"])
        self.assertEqual(loaded["courses"][0]["course_code"], "GEIP4004")


if __name__ == "__main__":
    unittest.main()

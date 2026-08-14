import importlib.util
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "audit_postgrad_modules.py"
SPEC = importlib.util.spec_from_file_location("audit_postgrad_modules", SCRIPT_PATH)
assert SPEC and SPEC.loader
audit_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_module)
audit_postgrad_modules = audit_module.audit_postgrad_modules


class PostgradModuleAuditTests(unittest.TestCase):
    def test_audit_finds_tree_and_course_only_modules_and_skips_international(self):
        mappings = {
            "202509": {
                "0810": {
                    "major_name": "信息与通信工程",
                    "plans": [
                        {
                            "plan_id": "DOMESTIC",
                            "name": "信息与通信工程-学术学位-硕士生培养方案",
                            "bgid": "BG-1",
                        },
                        {
                            "plan_id": "INTERNATIONAL",
                            "name": "信息与通信工程-硕士生培养方案(留学生)",
                            "bgid": "BG-2",
                        },
                    ],
                }
            }
        }

        def fetch_groups(plan_id, bgid):
            self.assertEqual((plan_id, bgid), ("DOMESTIC", "BG-1"))
            return [
                {"kzid": "root", "fkzid": "-1", "kzmc": "根节点"},
                {
                    "kzid": "recommended",
                    "fkzid": "root",
                    "kzmc": "推荐选修课模块",
                },
                {
                    "kzid": "mx",
                    "fkzid": "recommended",
                    "kzmc": "MX模块：智能科学与技术学科硕士选修课程清单",
                },
                {"kzid": "mx-leaf", "fkzid": "mx", "kzmc": "选修课"},
                {"kzid": "flat-leaf", "fkzid": "root", "kzmc": "选修课"},
            ]

        def fetch_courses(plan_id, group_id, zyfx, bgid):
            self.assertEqual((plan_id, zyfx, bgid), ("DOMESTIC", "", "BG-1"))
            if group_id == "mx-leaf":
                return [{"kcdm": "AI5001", "kzmc": "选修课"}]
            if group_id == "flat-leaf":
                return [
                    {
                        "kcdm": "MECH5001",
                        "kzmc": "DD模块：机械工程学科博士选修课程清单",
                    }
                ]
            return []

        report = audit_postgrad_modules(
            mappings,
            bbh="202509",
            group_fetcher=fetch_groups,
            course_fetcher=fetch_courses,
        )

        self.assertTrue(report["complete"])
        self.assertEqual(report["stats"]["international_plans_skipped"], 1)
        self.assertEqual(report["stats"]["modules_found"], 2)
        modules = {item["module_codes"][0]: item for item in report["modules"]}
        self.assertEqual(modules["MX"]["container_types"], ["recommended"])
        self.assertEqual(modules["MX"]["course_codes"], ["AI5001"])
        self.assertIn("group_tree", modules["MX"]["discovered_from"])
        self.assertEqual(modules["MX"]["relations"][0]["container_type"], "recommended")
        self.assertEqual(modules["MX"]["relations"][0]["plan_ID"], "DOMESTIC")
        self.assertEqual(modules["DD"]["course_codes"], ["MECH5001"])
        self.assertIn("course_kzmc", modules["DD"]["discovered_from"])

    def test_audit_marks_empty_group_responses_as_incomplete(self):
        mappings = {
            "202509": {
                "0810": {
                    "major_name": "信息与通信工程",
                    "plans": [{"plan_id": "PLAN-A", "name": "硕士生培养方案", "bgid": ""}],
                }
            }
        }

        report = audit_postgrad_modules(
            mappings,
            bbh="202509",
            group_fetcher=lambda plan_id, bgid: [],
            scan_courses=False,
        )

        self.assertFalse(report["complete"])
        self.assertEqual(report["stats"]["plans_with_empty_group_response"], 1)
        self.assertEqual(report["issues"][0]["type"], "empty_group_response")

    def test_audit_resumes_after_completed_plan(self):
        mappings = {
            "202509": {
                "0810": {
                    "major_name": "信息与通信工程",
                    "plans": [
                        {"plan_id": "PLAN-A", "name": "硕士生培养方案 A", "bgid": ""},
                        {"plan_id": "PLAN-B", "name": "硕士生培养方案 B", "bgid": ""},
                    ],
                }
            }
        }
        module_group = [
            {
                "kzid": "module",
                "fkzid": "-1",
                "kzmc": "MC模块：信息与通信工程学科硕士选修课程清单",
            }
        ]

        first_report = audit_postgrad_modules(
            mappings,
            bbh="202509",
            scan_courses=False,
            group_fetcher=lambda plan_id, bgid: module_group if plan_id == "PLAN-A" else [],
        )
        self.assertFalse(first_report["complete"])
        self.assertEqual(first_report["completed_plan_IDs"], ["PLAN-A"])

        fetched_on_resume = []

        def resumed_fetch(plan_id, bgid):
            fetched_on_resume.append(plan_id)
            return module_group

        resumed_report = audit_postgrad_modules(
            mappings,
            bbh="202509",
            scan_courses=False,
            group_fetcher=resumed_fetch,
            resume_report=first_report,
        )

        self.assertTrue(resumed_report["complete"])
        self.assertEqual(fetched_on_resume, ["PLAN-B"])
        self.assertEqual(resumed_report["completed_plan_IDs"], ["PLAN-A", "PLAN-B"])
        relations = resumed_report["modules"][0]["relations"]
        self.assertEqual({relation["plan_ID"] for relation in relations}, {"PLAN-A", "PLAN-B"})


if __name__ == "__main__":
    unittest.main()

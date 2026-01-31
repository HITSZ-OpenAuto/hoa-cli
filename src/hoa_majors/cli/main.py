import argparse
import sys
from pathlib import Path

from hoa_majors import __version__
from hoa_majors.cli import audit, courses, crawl, info, plans, repo, search
from hoa_majors.config import DEFAULT_DATA_DIR, logger


def main():
    parser = argparse.ArgumentParser(
        description="HOA Majors CLI - 哈工大（深圳）培养方案抓取与查询工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"hoa-majors {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # crawl
    crawl_parser = subparsers.add_parser("crawl", help="抓取培养方案与课程数据")
    crawl_parser.add_argument(
        "--grades",
        nargs="+",
        default=["2019", "2020", "2021", "2022", "2023", "2024", "2025"],
        help="要抓取的年级列表",
    )
    crawl_parser.add_argument(
        "--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="数据存储目录"
    )

    # search
    search_parser = subparsers.add_parser("search", help="在数据中搜索课程代码")
    search_parser.add_argument("code", nargs="?", help="要搜索的课程代码")
    search_parser.add_argument(
        "--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="数据存储目录"
    )

    # audit
    audit_parser = subparsers.add_parser("audit", help="审计课程名称与代码的冲突")
    audit_parser.add_argument(
        "--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="数据存储目录"
    )
    audit_parser.add_argument("--output", type=Path, help="保存冲突报告的路径")

    # plans
    plans_parser = subparsers.add_parser("plans", help="列出所有已抓取的培养方案")
    plans_parser.add_argument(
        "--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="数据存储目录"
    )

    # courses
    courses_parser = subparsers.add_parser("courses", help="列出特定培养方案的所有课程")
    courses_parser.add_argument("plan_id", help="培养方案 ID (fah)")
    courses_parser.add_argument(
        "--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="数据存储目录"
    )

    # info
    info_parser = subparsers.add_parser("info", help="获取培养方案中特定课程的详细信息")
    info_parser.add_argument("plan_id", help="培养方案 ID (fah)")
    info_parser.add_argument("course_code", help="课程代码")
    info_parser.add_argument(
        "--json",
        action="store_true",
        help="以纯 JSON 输出（仅输出课程与成绩构成等信息，不含格式化文本）",
    )
    info_parser.add_argument(
        "--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="数据存储目录"
    )

    # repo
    repo_parser = subparsers.add_parser("repo", help="获取课程对应的 OpenAuto 仓库 ID")
    repo_parser.add_argument("plan_id", help="培养方案 ID (fah)")
    repo_parser.add_argument("course_code", help="课程代码")
    repo_parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="数据存储目录")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if args.command == "crawl":
        mapping_file = args.data_dir / "major_mapping.json"
        logger.info(f"开始抓取年级映射: {args.grades}")
        crawl.crawl_majors(args.grades, mapping_file)
        logger.info("开始抓取课程详细数据")
        crawl.crawl_courses(mapping_file, args.data_dir)
        logger.info("抓取任务完成")
    elif args.command == "search":
        code = args.code
        if not code:
            code = input("请输入课程代码: ").strip()
        results = search.locate(code, args.data_dir)
        print("\n" + "=" * 40 + "\n查询结果\n" + "=" * 40 + "\n")
        if not results:
            print("未找到该课程代码。")
        else:
            print(f"找到 {len(results)} 个匹配：\n")
            for path, course in results:
                print(f"文件: {path.name}")
                print(f"课程名称: {course.get('course_name', 'N/A')}")
                print(f"课程性质: {course.get('course_nature', 'N/A')}")
                print(f"学分: {course.get('credit', 'N/A')}")
                print("-" * 40)
    elif args.command == "audit":
        mapping = audit.scan(args.data_dir)
        report_file = args.output or args.data_dir / "course_code_conflicts.txt"
        audit.report_conflicts(mapping, report_file)
    elif args.command == "plans":
        plans.list_plans(args.data_dir)
    elif args.command == "courses":
        courses.list_courses(args.plan_id, args.data_dir)
    elif args.command == "info":
        info.get_course_info(args.plan_id, args.course_code, args.data_dir, as_json=args.json)
    elif args.command == "repo":
        repo.run(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

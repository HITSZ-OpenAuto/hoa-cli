import argparse
import sys
from pathlib import Path

from hoa_cli import __version__
from hoa_cli.cli import courses, crawl, info, plans, repo
from hoa_cli.config import DEFAULT_DATA_DIR, logger


def main():
    parser = argparse.ArgumentParser(
        description="HOA CLI - 哈工大（深圳）培养方案抓取与查询工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"hoa-cli {__version__}")

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

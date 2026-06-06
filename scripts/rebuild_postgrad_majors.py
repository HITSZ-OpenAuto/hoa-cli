#!/usr/bin/env python3
"""Rebuild selected postgrad majors without rerunning the whole batch.

Examples:
  python scripts/rebuild_postgrad_majors.py --bbh 202509 --major-codes 0813 085801
  python scripts/rebuild_postgrad_majors.py --bbh 202509 --major-codes 1405 --refresh-mapping
"""

from __future__ import annotations

import argparse
from pathlib import Path

from hoa_cli.cli.crawl_postgrad import (
    build_postgrad_mappings,
    crawl_postgrad_courses,
    load_postgrad_mappings,
)
from hoa_cli.config import DEFAULT_DATA_DIR, logger


def _validate_requested_majors(mapping_path: Path, bbh: str, major_codes: set[str]) -> set[str]:
    """Return the subset of requested major codes that exists in the mapping."""
    all_mappings = load_postgrad_mappings(mapping_path)
    majors = all_mappings.get(bbh, {}) if isinstance(all_mappings, dict) else {}
    existing_codes = set(majors.keys()) if isinstance(majors, dict) else set()

    missing_codes = sorted(major_codes - existing_codes)
    for code in missing_codes:
        logger.warning(f"major_code={code} 不在版本 {bbh} 的研究生映射中，已跳过")

    return major_codes & existing_codes


def main() -> None:
    parser = argparse.ArgumentParser(description="按 major_code 小范围重抓研究生培养方案课程数据")
    parser.add_argument("--bbh", required=True, help="版本号，如 202509")
    parser.add_argument(
        "--major-codes",
        nargs="+",
        required=True,
        help="要重抓的专业代码列表，如 0813 085501 085801 1305",
    )
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="数据存储目录")
    parser.add_argument(
        "--mapping-file",
        type=Path,
        default=None,
        help="研究生映射文件路径，默认使用 {data_dir}/postgrad_mapping.json",
    )
    parser.add_argument(
        "--refresh-mapping",
        action="store_true",
        help="先重新抓取该 bbh 的研究生映射，再执行小范围重抓",
    )
    args = parser.parse_args()

    mapping_path = args.mapping_file or (args.data_dir / "postgrad_mapping.json")
    if args.refresh_mapping or not mapping_path.exists():
        logger.info(f"刷新研究生映射: {args.bbh}")
        all_mappings = load_postgrad_mappings(mapping_path) if mapping_path.exists() else {}
        if not isinstance(all_mappings, dict):
            all_mappings = {}
        all_mappings.update(build_postgrad_mappings([args.bbh], mapping_path))

    requested_codes = {code.strip() for code in args.major_codes if code.strip()}
    selected_codes = _validate_requested_majors(mapping_path, args.bbh, requested_codes)
    if not selected_codes:
        logger.error("没有可重抓的 major_code")
        return

    logger.info(f"开始小范围重抓: bbh={args.bbh}, major_codes={sorted(selected_codes)}")
    crawl_postgrad_courses(mapping_path, args.data_dir, major_codes=selected_codes, bbhs={args.bbh})
    logger.info("小范围重抓完成")


if __name__ == "__main__":
    main()

import argparse
import json
from pathlib import Path

from hoa_cli.config import DEFAULT_DATA_DIR
from hoa_cli.core.fetcher import get_postgrad_fah_list
from hoa_cli.core.postgrad import build_postgrad_mapping


def _filter_mapping(mapping: dict[str, dict], major_codes: list[str] | None) -> dict[str, dict]:
    if not major_codes:
        return mapping
    wanted = {code.strip() for code in major_codes if code.strip()}
    return {code: entry for code, entry in mapping.items() if code in wanted}


def main():
    parser = argparse.ArgumentParser(description="抓取并打印研究生专业方案号列表")
    parser.add_argument("--bbh", required=True, help="版本号，如 202509")
    parser.add_argument("--major-codes", nargs="*", help="要筛选的专业代码列表")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="可选：将筛选后的结果写入 JSON 文件",
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
    filtered = _filter_mapping(mapping, args.major_codes)

    print(f"bbh={args.bbh} major_count={len(filtered)}")
    for major_code, entry in filtered.items():
        major_name = entry.get("major_name", "")
        school_name = entry.get("school_name", "")
        print(f"{major_code} {major_name} [{school_name}]")
        for plan in entry.get("plans", []):
            print(f"  - {plan.get('plan_id')} | {plan.get('name')}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        payload = {args.bbh: filtered}
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Audit postgrad elective modules without changing generated plan data.

The audit scans both the raw course-group tree and, by default, every leaf
group's returned course rows. The latter is required because the JW API may
return a generic leaf group while exposing the real module name only in a
course row's ``kzmc`` field.

Examples:
  python scripts/audit_postgrad_modules.py --bbh 202509
  python scripts/audit_postgrad_modules.py --bbh 202509 --major-codes 0810 085402
  python scripts/audit_postgrad_modules.py --bbh 202509 --tree-only --output audit.json
  python scripts/audit_postgrad_modules.py --bbh 202509 --resume audit.json
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from hoa_cli.cli.crawl_postgrad import load_postgrad_mappings
from hoa_cli.config import DEFAULT_DATA_DIR, logger
from hoa_cli.core.fetcher import (
    fetch_postgrad_courses_by_group,
    get_postgrad_course_groups,
)
from hoa_cli.core.postgrad import (
    POSTGRAD_MODULE_CONTAINERS,
    derive_postgrad_degree_levels,
    derive_postgrad_zyfx,
    extract_postgrad_module_code,
    is_international_postgrad_plan_name,
    is_postgrad_elective_module_name,
    normalize_postgrad_module_name,
)

GroupFetcher = Callable[[str, str], list[dict[str, Any]]]
CourseFetcher = Callable[[str, str, str, str], list[dict[str, Any]]]
ProgressCallback = Callable[[dict[str, Any]], None]


def _normalize_groups(groups: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    normalized: dict[str, dict[str, str]] = {}
    for group in groups:
        group_id = str(group.get("kzid") or "").strip()
        if not group_id:
            continue
        normalized[group_id] = {
            "kzid": group_id,
            "fkzid": str(group.get("fkzid") or "").strip(),
            "kzmc": str(group.get("kzmc") or "").strip(),
        }
    return normalized


def _leaf_group_ids(groups_by_id: dict[str, dict[str, str]]) -> list[str]:
    parent_ids = {
        group["fkzid"]
        for group in groups_by_id.values()
        if group["fkzid"] and group["fkzid"] != "-1"
    }
    return sorted(group_id for group_id in groups_by_id if group_id not in parent_ids)


def _ancestor_ids(groups_by_id: dict[str, dict[str, str]], group_id: str) -> list[str]:
    ancestors: list[str] = []
    seen: set[str] = set()
    current_id = group_id
    while current_id and current_id != "-1" and current_id not in seen:
        seen.add(current_id)
        ancestors.append(current_id)
        current = groups_by_id.get(current_id)
        current_id = current["fkzid"] if current else ""
    return ancestors


def _container_types(groups_by_id: dict[str, dict[str, str]], group_id: str) -> set[str]:
    return {
        POSTGRAD_MODULE_CONTAINERS[name]
        for ancestor_id in _ancestor_ids(groups_by_id, group_id)
        if (name := groups_by_id.get(ancestor_id, {}).get("kzmc", "")) in POSTGRAD_MODULE_CONTAINERS
    }


def _nearest_module_name(
    groups_by_id: dict[str, dict[str, str]], group_id: str
) -> tuple[str, str] | None:
    for ancestor_id in _ancestor_ids(groups_by_id, group_id):
        name = groups_by_id.get(ancestor_id, {}).get("kzmc", "")
        if is_postgrad_elective_module_name(name):
            return name, ancestor_id
    return None


def _new_module_record(module_name: str) -> dict[str, Any]:
    normalized_name = normalize_postgrad_module_name(module_name)
    return {
        "normalized_name": normalized_name,
        "raw_names": set(),
        "module_codes": set(),
        "degree_levels": set(),
        "container_types": set(),
        "major_codes": set(),
        "major_names": set(),
        "source_plan_IDs": set(),
        "source_plan_names": set(),
        "source_group_IDs": set(),
        "queried_leaf_group_IDs": set(),
        "course_codes": set(),
        "discovered_from": set(),
        "relations": set(),
    }


def _record_module(
    modules: dict[str, dict[str, Any]],
    *,
    module_name: str,
    discovered_from: str,
    major_code: str,
    major_name: str,
    plan_id: str,
    plan_name: str,
    group_id: str = "",
    leaf_group_id: str = "",
    container_types: set[str] | None = None,
    course_code: str = "",
) -> None:
    key = normalize_postgrad_module_name(module_name)
    record = modules.setdefault(key, _new_module_record(module_name))
    record["raw_names"].add(module_name.strip())
    if module_code := extract_postgrad_module_code(module_name):
        record["module_codes"].add(module_code)
    degree_levels = derive_postgrad_degree_levels(module_name)
    record["degree_levels"].update(degree_levels or derive_postgrad_degree_levels(plan_name))
    if container_types:
        record["container_types"].discard("unknown")
        record["container_types"].update(container_types)
    elif not record["container_types"]:
        record["container_types"].add("unknown")
    record["major_codes"].add(major_code)
    record["major_names"].add(major_name)
    record["source_plan_IDs"].add(plan_id)
    record["source_plan_names"].add(plan_name)
    if group_id:
        record["source_group_IDs"].add(group_id)
    if leaf_group_id:
        record["queried_leaf_group_IDs"].add(leaf_group_id)
    if course_code:
        record["course_codes"].add(course_code)
    record["discovered_from"].add(discovered_from)
    for container_type in container_types or {"unknown"}:
        record["relations"].add((major_code, major_name, plan_id, plan_name, container_type))


def _serialize_module(record: dict[str, Any]) -> dict[str, Any]:
    serialized = {}
    for key, value in record.items():
        if key == "relations":
            serialized[key] = [
                {
                    "major_code": relation[0],
                    "major_name": relation[1],
                    "plan_ID": relation[2],
                    "plan_name": relation[3],
                    "container_type": relation[4],
                }
                for relation in sorted(value)
            ]
        else:
            serialized[key] = sorted(value) if isinstance(value, set) else value
    serialized["course_count"] = len(record["course_codes"])
    return serialized


def _deserialize_module(record: dict[str, Any]) -> dict[str, Any]:
    restored = _new_module_record(str(record.get("normalized_name") or ""))
    for key in restored:
        if key == "relations":
            restored[key] = {
                (
                    str(relation.get("major_code") or ""),
                    str(relation.get("major_name") or ""),
                    str(relation.get("plan_ID") or ""),
                    str(relation.get("plan_name") or ""),
                    str(relation.get("container_type") or "unknown"),
                )
                for relation in record.get("relations", [])
                if isinstance(relation, dict)
            }
        elif isinstance(restored[key], set):
            restored[key] = set(record.get(key, []))
    return restored


def _atomic_write_report(path: Path, report: dict[str, Any]) -> None:
    """Atomically replace a checkpoint without exposing a partially written JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.tmp")
    temporary_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary_path.replace(path)


def _default_output_path(bbh: str) -> Path:
    timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    candidate = Path(f"postgrad_module_audit_{bbh}_{timestamp}.json")
    suffix = 1
    while candidate.exists():
        candidate = Path(f"postgrad_module_audit_{bbh}_{timestamp}_{suffix}.json")
        suffix += 1
    return candidate


def _validate_resume_report(
    report: dict[str, Any], *, bbh: str, major_codes: set[str] | None, scan_courses: bool
) -> None:
    if report.get("schema_version") != 2:
        raise ValueError("只能恢复 schema_version=2 的审计报告")
    if report.get("bbh") != bbh:
        raise ValueError(f"恢复报告 bbh={report.get('bbh')} 与参数 bbh={bbh} 不一致")
    if bool(report.get("scan_courses")) != scan_courses:
        raise ValueError("恢复时 --tree-only 必须与原报告保持一致")
    expected_codes = sorted(major_codes) if major_codes else []
    if report.get("selected_major_codes", []) != expected_codes:
        raise ValueError("恢复时 --major-codes 必须与原报告保持一致")


def audit_postgrad_modules(
    all_mappings: dict[str, Any],
    *,
    bbh: str,
    major_codes: set[str] | None = None,
    scan_courses: bool = True,
    group_fetcher: GroupFetcher = get_postgrad_course_groups,
    course_fetcher: CourseFetcher = fetch_postgrad_courses_by_group,
    resume_report: dict[str, Any] | None = None,
    progress_callback: ProgressCallback | None = None,
) -> dict[str, Any]:
    """Return a module inventory, optionally resuming at completed-plan boundaries."""
    majors = all_mappings.get(bbh, {})
    if not isinstance(majors, dict):
        majors = {}

    if resume_report:
        _validate_resume_report(
            resume_report,
            bbh=bbh,
            major_codes=major_codes,
            scan_courses=scan_courses,
        )

    modules = {
        str(record.get("normalized_name") or ""): _deserialize_module(record)
        for record in (resume_report or {}).get("modules", [])
        if isinstance(record, dict) and record.get("normalized_name")
    }
    suspicious_names = set((resume_report or {}).get("suspicious_names", []))
    skipped_international_plans = list((resume_report or {}).get("skipped_international_plans", []))
    skipped_international_plan_ids = {
        str(plan.get("plan_ID") or "")
        for plan in skipped_international_plans
        if isinstance(plan, dict)
    }
    completed_plan_ids = set((resume_report or {}).get("completed_plan_IDs", []))
    scanned_major_codes = set((resume_report or {}).get("scanned_major_codes", []))
    issues: list[dict[str, str]] = []
    stats: defaultdict[str, int] = defaultdict(
        int, {key: int(value) for key, value in (resume_report or {}).get("stats", {}).items()}
    )
    started_at = (resume_report or {}).get("generated_at") or datetime.now(UTC).isoformat()

    target_plan_ids: set[str] = set()
    for major_code, major_entry in majors.items():
        if major_codes and major_code not in major_codes:
            continue
        if not isinstance(major_entry, dict):
            continue
        for plan in major_entry.get("plans", []):
            if not isinstance(plan, dict):
                continue
            plan_id = str(plan.get("plan_id") or "").strip()
            plan_name = str(plan.get("name") or "").strip()
            if plan_id and not is_international_postgrad_plan_name(plan_name):
                target_plan_ids.add(plan_id)

    def snapshot(status: str) -> dict[str, Any]:
        serialized_modules = [_serialize_module(modules[key]) for key in sorted(modules)]
        current_stats = dict(stats)
        current_stats["majors_scanned"] = len(scanned_major_codes)
        current_stats["modules_found"] = len(serialized_modules)
        current_stats["unique_module_courses"] = len(
            {code for record in modules.values() for code in record["course_codes"]}
        )
        current_stats["plans_completed"] = len(completed_plan_ids)
        current_stats["plans_targeted"] = len(target_plan_ids)
        complete = target_plan_ids <= completed_plan_ids and not issues
        return {
            "schema_version": 2,
            "generated_at": started_at,
            "updated_at": datetime.now(UTC).isoformat(),
            "bbh": bbh,
            "status": "complete" if complete else status,
            "complete": complete,
            "scan_courses": scan_courses,
            "selected_major_codes": sorted(major_codes) if major_codes else [],
            "completed_plan_IDs": sorted(completed_plan_ids),
            "scanned_major_codes": sorted(scanned_major_codes),
            "stats": dict(sorted(current_stats.items())),
            "modules": serialized_modules,
            "suspicious_names": sorted(suspicious_names),
            "skipped_international_plans": skipped_international_plans,
            "issues": issues,
        }

    def checkpoint(status: str = "running") -> None:
        if progress_callback:
            progress_callback(snapshot(status))

    checkpoint()

    for major_code, major_entry in sorted(majors.items()):
        if major_codes and major_code not in major_codes:
            continue
        if not isinstance(major_entry, dict):
            continue

        major_name = str(major_entry.get("major_name") or "").strip()
        zyfx = derive_postgrad_zyfx(major_code)
        plans = major_entry.get("plans", [])
        if not isinstance(plans, list):
            continue

        scanned_major_codes.add(major_code)
        for plan in plans:
            if not isinstance(plan, dict):
                continue
            plan_id = str(plan.get("plan_id") or "").strip()
            plan_name = str(plan.get("name") or "").strip()
            bgid = str(plan.get("bgid") or "").strip()
            if not plan_id:
                continue
            if is_international_postgrad_plan_name(plan_name):
                if plan_id not in skipped_international_plan_ids:
                    stats["international_plans_skipped"] += 1
                    skipped_international_plan_ids.add(plan_id)
                    skipped_international_plans.append(
                        {
                            "major_code": major_code,
                            "major_name": major_name,
                            "plan_ID": plan_id,
                            "plan_name": plan_name,
                        }
                    )
                    checkpoint()
                continue
            if plan_id in completed_plan_ids:
                continue

            stats["plan_attempts"] += 1
            logger.info("审计研究生课组: %s %s %s", bbh, major_code, plan_name)
            raw_groups = group_fetcher(plan_id, bgid)
            if not raw_groups:
                stats["plans_with_empty_group_response"] += 1
                issues.append(
                    {
                        "type": "empty_group_response",
                        "major_code": major_code,
                        "major_name": major_name,
                        "plan_ID": plan_id,
                        "plan_name": plan_name,
                    }
                )
                checkpoint("incomplete")
                continue
            groups_by_id = _normalize_groups(raw_groups)
            stats["groups_scanned"] += len(groups_by_id)

            for group_id, group in groups_by_id.items():
                group_name = group["kzmc"]
                if is_postgrad_elective_module_name(group_name):
                    _record_module(
                        modules,
                        module_name=group_name,
                        discovered_from="group_tree",
                        major_code=major_code,
                        major_name=major_name,
                        plan_id=plan_id,
                        plan_name=plan_name,
                        group_id=group_id,
                        container_types=_container_types(groups_by_id, group_id),
                    )
                elif group_name not in POSTGRAD_MODULE_CONTAINERS and (
                    "模块" in group_name
                    or "选修课程清单" in group_name
                    or "选修课清单" in group_name
                ):
                    suspicious_names.add(group_name)

            if scan_courses:
                for leaf_group_id in _leaf_group_ids(groups_by_id):
                    stats["leaf_groups_queried"] += 1
                    module_ancestor = _nearest_module_name(groups_by_id, leaf_group_id)
                    container_types = _container_types(groups_by_id, leaf_group_id)
                    raw_courses = course_fetcher(plan_id, leaf_group_id, zyfx, bgid)
                    stats["course_rows_scanned"] += len(raw_courses)

                    for course in raw_courses:
                        course_code = str(course.get("kcdm") or "").strip()
                        row_group_name = str(course.get("kzmc") or "").strip()

                        if module_ancestor:
                            module_name, module_group_id = module_ancestor
                            _record_module(
                                modules,
                                module_name=module_name,
                                discovered_from="module_branch_course",
                                major_code=major_code,
                                major_name=major_name,
                                plan_id=plan_id,
                                plan_name=plan_name,
                                group_id=module_group_id,
                                leaf_group_id=leaf_group_id,
                                container_types=container_types,
                                course_code=course_code,
                            )

                        if is_postgrad_elective_module_name(row_group_name):
                            _record_module(
                                modules,
                                module_name=row_group_name,
                                discovered_from="course_kzmc",
                                major_code=major_code,
                                major_name=major_name,
                                plan_id=plan_id,
                                plan_name=plan_name,
                                leaf_group_id=leaf_group_id,
                                container_types=container_types,
                                course_code=course_code,
                            )
                        elif row_group_name not in POSTGRAD_MODULE_CONTAINERS and (
                            "模块" in row_group_name
                            or "选修课程清单" in row_group_name
                            or "选修课清单" in row_group_name
                        ):
                            suspicious_names.add(row_group_name)

            completed_plan_ids.add(plan_id)
            checkpoint()

    report = snapshot("complete")
    checkpoint(report["status"])
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="审计研究生专业选修模块，不修改培养方案数据")
    parser.add_argument("--bbh", required=True, help="研究生培养方案版本，如 202509")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="数据目录")
    parser.add_argument(
        "--mapping-file",
        type=Path,
        default=None,
        help="研究生映射文件，默认使用 {data_dir}/postgrad_mapping.json",
    )
    parser.add_argument(
        "--major-codes",
        nargs="+",
        default=None,
        help="只审计指定专业代码；默认审计该版本全部专业",
    )
    parser.add_argument(
        "--tree-only",
        action="store_true",
        help="只检查课组树；更快，但无法发现仅出现在课程 kzmc 中的模块",
    )
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--output",
        type=Path,
        default=None,
        help="新报告路径；如果文件已存在则拒绝覆盖",
    )
    output_group.add_argument(
        "--resume",
        type=Path,
        default=None,
        help="从已有 schema_version=2 报告断点续跑，并原子更新该检查点",
    )
    args = parser.parse_args()

    mapping_path = args.mapping_file or (args.data_dir / "postgrad_mapping.json")
    all_mappings = load_postgrad_mappings(mapping_path)
    if args.bbh not in all_mappings:
        raise SystemExit(f"版本 {args.bbh} 不在研究生映射文件中: {mapping_path}")

    selected_codes = (
        {code.strip() for code in args.major_codes if code.strip()} if args.major_codes else None
    )
    resume_report = None
    if args.resume:
        output_path = args.resume
        if not output_path.is_file():
            raise SystemExit(f"恢复报告不存在: {output_path}")
        try:
            resume_report = json.loads(output_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"无法读取恢复报告 {output_path}: {exc}") from exc
        try:
            _validate_resume_report(
                resume_report,
                bbh=args.bbh,
                major_codes=selected_codes,
                scan_courses=not args.tree_only,
            )
        except ValueError as exc:
            raise SystemExit(f"无法恢复审计: {exc}") from exc
        if resume_report.get("complete"):
            logger.info("报告已经完成，无需续跑: %s", output_path.resolve())
            return
    else:
        output_path = args.output or _default_output_path(args.bbh)
        if output_path.exists():
            raise SystemExit(
                f"输出文件已存在，拒绝覆盖；请更换 --output 或使用 --resume: {output_path}"
            )

    logger.info("审计检查点: %s", output_path.resolve())
    try:
        report = audit_postgrad_modules(
            all_mappings,
            bbh=args.bbh,
            major_codes=selected_codes,
            scan_courses=not args.tree_only,
            resume_report=resume_report,
            progress_callback=lambda checkpoint: _atomic_write_report(output_path, checkpoint),
        )
    except KeyboardInterrupt:
        logger.warning("审计已中断；使用 --resume %s 继续", output_path)
        raise
    except ValueError as exc:
        raise SystemExit(f"无法恢复审计: {exc}") from exc

    stats = report["stats"]
    logger.info(
        "审计完成: modules=%s plans=%s skipped_international=%s course_rows=%s",
        stats.get("modules_found", 0),
        stats.get("plans_completed", 0),
        stats.get("international_plans_skipped", 0),
        stats.get("course_rows_scanned", 0),
    )
    logger.info("报告已写入: %s", output_path.resolve())
    if not report["complete"]:
        logger.error("审计报告不完整，请检查报告 issues 和请求日志")
        raise SystemExit(2)


if __name__ == "__main__":
    main()

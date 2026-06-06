import re
from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from hoa_cli.config import logger
from hoa_cli.core.parser import normalize_course

EXCLUDED_GROUP_NAMES = {"推荐选修课模块", "其他选修课模块"}
EXCLUDED_GROUP_KEYWORDS = ("模块", "选修课程清单")


def derive_major_code(item: dict[str, Any]) -> str:
    """Return zyfxdm when available, otherwise fall back to zydm."""
    return str(item.get("zyfxdm") or item.get("zydm") or "").strip()


def derive_major_name(item: dict[str, Any]) -> str:
    """Build a display name from major + optional direction."""
    zymc = str(item.get("zymc") or "").strip()
    zyfxmc = str(item.get("zyfxmc") or "").strip()
    if zymc and zyfxmc:
        return f"{zymc}（{zyfxmc}）"
    if zymc:
        return zymc
    return _derive_major_name_from_famc(str(item.get("famc") or "").strip())


def _derive_major_name_from_famc(famc: str) -> str:
    """Extract major name from famc when dedicated name fields are missing."""
    if not famc:
        return ""

    match = re.search(r"[】\]](.*)", famc)
    suffix = match.group(1) if match else famc
    suffix = suffix.lstrip("- ").strip()
    if not suffix:
        return ""
    return suffix.split("-", 1)[0].strip()


def should_skip_postgrad_plan(item: dict[str, Any]) -> bool:
    """Return True when a postgrad plan record should be excluded."""
    zydm = str(item.get("zydm") or "").strip()
    if zydm.startswith("X"):
        return True
    falxdm = item.get("falxdm")
    if falxdm is not None and str(falxdm).strip() != "1":
        return True
    return not derive_major_code(item)


def build_postgrad_mapping(raw_items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Group postgrad plans by major_code."""
    mapping: dict[str, dict[str, Any]] = {}

    for item in raw_items:
        if should_skip_postgrad_plan(item):
            continue

        major_code = derive_major_code(item)
        entry = mapping.setdefault(
            major_code,
            {
                "major_code": major_code,
                "major_name": derive_major_name(item),
                "school_name": str(item.get("yxmc") or "").strip(),
                "plans": [],
            },
        )

        if not entry["major_name"]:
            entry["major_name"] = derive_major_name(item)
        if not entry["school_name"]:
            entry["school_name"] = str(item.get("yxmc") or "").strip()

        plan_id = str(item.get("fah") or "").strip()
        if not plan_id:
            continue

        if any(plan.get("plan_id") == plan_id for plan in entry["plans"]):
            continue

        entry["plans"].append(
            {
                "name": str(item.get("famc") or "").strip(),
                "plan_id": plan_id,
                "bgid": str(item.get("bgid") or "").strip(),
            }
        )

    for entry in mapping.values():
        entry["plans"].sort(key=lambda plan: (plan.get("name", ""), plan.get("plan_id", "")))

    return dict(sorted(mapping.items()))


def _normalized_group(group: dict[str, Any]) -> dict[str, str]:
    return {
        "kzid": str(group.get("kzid") or "").strip(),
        "fkzid": str(group.get("fkzid") or "").strip(),
        "kzmc": str(group.get("kzmc") or "").strip(),
    }


def should_exclude_group_name(
    group_name: str,
    *,
    excluded_names: set[str] | None = None,
    excluded_keywords: tuple[str, ...] = EXCLUDED_GROUP_KEYWORDS,
) -> bool:
    """Return True when a group name should be excluded from traversal."""
    normalized_name = group_name.strip()
    if not normalized_name:
        return False

    names = excluded_names or EXCLUDED_GROUP_NAMES
    if normalized_name in names:
        return True

    return any(keyword in normalized_name for keyword in excluded_keywords)


def should_exclude_course_item(
    raw_course: dict[str, Any], *, excluded_names: set[str] | None = None
) -> bool:
    """Return True when a fetched course row belongs to an excluded group.

    与课组级过滤互补：课组树中存在扁平"选修课"叶子节点，其课组名不命中
    排除规则，但取回的课程条目 kzmc 可能是"XX模块：…选修课程清单"，
    因此需要在课程级对 kzmc 再做一次检查。
    """
    group_name = str(raw_course.get("kzmc") or "").strip()
    return should_exclude_group_name(group_name, excluded_names=excluded_names)


def analyze_group_selection(
    groups: Iterable[dict[str, Any]], excluded_names: set[str] | None = None
) -> dict[str, Any]:
    """Return a structured view of group filtering and leaf selection."""
    normalized_groups = [_normalized_group(group) for group in groups if group.get("kzid")]
    by_id = {group["kzid"]: group for group in normalized_groups}
    children_map: dict[str, list[str]] = defaultdict(list)

    for group in normalized_groups:
        parent_id = group["fkzid"]
        if parent_id and parent_id != "-1":
            children_map[parent_id].append(group["kzid"])

    excluded_ids: set[str] = set()
    stack = [
        group["kzid"]
        for group in normalized_groups
        if should_exclude_group_name(group["kzmc"], excluded_names=excluded_names)
    ]
    while stack:
        kzid = stack.pop()
        if kzid in excluded_ids:
            continue
        excluded_ids.add(kzid)
        stack.extend(children_map.get(kzid, []))

    kept_ids = {kzid for kzid in by_id if kzid not in excluded_ids}
    leaf_ids = [
        kzid
        for kzid in kept_ids
        if not any(child_id in kept_ids for child_id in children_map.get(kzid, []))
    ]

    return {
        "groups_by_id": by_id,
        "children_map": dict(children_map),
        "excluded_ids": excluded_ids,
        "kept_ids": kept_ids,
        "leaf_ids": sorted(leaf_ids),
    }


def select_leaf_group_ids(
    groups: Iterable[dict[str, Any]], excluded_names: set[str] | None = None
) -> list[str]:
    """Build a tree from the flat group list, exclude configured branches, and return kept leaves."""
    return analyze_group_selection(groups, excluded_names=excluded_names)["leaf_ids"]


def derive_postgrad_zyfx(major_code: str) -> str:
    """Use major_code as zyfx only for direction-level six-digit codes."""
    code = major_code.strip()
    return code if len(code) == 6 else ""


def merge_postgrad_courses(
    raw_courses: Iterable[dict[str, Any]], *, major_code: str, logger_prefix: str = ""
) -> list[dict[str, Any]]:
    """Normalize and merge courses by course_code, preserving source metadata."""
    merged: dict[str, dict[str, Any]] = {}
    warned_codes: set[str] = set()

    for raw_course in raw_courses:
        normalized = normalize_course(raw_course)
        course_code = str(normalized.get("course_code") or "").strip()
        if not course_code:
            continue

        plan_id = str(raw_course.get("fah") or "").strip()
        track = str(normalized.get("track") or "").strip()
        candidate = dict(normalized)
        candidate["source_plan_IDs"] = [plan_id] if plan_id else []
        candidate["source_tracks"] = [track] if track else []

        if course_code not in merged:
            merged[course_code] = candidate
            continue

        existing = merged[course_code]
        comparable_keys = set(existing.keys()) | set(candidate.keys())
        comparable_keys.discard("source_plan_IDs")
        comparable_keys.discard("source_tracks")
        comparable_keys.discard("track")

        if (
            any(existing.get(key) != candidate.get(key) for key in comparable_keys)
            and course_code not in warned_codes
        ):
            logger.warning(
                "%s课程 %s 在 major_code=%s 下存在字段冲突，保留首条记录",
                logger_prefix,
                course_code,
                major_code,
            )
            warned_codes.add(course_code)

        for source_plan_id in candidate["source_plan_IDs"]:
            if source_plan_id and source_plan_id not in existing["source_plan_IDs"]:
                existing["source_plan_IDs"].append(source_plan_id)

        for source_track in candidate["source_tracks"]:
            if source_track and source_track not in existing["source_tracks"]:
                existing["source_tracks"].append(source_track)

    return [merged[course_code] for course_code in sorted(merged)]
